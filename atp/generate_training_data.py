#!/usr/bin/env python3
"""
Generate comprehensive training dataset for ATP Chatbot
Creates 500+ examples covering all intents, entities, and conversational patterns
"""

import json
import random
from typing import List, Dict

class TrainingDataGenerator:
    """Generate training examples for intent classification and entity extraction"""

    def __init__(self):
        self.intents = [
            'greeting', 'help', 'stock_query', 'delivery_query',
            'product_info', 'plant_selection', 'export', 'farewell', 'unknown'
        ]

        # Sample product numbers for realistic examples
        self.products = [
            '10001', '10002', '12345', '67890', '11111', '22222', '33333',
            '44444', '55555', '77777', '88888', '99999', '10001', '20002',
            '30003', '40004', '50005', '60006', '70007', '80008', '90009'
        ]

        # Sample vendor SKUs
        self.vendor_skus = [
            'ABC123', 'XYZ789', 'DEF456', 'GHI012', 'JKL345',
            'MNO678', 'PQR901', 'STU234', 'VWX567', 'YZA890'
        ]

        # Plant codes
        self.plants = ['1001', '1000', '2000', '3000', '4000']

        # Field types for product_info intent
        self.fields = [
            'upc', 'brand', 'origin', 'weight', 'case_pack',
            'vendor_sku', 'delivery', 'stock', 'all_info'
        ]

        # Export formats
        self.export_formats = ['excel', 'csv', 'pdf']

    def generate_all_examples(self) -> List[Dict]:
        """Generate complete training dataset"""
        examples = []

        # 1. Greeting intent (50 examples)
        examples.extend(self.generate_greeting_examples(50))

        # 2. Help intent (30 examples)
        examples.extend(self.generate_help_examples(30))

        # 3. Stock query intent (100 examples)
        examples.extend(self.generate_stock_examples(100))

        # 4. Delivery query intent (100 examples)
        examples.extend(self.generate_delivery_examples(100))

        # 5. Product info intent (100 examples)
        examples.extend(self.generate_product_info_examples(100))

        # 6. Plant selection intent (30 examples)
        examples.extend(self.generate_plant_selection_examples(30))

        # 7. Export intent (30 examples)
        examples.extend(self.generate_export_examples(30))

        # 8. Farewell intent (30 examples)
        examples.extend(self.generate_farewell_examples(30))

        # 9. Follow-up questions (50 examples)
        examples.extend(self.generate_followup_examples(50))

        # 10. Action repeat patterns (50 examples)
        examples.extend(self.generate_action_repeat_examples(50))

        # 11. Multi-product queries (50 examples)
        examples.extend(self.generate_multi_product_examples(50))

        # 12. Edge cases and unknown (30 examples)
        examples.extend(self.generate_edge_cases(30))

        return examples

    def generate_greeting_examples(self, count: int) -> List[Dict]:
        """Generate greeting intent examples"""
        templates = [
            "Hello",
            "Hi",
            "Hey",
            "Good morning",
            "Good afternoon",
            "Good evening",
            "Hi there",
            "Hello there",
            "Hey there",
            "Greetings",
            "What's up",
            "Howdy",
            "Hi, how are you?",
            "Hello, I need help",
            "Hey, can you help me?",
            "Good morning! I need to check something",
            "Hi! Quick question",
            "Hello bot",
            "Hey chatbot",
            "Morning!",
        ]

        examples = []
        for i in range(count):
            query = random.choice(templates)
            examples.append({
                'query': query,
                'intent': 'greeting',
                'confidence': 0.95,
                'entities': {}
            })

        return examples

    def generate_help_examples(self, count: int) -> List[Dict]:
        """Generate help intent examples"""
        templates = [
            "What can you do?",
            "Help",
            "I need help",
            "How do I use this?",
            "What features do you have?",
            "Can you help me?",
            "Show me what you can do",
            "What are your capabilities?",
            "How does this work?",
            "I don't understand",
            "What commands do you support?",
            "How do I check stock?",
            "How do I search for products?",
            "What can I ask you?",
            "Guide me",
            "Instructions please",
            "Help me get started",
            "I'm lost",
            "What should I do?",
            "Explain how this works",
        ]

        examples = []
        for template in templates[:count]:
            examples.append({
                'query': template,
                'intent': 'help',
                'confidence': 0.90,
                'entities': {}
            })

        return examples

    def generate_stock_examples(self, count: int) -> List[Dict]:
        """Generate stock query intent examples with entities"""
        templates = [
            "What's the stock of product {product}?",
            "Check stock for {product}",
            "How many {product} do we have?",
            "Show me inventory for {product}",
            "Do we have {product} in stock?",
            "Is {product} available?",
            "Stock level for {product}",
            "Check availability of {product}",
            "How much {product} is available?",
            "Quantity for {product}",
            "Check if we have {product}",
            "Stock status of {product}",
            "Show stock for {product}",
            "Is there stock for {product}?",
            "Product {product} stock",
            "How many units of {product}?",
            "Check inventory {product}",
            "Do we have any {product}?",
            "Stock check {product}",
            "Availability of {product}",
            "Check stock for products {product1}, {product2}",
            "What's the stock for {product1} and {product2}?",
            "Show me inventory for {product1}, {product2}, {product3}",
            "Check stock: {product1}, {product2}",
            "How many {product1} and {product2} do we have?",
        ]

        examples = []
        for i in range(count):
            template = random.choice(templates)

            if '{product1}' in template:
                # Multi-product example
                prods = random.sample(self.products, 3)
                query = template.format(product1=prods[0], product2=prods[1], product3=prods[2])
                entities = {
                    'product_numbers': prods[:2] if '{product3}' not in template else prods
                }
            else:
                # Single product example
                product = random.choice(self.products)
                query = template.format(product=product)
                entities = {
                    'product_numbers': [product]
                }

            # Sometimes add plant code
            if random.random() > 0.7:
                plant = random.choice(self.plants)
                query += f" at plant {plant}"
                entities['plant_code'] = plant

            examples.append({
                'query': query,
                'intent': 'stock_query',
                'confidence': 0.92,
                'entities': entities
            })

        return examples

    def generate_delivery_examples(self, count: int) -> List[Dict]:
        """Generate delivery query intent examples"""
        templates = [
            "When is {product} arriving?",
            "Delivery date for {product}",
            "When will {product} be delivered?",
            "Next shipment of {product}",
            "ETA for {product}",
            "When is the next delivery of {product}?",
            "Show delivery schedule for {product}",
            "When can I expect {product}?",
            "Arrival date for {product}",
            "When does {product} come in?",
            "Delivery status of {product}",
            "When will we get {product}?",
            "Show me delivery for {product}",
            "Next arrival of {product}",
            "Shipment ETA for {product}",
            "When is {product} coming?",
            "Delivery timeline for {product}",
            "Expected arrival of {product}",
            "When will {product} be in stock?",
            "Show delivery dates for {product}",
            "When is {product1} and {product2} arriving?",
            "Delivery schedule for {product1}, {product2}",
        ]

        examples = []
        for i in range(count):
            template = random.choice(templates)

            if '{product1}' in template:
                prods = random.sample(self.products, 2)
                query = template.format(product1=prods[0], product2=prods[1])
                entities = {'product_numbers': prods}
            else:
                product = random.choice(self.products)
                query = template.format(product=product)
                entities = {'product_numbers': [product]}

            if random.random() > 0.8:
                plant = random.choice(self.plants)
                query += f" for plant {plant}"
                entities['plant_code'] = plant

            examples.append({
                'query': query,
                'intent': 'delivery_query',
                'confidence': 0.90,
                'entities': entities
            })

        return examples

    def generate_product_info_examples(self, count: int) -> List[Dict]:
        """Generate product info intent examples with field detection"""
        field_templates = {
            'upc': [
                "What's the UPC of {product}?",
                "Show UPC for {product}",
                "UPC code for {product}",
                "What's the barcode of {product}?",
                "EAN for {product}",
                "Product code for {product}",
            ],
            'brand': [
                "What's the brand of {product}?",
                "Show brand for {product}",
                "Who manufactures {product}?",
                "Brand name for {product}",
                "Manufacturer of {product}",
                "What brand is {product}?",
            ],
            'origin': [
                "Where is {product} from?",
                "Origin of {product}",
                "Country of origin for {product}",
                "Where is {product} made?",
                "What country is {product} from?",
                "Show origin for {product}",
            ],
            'weight': [
                "How heavy is {product}?",
                "Weight of {product}",
                "What's the weight of {product}?",
                "Show weight for {product}",
                "How much does {product} weigh?",
            ],
            'case_pack': [
                "What's the case pack for {product}?",
                "Units per case for {product}",
                "Case pack of {product}",
                "How many units in a case of {product}?",
            ],
            'vendor_sku': [
                "What's the vendor SKU for {product}?",
                "Vendor code for {product}",
                "Supplier SKU for {product}",
                "Show vendor SKU {product}",
            ],
            'all_info': [
                "Tell me about {product}",
                "Show all info for {product}",
                "Product details for {product}",
                "Everything about {product}",
                "Full information on {product}",
                "Product {product} details",
                "Show me {product}",
            ]
        }

        examples = []
        per_field = count // len(field_templates)

        for field, templates in field_templates.items():
            for i in range(per_field):
                template = random.choice(templates)
                product = random.choice(self.products)
                query = template.format(product=product)

                entities = {
                    'product_numbers': [product],
                    'field_requested': field
                }

                examples.append({
                    'query': query,
                    'intent': 'product_info',
                    'confidence': 0.93,
                    'entities': entities
                })

        return examples

    def generate_plant_selection_examples(self, count: int) -> List[Dict]:
        """Generate plant selection intent examples"""
        templates = [
            "Switch to plant {plant}",
            "Change to plant {plant}",
            "Use plant {plant}",
            "Set plant to {plant}",
            "I want to check plant {plant}",
            "Show me plant {plant}",
            "Select plant {plant}",
            "Plant {plant} please",
            "Change my plant to {plant}",
            "Switch plant to {plant}",
        ]

        examples = []
        for i in range(count):
            template = random.choice(templates)
            plant = random.choice(self.plants)
            query = template.format(plant=plant)

            examples.append({
                'query': query,
                'intent': 'plant_selection',
                'confidence': 0.88,
                'entities': {'plant_code': plant}
            })

        return examples

    def generate_export_examples(self, count: int) -> List[Dict]:
        """Generate export intent examples"""
        templates = [
            "Export to {format}",
            "Download as {format}",
            "Export results to {format}",
            "Save as {format}",
            "Download in {format} format",
            "Export this to {format}",
            "Can I get this as {format}?",
            "Export data to {format}",
            "Download results as {format}",
            "Give me {format} export",
        ]

        examples = []
        for i in range(count):
            template = random.choice(templates)
            fmt = random.choice(self.export_formats)
            query = template.format(format=fmt)

            examples.append({
                'query': query,
                'intent': 'export',
                'confidence': 0.85,
                'entities': {'export_format': fmt}
            })

        return examples

    def generate_farewell_examples(self, count: int) -> List[Dict]:
        """Generate farewell intent examples"""
        templates = [
            "Goodbye",
            "Bye",
            "See you",
            "Thanks, bye",
            "Thank you, goodbye",
            "That's all, thanks",
            "I'm done",
            "Exit",
            "Quit",
            "See you later",
            "Talk to you later",
            "Thanks for your help",
            "Bye bye",
            "Farewell",
            "Later",
            "Catch you later",
            "I'm good, thanks",
            "That's all I needed",
            "Nothing else, thanks",
            "All set, bye",
        ]

        examples = []
        for template in templates[:count]:
            examples.append({
                'query': template,
                'intent': 'farewell',
                'confidence': 0.92,
                'entities': {}
            })

        return examples

    def generate_followup_examples(self, count: int) -> List[Dict]:
        """Generate follow-up question examples (context-dependent)"""
        followup_templates = [
            # Pronoun-based follow-ups
            ("What's the stock of 10001?", "What's its UPC?", 'product_info', {'product_numbers': ['10001'], 'field_requested': 'upc', 'from_context': True}),
            ("Check stock for 12345", "What's the delivery date?", 'delivery_query', {'product_numbers': ['12345'], 'from_context': True}),
            ("Show me product 67890", "What's the brand?", 'product_info', {'product_numbers': ['67890'], 'field_requested': 'brand', 'from_context': True}),
            ("Check 11111", "What about the origin?", 'product_info', {'product_numbers': ['11111'], 'field_requested': 'origin', 'from_context': True}),
            ("Product 22222", "How heavy is it?", 'product_info', {'product_numbers': ['22222'], 'field_requested': 'weight', 'from_context': True}),

            # Question without product number
            ("Stock for 33333", "What's the UPC code?", 'product_info', {'product_numbers': ['33333'], 'field_requested': 'upc', 'from_context': True}),
            ("Check 44444", "When's the delivery?", 'delivery_query', {'product_numbers': ['44444'], 'from_context': True}),
            ("Show 55555", "What brand?", 'product_info', {'product_numbers': ['55555'], 'field_requested': 'brand', 'from_context': True}),

            # "The product" references
            ("Stock of 77777", "What's the product's UPC?", 'product_info', {'product_numbers': ['77777'], 'field_requested': 'upc', 'from_context': True}),
            ("Check 88888", "Show me the product details", 'product_info', {'product_numbers': ['88888'], 'from_context': True}),
        ]

        examples = []
        for first_query, followup_query, intent, entities in followup_templates:
            examples.append({
                'query': followup_query,
                'intent': intent,
                'confidence': 0.88,
                'entities': entities,
                'requires_context': True,
                'previous_query': first_query
            })

        # Generate more variations
        while len(examples) < count:
            product = random.choice(self.products)
            field = random.choice(['upc', 'brand', 'origin', 'delivery'])

            followup_phrases = [
                f"What's the {field}?",
                f"Show me the {field}",
                f"What about {field}?",
                f"And the {field}?",
            ]

            examples.append({
                'query': random.choice(followup_phrases),
                'intent': 'delivery_query' if field == 'delivery' else 'product_info',
                'confidence': 0.85,
                'entities': {
                    'product_numbers': [product],
                    'field_requested': field if field != 'delivery' else None,
                    'from_context': True
                },
                'requires_context': True
            })

        return examples[:count]

    def generate_action_repeat_examples(self, count: int) -> List[Dict]:
        """Generate action repeat pattern examples"""
        repeat_phrases = [
            'do the same',
            'same thing',
            'same for',
            'same with',
            'also check',
            'also show',
            'also get',
            'how about',
            'what about',
            'check that for',
            'show that for',
            'repeat for',
            'again for',
        ]

        action_contexts = [
            ("What's the UPC of 10001?", 'product_info', 'upc'),
            ("Show me the brand for 12345", 'product_info', 'brand'),
            ("What's the stock of 67890?", 'stock_query', None),
            ("When is 11111 arriving?", 'delivery_query', None),
            ("Origin of 22222", 'product_info', 'origin'),
        ]

        examples = []
        for i in range(count):
            phrase = random.choice(repeat_phrases)
            new_product = random.choice(self.products)
            previous_query, intent, field = random.choice(action_contexts)

            query = f"{phrase} {new_product}"

            entities = {
                'product_numbers': [new_product],
                'action_repeat': True
            }

            if field:
                entities['field_requested'] = field

            examples.append({
                'query': query,
                'intent': intent,
                'confidence': 0.95,
                'entities': entities,
                'previous_action': previous_query
            })

        return examples

    def generate_multi_product_examples(self, count: int) -> List[Dict]:
        """Generate multi-product query examples"""
        templates = [
            "Check stock for {p1}, {p2}, {p3}",
            "What's the stock of {p1} and {p2}?",
            "Show me {p1}, {p2}, and {p3}",
            "Products {p1}, {p2}",
            "Check {p1} {p2} {p3}",
            "Stock for {p1},{p2},{p3}",
            "Show delivery for {p1} and {p2}",
            "When are {p1} and {p2} arriving?",
        ]

        examples = []
        for i in range(count):
            template = random.choice(templates)
            prods = random.sample(self.products, 3)
            query = template.format(p1=prods[0], p2=prods[1], p3=prods[2])

            # Detect intent from template
            if 'delivery' in template.lower() or 'arriving' in template.lower():
                intent = 'delivery_query'
            elif 'stock' in template.lower():
                intent = 'stock_query'
            else:
                intent = 'product_info'

            examples.append({
                'query': query,
                'intent': intent,
                'confidence': 0.88,
                'entities': {
                    'product_numbers': prods[:2] if 'and' in template else prods
                }
            })

        return examples

    def generate_edge_cases(self, count: int) -> List[Dict]:
        """Generate edge cases and unknown intents"""
        templates = [
            "asdfgh",
            "Random gibberish",
            "12345",
            "???",
            "What's the weather?",
            "Tell me a joke",
            "How are you?",
            "I like pizza",
            "The quick brown fox",
            "42",
            "What time is it?",
            "Where am I?",
            "Who are you?",
            "blah blah blah",
            "test test",
            "Lorem ipsum",
            "undefined",
            "null",
            "error",
            "crash the system",
        ]

        examples = []
        for template in templates[:count]:
            examples.append({
                'query': template,
                'intent': 'unknown',
                'confidence': 0.60,
                'entities': {}
            })

        return examples

    def save_dataset(self, filename: str):
        """Generate and save complete training dataset"""
        print("Generating training dataset...")
        examples = self.generate_all_examples()

        print(f"Generated {len(examples)} training examples")
        print("\nBreakdown by intent:")

        intent_counts = {}
        for ex in examples:
            intent = ex['intent']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        for intent, count in sorted(intent_counts.items()):
            print(f"  {intent:20s}: {count:3d} examples")

        # Save as JSON
        with open(filename, 'w') as f:
            json.dump(examples, f, indent=2)

        print(f"\n✅ Dataset saved to: {filename}")

        # Also save in Modelfile format
        modelfile_path = filename.replace('.json', '_modelfile_examples.txt')
        self.save_as_modelfile_format(examples, modelfile_path)

        return examples

    def save_as_modelfile_format(self, examples: List[Dict], filename: str):
        """Convert examples to Modelfile system prompt format"""

        system_prompt = """You are an intelligent SAP product availability assistant. Your job is to:
1. Classify user intent accurately
2. Extract product numbers, plant codes, and other entities
3. Understand follow-up questions and action repeats

Here are examples of correct classifications:

"""

        # Add representative examples (not all 500+, that's too long)
        # Group by intent and take top examples
        by_intent = {}
        for ex in examples:
            intent = ex['intent']
            if intent not in by_intent:
                by_intent[intent] = []
            by_intent[intent].append(ex)

        # Take 10 examples per intent
        for intent, intent_examples in by_intent.items():
            system_prompt += f"\n## {intent.upper()} Examples:\n\n"
            for ex in intent_examples[:10]:
                system_prompt += f"User: {ex['query']}\n"
                system_prompt += f"Intent: {ex['intent']}\n"
                if ex['entities']:
                    system_prompt += f"Entities: {json.dumps(ex['entities'])}\n"
                system_prompt += "\n"

        system_prompt += """
Now classify new user queries following these exact patterns.
Always respond with valid JSON containing intent, confidence, and entities.
"""

        with open(filename, 'w') as f:
            f.write(system_prompt)

        print(f"✅ Modelfile examples saved to: {filename}")


if __name__ == '__main__':
    generator = TrainingDataGenerator()
    dataset = generator.save_dataset('atp_training_dataset.json')
    print("\n🎉 Training dataset generation complete!")
    print("\nNext steps:")
    print("1. Review atp_training_dataset.json")
    print("2. Create Ollama Modelfile with these examples")
    print("3. Build custom model: ollama create atp-chatbot -f Modelfile")
