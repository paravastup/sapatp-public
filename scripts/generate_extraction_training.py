#!/usr/bin/env python3
"""
Comprehensive Training Data Generator for LLM Exact Value Extraction
Generates 15,000 high-quality training examples to teach the model to:
1. Extract exact values from context (no hallucination)
2. Return null when values are not present
3. Handle multiple phrasings and formats
4. Work with all SAP fields
"""

import json
import random
import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExtractionTrainingGenerator:
    """Generate 15,000 training examples for exact value extraction"""

    def __init__(self, use_real_sap_data: bool = False):
        """Initialize with field definitions and sample data"""

        # All SAP fields with their variations and sample values
        self.fields = {
            'upc': {
                'sap_field': 'EAN11',
                'display_name': 'UPC',
                'variations': [
                    'UPC', 'upc', 'barcode', 'bar code', 'EAN', 'ean',
                    'scan code', 'product code', 'universal product code',
                    'UPC code', 'EAN code', 'barcode number', 'scanning code'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "What is the {field}?",
                    "Show me the {field}",
                    "I need the {field}",
                    "Can you tell me the {field}?",
                    "Give me the {field}",
                    "{field}?",
                    "What's the {field} for this product?",
                    "Please provide the {field}",
                    "Could you find the {field}?",
                    "I'm looking for the {field}",
                    "Do you have the {field}?",
                    "Find the {field}",
                    "Get the {field}",
                    "Tell me the {field}"
                ],
                'sample_values': [
                    '10026102100020', '10026102100010', '10883314193807',
                    '10026102002138', '98765432109876', '12345678901234',
                    '11111111111111', '99999999999999', '10101010101010'
                ]
            },
            'brand': {
                'sap_field': 'ZBRDES',
                'display_name': 'brand',
                'variations': [
                    'brand', 'Brand', 'manufacturer', 'make', 'company',
                    'who makes', 'brand name', 'product brand', 'maker',
                    'manufacturing company', 'produced by', 'made by'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "What brand is it?",
                    "Who makes this?",
                    "Which company manufactures this?",
                    "Tell me the {field}",
                    "What is the {field} name?",
                    "Show the {field}",
                    "I need to know the {field}",
                    "{field}?",
                    "What {field} is this product?",
                    "Can you identify the {field}?",
                    "Please provide the {field}"
                ],
                'sample_values': [
                    'BRAND_A', 'BRAND_B', 'ACME CORP', 'BRAND_C',
                    'BRAND_D', 'ARC INTERNATIONAL', 'BRAND_H',
                    'BRAND_E', 'BRAND_F', 'BRAND_G'
                ]
            },
            'stock': {
                'sap_field': 'STOCK',
                'display_name': 'stock',
                'variations': [
                    'stock', 'inventory', 'quantity', 'how many',
                    'available', 'in stock', 'stock level', 'on hand',
                    'available quantity', 'current stock', 'pieces available',
                    'units available', 'stock count'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "How many do we have?",
                    "Check {field}",
                    "What's the {field} level?",
                    "How many are available?",
                    "Show current {field}",
                    "Do we have any in {field}?",
                    "What's our {field} count?",
                    "{field}?",
                    "Get {field} quantity",
                    "Tell me the {field}",
                    "Is it in {field}?"
                ],
                'sample_values': [
                    '0', '1', '10', '100', '500', '1000', '1500', '2000',
                    '5000', '10000', '99999', '12345', '789', '4567'
                ]
            },
            'origin': {
                'sap_field': 'HERKL',
                'display_name': 'country of origin',
                'variations': [
                    'origin', 'country', 'country of origin', 'made in',
                    'from where', 'manufactured in', 'produced in',
                    'where made', 'where from', 'source country',
                    'origin country', 'manufacturing country'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Where is it made?",
                    "Where does it come from?",
                    "What country is it from?",
                    "Tell me the {field}",
                    "Which country manufactures this?",
                    "Show the {field}",
                    "{field}?",
                    "I need the {field}",
                    "What is the {field}?",
                    "Find the {field}"
                ],
                'sample_values': [
                    'USA', 'CHINA', 'FRANCE', 'GERMANY', 'ITALY',
                    'MEXICO', 'CANADA', 'JAPAN', 'SPAIN', 'UK',
                    'BRAZIL', 'INDIA', 'TURKEY', 'POLAND'
                ]
            },
            'weight': {
                'sap_field': 'BRGEW',
                'display_name': 'weight',
                'variations': [
                    'weight', 'Weight', 'how heavy', 'mass', 'kg',
                    'kilograms', 'pounds', 'lbs', 'gross weight',
                    'product weight', 'item weight', 'how much does it weigh'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "How heavy is it?",
                    "Tell me the {field}",
                    "What does it weigh?",
                    "Show the {field} in kg",
                    "I need the {field}",
                    "{field}?",
                    "Get the {field}",
                    "How many kg?",
                    "Weight in kilograms?",
                    "What is the {field}?"
                ],
                'sample_values': [
                    '0.5', '1.0', '1.5', '2.0', '2.5', '3.0', '5.0',
                    '10.0', '15.5', '20.0', '0.25', '0.75', '12.3'
                ]
            },
            'case_pack': {
                'sap_field': 'UMREZ',
                'display_name': 'case pack size',
                'variations': [
                    'case pack', 'case', 'pack size', 'units per case',
                    'case pack size', 'pack', 'case quantity', 'per case',
                    'case count', 'units in case', 'case size', 'packing'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "How many per case?",
                    "What's the {field} size?",
                    "Units per case?",
                    "Tell me the {field}",
                    "Show {field}",
                    "{field}?",
                    "I need the {field}",
                    "Get {field} information",
                    "What is the {field}?"
                ],
                'sample_values': [
                    '1', '6', '12', '24', '36', '48', '60', '72',
                    '100', '144', '200', '500', '1000'
                ]
            },
            'vendor_sku': {
                'sap_field': 'BISMT',
                'display_name': 'vendor SKU',
                'variations': [
                    'vendor SKU', 'vendor sku', 'supplier code', 'vendor code',
                    'old SKU', 'vendor number', 'supplier SKU', 'vendor part',
                    'vendor product code', 'supplier number', 'vendor item'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Show the {field}",
                    "I need the {field}",
                    "What is the {field}?",
                    "Tell me the {field}",
                    "{field}?",
                    "Get the {field}",
                    "Find the {field}",
                    "Provide the {field}"
                ],
                'sample_values': [
                    'V12345', 'ABC-123', 'VENDOR-001', 'SUP-456',
                    'OLD-789', 'VEN-ABC-123', '98765-V', 'ITEM-999'
                ]
            },
            'delivery_date': {
                'sap_field': 'EEIND',
                'display_name': 'delivery date',
                'variations': [
                    'delivery date', 'delivery', 'ETA', 'arrival', 'arriving',
                    'coming', 'next shipment', 'when coming', 'arrival date',
                    'expected date', 'delivery schedule', 'when will it arrive'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "When is it coming?",
                    "When will it arrive?",
                    "Show {field}",
                    "What's the ETA?",
                    "Next delivery?",
                    "{field}?",
                    "When is the next shipment?",
                    "Tell me the {field}",
                    "I need the {field}"
                ],
                'sample_values': [
                    '2025-11-15', '2025-11-20', '2025-12-01', '2025-12-15',
                    '2026-01-10', '2026-01-25', '2026-02-14', '2026-03-01'
                ]
            },
            'delivery_quantity': {
                'sap_field': 'MNG01',
                'display_name': 'delivery quantity',
                'variations': [
                    'delivery quantity', 'incoming quantity', 'shipment size',
                    'how many coming', 'delivery amount', 'incoming stock',
                    'shipment quantity', 'arriving quantity', 'on order'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "How many are coming?",
                    "What quantity is arriving?",
                    "Show {field}",
                    "Tell me the {field}",
                    "{field}?",
                    "How many on order?",
                    "What's the incoming amount?",
                    "Get {field}"
                ],
                'sample_values': [
                    '100', '200', '500', '1000', '1500', '2000',
                    '5000', '10000', '250', '750', '3000'
                ]
            },
            'product_number': {
                'sap_field': 'MATNR',
                'display_name': 'product number',
                'variations': [
                    'product number', 'product', 'SKU', 'item number',
                    'product code', 'item', 'article number', 'material number',
                    'product ID', 'item code', 'ARC SKU'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Show the {field}",
                    "Tell me the {field}",
                    "What is the {field}?",
                    "{field}?",
                    "Get the {field}",
                    "I need the {field}",
                    "Find the {field}"
                ],
                'sample_values': [
                    '10002', '10001', 'G3960', '00213', '12345',
                    '99999', 'A1234', 'B5678', 'C9012', 'TEST1'
                ]
            },
            'description': {
                'sap_field': 'MAKTX',
                'display_name': 'description',
                'variations': [
                    'description', 'product description', 'name', 'product name',
                    'item description', 'what is it', 'product details', 'title'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Describe the product",
                    "What is this product?",
                    "Show the {field}",
                    "Tell me the {field}",
                    "{field}?",
                    "What's it called?",
                    "Product name?"
                ],
                'sample_values': [
                    'GLASS TUMBLER 12OZ', 'COFFEE MUG SET', 'WINE GLASS 8OZ',
                    'DINNER PLATE 10"', 'SOUP BOWL', 'SERVING PLATTER',
                    'BAKING DISH 2QT', 'STORAGE CONTAINER 1L', 'PITCHER 64OZ'
                ]
            },
            'unit': {
                'sap_field': 'MEINS',
                'display_name': 'unit of measure',
                'variations': [
                    'unit', 'UOM', 'unit of measure', 'units', 'measurement unit',
                    'how sold', 'sold by', 'unit type', 'measure'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "What unit is it sold in?",
                    "Show the {field}",
                    "{field}?",
                    "How is it measured?",
                    "Tell me the {field}",
                    "Unit type?"
                ],
                'sample_values': [
                    'EA', 'PC', 'CS', 'DZ', 'BX', 'PK', 'ST', 'KG', 'LB'
                ]
            },
            'vendor': {
                'sap_field': 'LIFNR',
                'display_name': 'vendor',
                'variations': [
                    'vendor', 'supplier', 'vendor name', 'supplier name',
                    'who supplies', 'vendor code', 'from whom', 'source'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Who is the supplier?",
                    "Show the {field}",
                    "Tell me the {field}",
                    "{field}?",
                    "Who supplies this?",
                    "Get {field} info"
                ],
                'sample_values': [
                    'VENDOR001', 'SUPPLIER-A', 'ACME-SUP', 'GLOBAL-123',
                    'LOCAL-456', 'IMPORT-789', 'DIST-ABC', 'WHOLE-XYZ'
                ]
            },
            'purchase_order': {
                'sap_field': 'EBELN',
                'display_name': 'purchase order',
                'variations': [
                    'PO', 'purchase order', 'PO number', 'order number',
                    'purchase order number', 'order', 'PO#', 'order#'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Show the {field} number",
                    "Tell me the {field}",
                    "{field}?",
                    "What PO is this on?",
                    "Get the {field}",
                    "Find the {field}"
                ],
                'sample_values': [
                    'PO-2025-001', 'PO-2025-002', '4500123456', '4500789012',
                    'ORDER-999', 'PO123456', '2025110301', 'PUR-ABC-123'
                ]
            },
            'plant': {
                'sap_field': 'WERKS',
                'display_name': 'plant',
                'variations': [
                    'plant', 'location', 'warehouse', 'site', 'plant code',
                    'facility', 'distribution center', 'DC', 'where stored'
                ],
                'question_patterns': [
                    "What's the {field}?",
                    "Which location?",
                    "Show the {field}",
                    "{field}?",
                    "What warehouse?",
                    "Tell me the {field}",
                    "Where is it?"
                ],
                'sample_values': [
                    '1000', '9994', '9993', '9943', 'DURAND', 'MILLVILLE',
                    'BRAND_D', 'ARC CANADA', 'PLANT-A', 'WAREHOUSE-1'
                ]
            }
        }

        # Sample product data for realistic examples
        self.sample_products = self._generate_sample_products()

    def _generate_sample_products(self) -> List[Dict]:
        """Generate sample product data"""
        products = []

        # Create 100 sample products with realistic data
        for i in range(100):
            product = {
                'MATNR': random.choice(['10002', '10001', 'G3960', '00213', f'{40000 + i}', f'A{1000 + i}']),
                'EAN11': f"{random.randint(1000000000000, 9999999999999)}",
                'MAKTX': random.choice([
                    'GLASS TUMBLER 12OZ CLEAR', 'COFFEE MUG SET 4PC',
                    'WINE GLASS 8OZ STEMMED', 'DINNER PLATE 10" WHITE',
                    'SOUP BOWL CERAMIC', 'SERVING PLATTER OVAL',
                    'BAKING DISH 2QT GLASS', 'STORAGE CONTAINER 1L',
                    f'PRODUCT ITEM {i}'
                ]),
                'ZBRDES': random.choice(['BRAND_A', 'BRAND_B', 'BRAND_C', 'BRAND_D', 'BRAND_E', 'ANCHOR']),
                'HERKL': random.choice(['USA', 'CHINA', 'FRANCE', 'GERMANY', 'MEXICO', 'ITALY']),
                'BRGEW': f"{random.uniform(0.1, 25.0):.2f}",
                'MEINS': random.choice(['EA', 'PC', 'CS', 'DZ']),
                'UMREZ': str(random.choice([1, 6, 12, 24, 36, 48])),
                'BISMT': f"{random.choice(['V', 'SUP', 'OLD'])}-{random.randint(10000, 99999)}",
                'STOCK': str(random.randint(0, 10000)),
                'EEIND': (datetime.now() + timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
                'MNG01': str(random.randint(100, 5000)),
                'LIFNR': f"VENDOR{random.randint(1, 50):03d}",
                'EBELN': f"PO-2025-{random.randint(1, 999):03d}",
                'WERKS': random.choice(['1000', '9994', '9993', '9943'])
            }
            products.append(product)

        return products

    def generate_single_field_examples(self) -> List[Dict]:
        """Generate 5,000 examples for single field extraction"""
        examples = []

        # Generate ~333 examples per field (15 fields total)
        for field_key, field_info in self.fields.items():
            for _ in range(333):
                product = random.choice(self.sample_products)

                # Choose random variation and question pattern
                variation = random.choice(field_info['variations'])
                pattern = random.choice(field_info['question_patterns'])
                query = pattern.format(field=variation)

                # Randomly decide if field is present (70% positive, 30% negative)
                if random.random() < 0.7:
                    # Positive example - field is present
                    context = self._generate_context_with_field(product, field_key)
                    expected = {field_key: product[field_info['sap_field']]}
                else:
                    # Negative example - field is missing
                    context = self._generate_context_without_field(product, field_key)
                    expected = {field_key: None}

                examples.append({
                    'messages': [
                        {'role': 'system', 'content': 'Extract the requested information exactly as shown in the context. If the information is not present, return null.'},
                        {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                        {'role': 'assistant', 'content': json.dumps(expected)}
                    ],
                    'category': 'single_field',
                    'field': field_key,
                    'is_positive': expected[field_key] is not None
                })

        return examples[:5000]  # Ensure exactly 5000

    def generate_multi_field_examples(self) -> List[Dict]:
        """Generate 3,000 examples for multi-field extraction"""
        examples = []

        for _ in range(3000):
            product = random.choice(self.sample_products)

            # Choose 2-5 random fields
            num_fields = random.randint(2, 5)
            selected_fields = random.sample(list(self.fields.keys()), num_fields)

            # Create query asking for multiple fields
            field_names = []
            for field in selected_fields:
                variation = random.choice(self.fields[field]['variations'])
                field_names.append(variation)

            # Different ways to ask for multiple fields
            query_patterns = [
                f"What's the {', '.join(field_names[:-1])} and {field_names[-1]}?",
                f"Show me {', '.join(field_names)}",
                f"I need the {' and '.join(field_names)}",
                f"Get {', '.join(field_names)}",
                f"Tell me the {', '.join(field_names)} for this product"
            ]
            query = random.choice(query_patterns)

            # Generate context with some fields present, some missing
            context_parts = [f"Product {product['MATNR']}"]
            expected = {}

            for field in selected_fields:
                # 80% chance field is present
                if random.random() < 0.8:
                    sap_field = self.fields[field]['sap_field']
                    display_name = self.fields[field]['display_name']
                    value = product[sap_field]
                    context_parts.append(f"{display_name}: {value}")
                    expected[field] = value
                else:
                    expected[field] = None

            context = ", ".join(context_parts)

            examples.append({
                'messages': [
                    {'role': 'system', 'content': 'Extract all requested fields exactly as shown. Return null for any field not present in the context.'},
                    {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                    {'role': 'assistant', 'content': json.dumps(expected)}
                ],
                'category': 'multi_field',
                'fields': selected_fields
            })

        return examples

    def generate_negative_examples(self) -> List[Dict]:
        """Generate 2,500 examples where fields are not present"""
        examples = []

        for _ in range(2500):
            product = random.choice(self.sample_products)

            # Choose a field to ask about that won't be in context
            field_key = random.choice(list(self.fields.keys()))
            field_info = self.fields[field_key]

            # Generate query
            variation = random.choice(field_info['variations'])
            pattern = random.choice(field_info['question_patterns'])
            query = pattern.format(field=variation)

            # Generate context WITHOUT the requested field
            context_parts = [f"Product {product['MATNR']}"]

            # Add 2-4 other random fields (but not the one being asked)
            other_fields = [f for f in self.fields.keys() if f != field_key]
            for other_field in random.sample(other_fields, random.randint(2, 4)):
                sap_field = self.fields[other_field]['sap_field']
                display_name = self.fields[other_field]['display_name']
                value = product[sap_field]
                context_parts.append(f"{display_name}: {value}")

            context = ", ".join(context_parts)
            expected = {field_key: None}

            examples.append({
                'messages': [
                    {'role': 'system', 'content': 'Only extract information that is explicitly present in the context. If the requested information is not present, you must return null. Never generate or guess values.'},
                    {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                    {'role': 'assistant', 'content': json.dumps(expected)}
                ],
                'category': 'negative',
                'field': field_key,
                'explanation': 'Field not present in context - must return null'
            })

        return examples

    def generate_distractor_examples(self) -> List[Dict]:
        """Generate 2,000 examples with multiple products (distractors)"""
        examples = []

        for _ in range(2000):
            # Choose 2-3 products
            num_products = random.randint(2, 3)
            products = random.sample(self.sample_products, num_products)
            target_product = products[0]

            # Choose field to ask about
            field_key = random.choice(list(self.fields.keys()))
            field_info = self.fields[field_key]

            # Generate query for specific product
            variation = random.choice(field_info['variations'])
            query_patterns = [
                f"What's the {variation} for product {target_product['MATNR']}?",
                f"Show me the {variation} of {target_product['MATNR']}",
                f"I need the {variation} for {target_product['MATNR']}",
                f"For product {target_product['MATNR']}, what's the {variation}?"
            ]
            query = random.choice(query_patterns)

            # Generate context with multiple products
            context_parts = []
            for i, product in enumerate(products):
                product_context = [f"Product {product['MATNR']}"]

                # Add 2-4 fields for each product
                selected_fields = random.sample(list(self.fields.keys()), random.randint(2, 4))

                # For target product, 70% chance the requested field is present
                if i == 0:
                    if random.random() < 0.7 and field_key not in selected_fields:
                        selected_fields.append(field_key)

                for field in selected_fields:
                    sap_field = self.fields[field]['sap_field']
                    display_name = self.fields[field]['display_name']
                    value = product[sap_field]
                    product_context.append(f"{display_name}: {value}")

                context_parts.append(", ".join(product_context))

            context = ". ".join(context_parts)

            # Expected value only from target product
            sap_field = field_info['sap_field']
            if field_key in selected_fields and any(f"Product {target_product['MATNR']}" in part and field_info['display_name'] in part for part in context_parts):
                expected = {field_key: target_product[sap_field]}
            else:
                expected = {field_key: None}

            examples.append({
                'messages': [
                    {'role': 'system', 'content': 'Extract information only for the specific product mentioned in the question. Do not extract from other products in the context. Return null if the information is not available for the requested product.'},
                    {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                    {'role': 'assistant', 'content': json.dumps(expected)}
                ],
                'category': 'distractor',
                'target_product': target_product['MATNR'],
                'num_products': num_products
            })

        return examples

    def generate_context_variations(self) -> List[Dict]:
        """Generate 1,500 examples with different context formats"""
        examples = []

        format_generators = [
            self._generate_table_format,
            self._generate_json_format,
            self._generate_natural_language_format,
            self._generate_list_format,
            self._generate_mixed_format
        ]

        for _ in range(1500):
            product = random.choice(self.sample_products)
            field_key = random.choice(list(self.fields.keys()))
            field_info = self.fields[field_key]

            # Generate query
            variation = random.choice(field_info['variations'])
            pattern = random.choice(field_info['question_patterns'])
            query = pattern.format(field=variation)

            # Choose random format generator
            format_gen = random.choice(format_generators)
            context, has_field = format_gen(product, field_key)

            sap_field = field_info['sap_field']
            expected = {field_key: product[sap_field] if has_field else None}

            examples.append({
                'messages': [
                    {'role': 'system', 'content': 'Extract information from any format. Look for the requested field regardless of how the data is structured.'},
                    {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                    {'role': 'assistant', 'content': json.dumps(expected)}
                ],
                'category': 'context_variation',
                'format_type': format_gen.__name__
            })

        return examples

    def generate_followup_examples(self) -> List[Dict]:
        """Generate 1,000 examples with follow-up queries"""
        examples = []

        followup_patterns = [
            "How about the {field}?",
            "And the {field}?",
            "What about {field}?",
            "Also show the {field}",
            "Now the {field}",
            "{field} too?",
            "Also need {field}",
            "Get {field} as well"
        ]

        for _ in range(1000):
            product = random.choice(self.sample_products)

            # First query and response
            first_field = random.choice(list(self.fields.keys()))
            first_context = self._generate_context_with_field(product, first_field)

            # Follow-up query for different field
            second_field = random.choice([f for f in self.fields.keys() if f != first_field])
            field_info = self.fields[second_field]
            variation = random.choice(field_info['variations'])
            pattern = random.choice(followup_patterns)
            query = pattern.format(field=variation)

            # Context includes previous query info
            conversation_context = f"Previous query was about {self.fields[first_field]['display_name']} for product {product['MATNR']}."

            # 70% chance the follow-up field is present
            if random.random() < 0.7:
                context = self._generate_context_with_field(product, second_field)
                sap_field = field_info['sap_field']
                expected = {second_field: product[sap_field]}
            else:
                context = self._generate_context_without_field(product, second_field)
                expected = {second_field: None}

            full_context = f"{conversation_context} {context}"

            examples.append({
                'messages': [
                    {'role': 'system', 'content': 'Handle follow-up queries by extracting the newly requested information. Consider the conversation context.'},
                    {'role': 'user', 'content': f"Context: {full_context}\n\nQuestion: {query}"},
                    {'role': 'assistant', 'content': json.dumps(expected)}
                ],
                'category': 'followup',
                'first_field': first_field,
                'second_field': second_field
            })

        return examples

    def generate_edge_cases(self) -> List[Dict]:
        """Generate 1,000 edge case examples"""
        examples = []

        edge_case_generators = [
            self._generate_null_value_example,
            self._generate_malformed_data_example,
            self._generate_ambiguous_query_example,
            self._generate_special_characters_example,
            self._generate_multiple_values_example,
            self._generate_partial_match_example,
            self._generate_typo_example,
            self._generate_case_sensitivity_example
        ]

        for _ in range(1000):
            generator = random.choice(edge_case_generators)
            example = generator()
            examples.append(example)

        return examples

    # Helper methods for context generation
    def _generate_context_with_field(self, product: Dict, field_key: str) -> str:
        """Generate context that includes the requested field"""
        field_info = self.fields[field_key]
        sap_field = field_info['sap_field']
        display_name = field_info['display_name']
        value = product[sap_field]

        # Different context patterns
        patterns = [
            f"Product {product['MATNR']} has {display_name} {value}",
            f"Product {product['MATNR']}: {display_name} is {value}",
            f"{display_name}: {value} for product {product['MATNR']}",
            f"Product {product['MATNR']} - {display_name}: {value}",
            f"For product {product['MATNR']}, the {display_name} is {value}"
        ]

        base = random.choice(patterns)

        # Add 1-3 other random fields
        other_fields = [f for f in self.fields.keys() if f != field_key]
        for other_field in random.sample(other_fields, random.randint(1, 3)):
            other_info = self.fields[other_field]
            other_sap = other_info['sap_field']
            other_display = other_info['display_name']
            other_value = product[other_sap]
            base += f", {other_display}: {other_value}"

        return base

    def _generate_context_without_field(self, product: Dict, field_key: str) -> str:
        """Generate context that does NOT include the requested field"""
        context_parts = [f"Product {product['MATNR']}"]

        # Add 2-4 other fields (but not the requested one)
        other_fields = [f for f in self.fields.keys() if f != field_key]
        for other_field in random.sample(other_fields, random.randint(2, 4)):
            field_info = self.fields[other_field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]
            context_parts.append(f"{display_name}: {value}")

        return ", ".join(context_parts)

    # Format generators for context variations
    def _generate_table_format(self, product: Dict, field_key: str) -> Tuple[str, bool]:
        """Generate table format context"""
        has_field = random.random() < 0.7

        headers = ['Product', 'Field', 'Value']
        rows = [f"| {'|'.join(headers)} |", "|---|---|---|"]

        fields_to_include = random.sample(list(self.fields.keys()), random.randint(3, 6))
        if has_field and field_key not in fields_to_include:
            fields_to_include.append(field_key)
        elif not has_field and field_key in fields_to_include:
            fields_to_include.remove(field_key)

        for field in fields_to_include:
            field_info = self.fields[field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]
            rows.append(f"| {product['MATNR']} | {display_name} | {value} |")

        return "\n".join(rows), has_field

    def _generate_json_format(self, product: Dict, field_key: str) -> Tuple[str, bool]:
        """Generate JSON format context"""
        has_field = random.random() < 0.7

        data = {"product": product['MATNR']}

        fields_to_include = random.sample(list(self.fields.keys()), random.randint(3, 6))
        if has_field and field_key not in fields_to_include:
            fields_to_include.append(field_key)
        elif not has_field and field_key in fields_to_include:
            fields_to_include.remove(field_key)

        for field in fields_to_include:
            field_info = self.fields[field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]
            data[display_name] = value

        return json.dumps(data, indent=2), has_field

    def _generate_natural_language_format(self, product: Dict, field_key: str) -> Tuple[str, bool]:
        """Generate natural language format context"""
        has_field = random.random() < 0.7

        sentences = [
            f"We have product {product['MATNR']} in our system.",
            f"Product {product['MATNR']} is available.",
            f"Looking at product {product['MATNR']},"
        ]
        text = random.choice(sentences)

        fields_to_include = random.sample(list(self.fields.keys()), random.randint(3, 5))
        if has_field and field_key not in fields_to_include:
            fields_to_include.append(field_key)
        elif not has_field and field_key in fields_to_include:
            fields_to_include.remove(field_key)

        for field in fields_to_include:
            field_info = self.fields[field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]

            connectors = [
                f" It has a {display_name} of {value}.",
                f" The {display_name} is {value}.",
                f" Its {display_name} is {value}.",
                f" With {display_name} {value}."
            ]
            text += random.choice(connectors)

        return text, has_field

    def _generate_list_format(self, product: Dict, field_key: str) -> Tuple[str, bool]:
        """Generate list format context"""
        has_field = random.random() < 0.7

        lines = [f"Product: {product['MATNR']}"]

        fields_to_include = random.sample(list(self.fields.keys()), random.randint(3, 6))
        if has_field and field_key not in fields_to_include:
            fields_to_include.append(field_key)
        elif not has_field and field_key in fields_to_include:
            fields_to_include.remove(field_key)

        for field in fields_to_include:
            field_info = self.fields[field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]

            formats = [
                f"- {display_name}: {value}",
                f"• {display_name} = {value}",
                f"  {display_name} -> {value}"
            ]
            lines.append(random.choice(formats))

        return "\n".join(lines), has_field

    def _generate_mixed_format(self, product: Dict, field_key: str) -> Tuple[str, bool]:
        """Generate mixed format context"""
        has_field = random.random() < 0.7

        # Mix different formats
        parts = []

        # Start with product number
        starters = [
            f"Product #{product['MATNR']}:",
            f"[{product['MATNR']}]",
            f"Item {product['MATNR']} -"
        ]
        parts.append(random.choice(starters))

        fields_to_include = random.sample(list(self.fields.keys()), random.randint(3, 5))
        if has_field and field_key not in fields_to_include:
            fields_to_include.append(field_key)
        elif not has_field and field_key in fields_to_include:
            fields_to_include.remove(field_key)

        for i, field in enumerate(fields_to_include):
            field_info = self.fields[field]
            sap_field = field_info['sap_field']
            display_name = field_info['display_name']
            value = product[sap_field]

            if i % 2 == 0:
                parts.append(f"{display_name}={value}")
            else:
                parts.append(f"({display_name}: {value})")

        return " ".join(parts), has_field

    # Edge case generators
    def _generate_null_value_example(self) -> Dict:
        """Generate example with null/N/A values"""
        product = random.choice(self.sample_products)
        field_key = random.choice(list(self.fields.keys()))
        field_info = self.fields[field_key]

        variation = random.choice(field_info['variations'])
        pattern = random.choice(field_info['question_patterns'])
        query = pattern.format(field=variation)

        # Context with N/A value
        null_values = ['N/A', 'null', 'None', 'not available', '-', '', 'TBD']
        null_value = random.choice(null_values)

        context = f"Product {product['MATNR']}: {field_info['display_name']}: {null_value}"

        # Add some other fields
        other_fields = random.sample([f for f in self.fields.keys() if f != field_key], 2)
        for other_field in other_fields:
            other_info = self.fields[other_field]
            context += f", {other_info['display_name']}: {product[other_info['sap_field']]}"

        expected = {field_key: None}  # Null values should return None

        return {
            'messages': [
                {'role': 'system', 'content': 'Treat N/A, null, None, and similar values as missing data. Return null for these cases.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'null_value'
        }

    def _generate_malformed_data_example(self) -> Dict:
        """Generate example with malformed data"""
        product = random.choice(self.sample_products)
        field_key = 'upc'  # Use UPC for malformed examples
        field_info = self.fields[field_key]

        variation = random.choice(field_info['variations'])
        query = f"What's the {variation}?"

        # Malformed UPC values
        malformed_values = [
            '12345',  # Too short
            '123456789012345678',  # Too long
            '12345-67890-12',  # With dashes
            'ABC123456789',  # With letters
            '1234 5678 9012'  # With spaces
        ]
        malformed_value = random.choice(malformed_values)

        context = f"Product {product['MATNR']} has UPC: {malformed_value}"

        # Model should still extract what's there (even if malformed)
        expected = {field_key: malformed_value}

        return {
            'messages': [
                {'role': 'system', 'content': 'Extract values exactly as they appear, even if they seem malformed or incorrect.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'malformed_data'
        }

    def _generate_ambiguous_query_example(self) -> Dict:
        """Generate example with ambiguous query"""
        products = random.sample(self.sample_products, 2)
        field_key = random.choice(list(self.fields.keys()))
        field_info = self.fields[field_key]

        # Ambiguous query without specifying which product
        ambiguous_queries = [
            f"What's the {field_info['display_name']}?",
            f"Show {field_info['display_name']}",
            f"I need the {field_info['display_name']}",
            f"{field_info['display_name']}?"
        ]
        query = random.choice(ambiguous_queries)

        # Context with multiple products
        context = ""
        for product in products:
            sap_field = field_info['sap_field']
            value = product[sap_field]
            context += f"Product {product['MATNR']} has {field_info['display_name']} {value}. "

        # Should return null for ambiguous queries
        expected = {field_key: None}

        return {
            'messages': [
                {'role': 'system', 'content': 'When multiple products are present and the query is ambiguous about which product, return null.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'ambiguous_query'
        }

    def _generate_special_characters_example(self) -> Dict:
        """Generate example with special characters in values"""
        product = random.choice(self.sample_products).copy()
        field_key = 'description'
        field_info = self.fields[field_key]

        # Add special characters to description
        special_values = [
            'GLASS 12" TUMBLER (SET OF 4)',
            'MUG & SAUCER - 8OZ/250ML',
            'PLATE [LARGE] 10.5"',
            'BOWL #3 @ $5.99',
            'ITEM: GLASS; TYPE: WINE; SIZE: 8OZ',
            '100% CRYSTAL GLASS <PREMIUM>'
        ]
        product['MAKTX'] = random.choice(special_values)

        query = "What's the product description?"
        context = f"Product {product['MATNR']}: Description = {product['MAKTX']}"

        expected = {field_key: product['MAKTX']}

        return {
            'messages': [
                {'role': 'system', 'content': 'Extract values exactly as shown, including all special characters, punctuation, and formatting.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'special_characters'
        }

    def _generate_multiple_values_example(self) -> Dict:
        """Generate example with multiple possible values"""
        product = random.choice(self.sample_products)
        field_key = 'upc'

        query = "What's the UPC?"

        # Context with multiple UPC values
        context = f"Product {product['MATNR']} has primary UPC: {product['EAN11']} and alternate UPC: 98765432109876"

        # Should return the primary/first value
        expected = {field_key: product['EAN11']}

        return {
            'messages': [
                {'role': 'system', 'content': 'When multiple values are present for the same field, extract the primary or first value mentioned.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'multiple_values'
        }

    def _generate_partial_match_example(self) -> Dict:
        """Generate example with partial product number match"""
        product = random.choice(self.sample_products)
        field_key = random.choice(list(self.fields.keys()))
        field_info = self.fields[field_key]

        # Query with partial product number
        partial = product['MATNR'][:3]  # First 3 characters
        query = f"What's the {field_info['display_name']} for product starting with {partial}?"

        # Context with full product
        sap_field = field_info['sap_field']
        value = product[sap_field]
        context = f"Product {product['MATNR']} has {field_info['display_name']} {value}"

        # Should extract since partial match is clear
        expected = {field_key: value}

        return {
            'messages': [
                {'role': 'system', 'content': 'When a partial product identifier clearly matches a product in context, extract the requested information.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'partial_match'
        }

    def _generate_typo_example(self) -> Dict:
        """Generate example with typos in query"""
        product = random.choice(self.sample_products)
        field_key = 'upc'
        field_info = self.fields[field_key]

        # Common typos for UPC
        typos = ['UCP', 'ucp', 'UPS', 'UFC', 'barcod', 'barkode', 'ENA', 'scna code']
        typo = random.choice(typos)

        query = f"What's the {typo}?"

        # Context with correct field
        sap_field = field_info['sap_field']
        value = product[sap_field]
        context = f"Product {product['MATNR']} has UPC: {value}"

        # Should still extract despite typo
        expected = {field_key: value}

        return {
            'messages': [
                {'role': 'system', 'content': 'Understand common typos and variations in field names. Extract the most likely matching field.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'typo'
        }

    def _generate_case_sensitivity_example(self) -> Dict:
        """Generate example with case sensitivity variations"""
        product = random.choice(self.sample_products)
        field_key = random.choice(list(self.fields.keys()))
        field_info = self.fields[field_key]

        # Random case variations
        variations = [
            field_info['display_name'].upper(),
            field_info['display_name'].lower(),
            field_info['display_name'].title(),
            ''.join(random.choice([c.upper(), c.lower()]) for c in field_info['display_name'])
        ]
        variation = random.choice(variations)

        query = f"What's the {variation}?"

        # Context with standard case
        sap_field = field_info['sap_field']
        value = product[sap_field]
        context = f"Product {product['MATNR']}: {field_info['display_name']} = {value}"

        expected = {field_key: value}

        return {
            'messages': [
                {'role': 'system', 'content': 'Field matching should be case-insensitive. Extract values regardless of case variations.'},
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {query}"},
                {'role': 'assistant', 'content': json.dumps(expected)}
            ],
            'category': 'edge_case',
            'subcategory': 'case_sensitivity'
        }

    def generate_all_examples(self) -> List[Dict]:
        """Generate all 15,000 training examples"""
        print("Generating 15,000 comprehensive training examples...")

        all_examples = []

        # Generate each category
        print("Generating 5,000 single field examples...")
        all_examples.extend(self.generate_single_field_examples())

        print("Generating 3,000 multi-field examples...")
        all_examples.extend(self.generate_multi_field_examples())

        print("Generating 2,500 negative examples...")
        all_examples.extend(self.generate_negative_examples())

        print("Generating 2,000 distractor examples...")
        all_examples.extend(self.generate_distractor_examples())

        print("Generating 1,500 context variation examples...")
        all_examples.extend(self.generate_context_variations())

        print("Generating 1,000 follow-up examples...")
        all_examples.extend(self.generate_followup_examples())

        print("Generating 1,000 edge case examples...")
        all_examples.extend(self.generate_edge_cases())

        # Shuffle for better training
        random.shuffle(all_examples)

        print(f"Total examples generated: {len(all_examples)}")

        # Add metadata
        for i, example in enumerate(all_examples):
            example['id'] = i + 1
            example['timestamp'] = datetime.now().isoformat()

        return all_examples

    def save_to_file(self, examples: List[Dict], output_file: str):
        """Save examples to JSONL file for Ollama fine-tuning"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for example in examples:
                # Format for Ollama fine-tuning (messages format)
                training_example = {
                    'messages': example['messages']
                }
                f.write(json.dumps(training_example) + '\n')

        print(f"Saved {len(examples)} examples to {output_path}")

        # Also save metadata file
        metadata = {
            'total_examples': len(examples),
            'categories': {},
            'fields': {},
            'generation_date': datetime.now().isoformat()
        }

        # Count categories
        for example in examples:
            category = example.get('category', 'unknown')
            metadata['categories'][category] = metadata['categories'].get(category, 0) + 1

            # Count fields
            if 'field' in example:
                field = example['field']
                metadata['fields'][field] = metadata['fields'].get(field, 0) + 1

        metadata_path = output_path.with_suffix('.metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Saved metadata to {metadata_path}")

        return output_path, metadata_path

    def generate_validation_set(self, num_examples: int = 1000) -> List[Dict]:
        """Generate a separate validation set for testing"""
        print(f"Generating {num_examples} validation examples...")

        # Use different random seed for validation
        random.seed(42)

        validation_examples = []

        # Generate proportional examples from each category
        categories = [
            ('single_field', int(num_examples * 0.33)),
            ('multi_field', int(num_examples * 0.20)),
            ('negative', int(num_examples * 0.17)),
            ('distractor', int(num_examples * 0.13)),
            ('context_variation', int(num_examples * 0.10)),
            ('followup', int(num_examples * 0.07))
        ]

        for category, count in categories:
            if category == 'single_field':
                examples = self.generate_single_field_examples()
            elif category == 'multi_field':
                examples = self.generate_multi_field_examples()
            elif category == 'negative':
                examples = self.generate_negative_examples()
            elif category == 'distractor':
                examples = self.generate_distractor_examples()
            elif category == 'context_variation':
                examples = self.generate_context_variations()
            elif category == 'followup':
                examples = self.generate_followup_examples()

            validation_examples.extend(examples[:count])

        # Reset random seed
        random.seed()

        return validation_examples


def main():
    """Main function to generate training data"""
    print("=" * 80)
    print("LLM Extraction Training Data Generator")
    print("Generating 15,000 examples for exact value extraction")
    print("=" * 80)

    # Initialize generator
    generator = ExtractionTrainingGenerator(use_real_sap_data=False)

    # Generate training examples
    training_examples = generator.generate_all_examples()

    # Save training set
    training_file = '/opt/app/training_data/extraction_training_15k.jsonl'
    generator.save_to_file(training_examples, training_file)

    # Generate validation set
    validation_examples = generator.generate_validation_set(1000)
    validation_file = '/opt/app/training_data/extraction_validation_1k.jsonl'
    generator.save_to_file(validation_examples, validation_file)

    print("\n" + "=" * 80)
    print("Training data generation complete!")
    print(f"Training set: {len(training_examples)} examples")
    print(f"Validation set: {len(validation_examples)} examples")
    print("\nFiles created:")
    print(f"  - {training_file}")
    print(f"  - {validation_file}")
    print("\nNext steps:")
    print("  1. Review the generated examples")
    print("  2. Fine-tune Ollama model with this data")
    print("  3. Test extraction accuracy with validation set")
    print("=" * 80)


if __name__ == '__main__':
    main()