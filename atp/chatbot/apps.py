"""
Django app configuration for the chatbot application
"""

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    """Configuration for the chatbot Django app"""

    name = 'chatbot'
    verbose_name = 'AI Chatbot'

    def ready(self):
        """Initialize app when Django starts"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Chatbot app initialized")

        # Test Ollama connection on startup (optional)
        try:
            from .services.ollama_client import OllamaClient
            client = OllamaClient()
            if client.test_connection():
                logger.info("Ollama connection successful")
            else:
                logger.warning("Ollama connection failed - chatbot will use fallback mode")
        except Exception as e:
            logger.error(f"Error testing Ollama connection: {e}")