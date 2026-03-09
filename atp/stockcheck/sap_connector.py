"""
Enhanced SAP connector with timeout and error handling
"""
import logging
import threading
import queue
import time
from typing import Dict, Any, Optional
from pyrfc import Connection
from django.conf import settings

logger = logging.getLogger(__name__)

class SAPConnectionTimeout(Exception):
    """Raised when SAP connection times out"""
    pass

class SAPConnectionError(Exception):
    """Raised when SAP connection fails"""
    pass

class SAPConnectorWithTimeout:
    """
    SAP connector with timeout and graceful error handling
    """

    def __init__(self, connection_params: Dict[str, Any], timeout: int = 30):
        """
        Initialize SAP connector

        Args:
            connection_params: SAP connection parameters
            timeout: Timeout in seconds (default 30)
        """
        self.connection_params = connection_params
        self.timeout = timeout
        self.result_queue = queue.Queue()
        self.error_queue = queue.Queue()

    def _call_with_timeout(self, function_name: str, **kwargs) -> Dict:
        """
        Call SAP function with timeout

        Args:
            function_name: SAP function module name
            **kwargs: Function parameters

        Returns:
            SAP response dictionary

        Raises:
            SAPConnectionTimeout: If call exceeds timeout
            SAPConnectionError: If SAP connection fails
        """

        def sap_call():
            """Execute SAP call in separate thread"""
            try:
                logger.info(f"Attempting SAP connection to {self.connection_params.get('ashost', 'unknown')}")
                with Connection(**self.connection_params) as conn:
                    logger.info(f"Calling SAP function: {function_name} with params: {kwargs}")
                    result = conn.call(function_name, **kwargs)
                    self.result_queue.put(result)
            except Exception as e:
                logger.error(f"SAP connection error: {str(e)}")
                self.error_queue.put(e)

        # Start SAP call in separate thread
        thread = threading.Thread(target=sap_call)
        thread.daemon = True
        thread.start()

        # Wait for result with timeout
        thread.join(timeout=self.timeout)

        # Check if thread is still alive (timeout occurred)
        if thread.is_alive():
            logger.error(f"SAP call timed out after {self.timeout} seconds")
            raise SAPConnectionTimeout(f"SAP call '{function_name}' timed out after {self.timeout} seconds. SAP system may be unavailable.")

        # Check for errors
        if not self.error_queue.empty():
            error = self.error_queue.get()
            logger.error(f"SAP call failed: {str(error)}")
            raise SAPConnectionError(f"SAP connection failed: {str(error)}")

        # Get result
        if not self.result_queue.empty():
            return self.result_queue.get()
        else:
            raise SAPConnectionError("No response received from SAP")

    def get_material_details(self, plant: str, product: str, mode: str) -> Dict:
        """
        Get material details from SAP with timeout protection

        Args:
            plant: Plant code
            product: Product number
            mode: Query mode

        Returns:
            Material details dictionary
        """
        try:
            result = self._call_with_timeout(
                'Z_GET_MATERIAL_DETAILS',
                IV_WERKS=str(plant),
                IV_MATNR=product,
                IV_MODE=mode
            )
            return result.get('ES_OUTPUT', {})
        except (SAPConnectionTimeout, SAPConnectionError) as e:
            # Return error response that can be handled gracefully
            logger.error(f"Failed to get material details: {str(e)}")
            return {
                'error': str(e),
                'MATNR': product,
                'WERKS': plant,
                'STOCK': 'N/A',
                'MAKTX': 'SAP Connection Failed'
            }

    def get_material_all(self, plant: str, product: str) -> Dict:
        """
        Get all material data from SAP with timeout protection

        Args:
            plant: Plant code
            product: Product number

        Returns:
            Material data dictionary
        """
        try:
            result = self._call_with_timeout(
                'BAPI_MATERIAL_GET_ALL',
                PLANT=str(plant),
                MATERIAL=product
            )

            # Process result
            if 'PLANTDATA' in result:
                result['PLANTDATA']['MATNR'] = product
                if 'CLIENTDATA' in result:
                    result['PLANTDATA']['OLD_MAT_NO'] = result['CLIENTDATA'].get('OLD_MAT_NO', '')
                if 'FORECASTPARAMETERS' in result:
                    result['PLANTDATA']['FORE_MODEL'] = result['FORECASTPARAMETERS'].get('FORE_MODEL', '')
                return result['PLANTDATA']

            return {}

        except (SAPConnectionTimeout, SAPConnectionError) as e:
            logger.error(f"Failed to get material data: {str(e)}")
            return {
                'error': str(e),
                'MATNR': product,
                'PLANT': plant,
                'MAKTX': 'SAP Connection Failed'
            }

    def check_connection_health(self) -> bool:
        """
        Check if SAP connection is healthy

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Try a simple RFC_PING call with short timeout
            original_timeout = self.timeout
            self.timeout = 5  # Short timeout for health check

            result = self._call_with_timeout('RFC_PING')
            self.timeout = original_timeout

            logger.info("SAP connection health check: OK")
            return True

        except (SAPConnectionTimeout, SAPConnectionError) as e:
            logger.warning(f"SAP connection health check failed: {str(e)}")
            self.timeout = original_timeout if 'original_timeout' in locals() else self.timeout
            return False

# Singleton instance
_sap_connector = None

def get_sap_connector(timeout: int = 30) -> SAPConnectorWithTimeout:
    """
    Get singleton SAP connector instance

    Args:
        timeout: Connection timeout in seconds

    Returns:
        SAPConnectorWithTimeout instance
    """
    global _sap_connector

    if _sap_connector is None:
        from stockcheck.connection import get_sap_connection_params
        params = get_sap_connection_params()
        _sap_connector = SAPConnectorWithTimeout(params, timeout)

    return _sap_connector