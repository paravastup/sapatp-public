#!/usr/bin/env python3
"""Generate specialized training data for terminology mapping (EAN, product code, etc.)"""

import json
import random
from pathlib import Path
from typing import List, Dict

class TerminologyTrainingGenerator:
    def __init__(self):
        # All these terms should map to 'upc' field
        self.upc_synonyms = [
            "product code",
            "EAN",
            "EAN code",
            "ean",
            "scanning code",
            "scan code",
            "bar code",
            "barcode",
            "universal product code",
            "UPC code",
            "barcode number",
            "product identifier",
            "GTIN",
            "item code"
        ]

        # Sample products with UPCs
        self.sample_products = [
            {"number": "46961", "upc": "10026102469610", "brand": "LUMINARC"},
            {"number": "46888", "upc": "3429270008762", "brand": "PYREX"},
            {"number": "00213", "upc": "9533658678271", "brand": "LIBBEY"},
            {"number": "G3960", "upc": "8985801984483", "brand": "DUROBOR"},
            {"number": "A1040", "upc": "5772251489388", "brand": "CARDINAL"},
            {"number": "40068", "upc": "7885064749434", "brand": "ANCHOR"},
            {"number": "A1019", "upc": "3685270303056", "brand": "DUROBOR"},
            {"number": "40093", "upc": "5342466376353", "brand": "LUMINARC"}
        ]

    def generate_synonym_examples(self, num_examples: int = 2000) -> List[Dict]:
        """Generate examples teaching that various terms map to UPC"""
        examples = []

        for _ in range(num_examples):
            product = random.choice(self.sample_products)
            synonym = random.choice(self.upc_synonyms)

            # 70% positive (UPC present), 30% negative (UPC absent)
            if random.random() < 0.7:
                # Positive case - UPC is present
                context_templates = [
                    f"Product {product['number']} has UPC {product['upc']}, brand {product['brand']}",
                    f"For product {product['number']}, the UPC is {product['upc']}",
                    f"UPC: {product['upc']} for product {product['number']}",
                    f"Product {product['number']}: UPC is {product['upc']}, brand: {product['brand']}",
                    f"Product {product['number']} - UPC: {product['upc']}"
                ]

                context = random.choice(context_templates)

                # Various ways to ask for the UPC using synonyms
                question_templates = [
                    f"What's the {synonym}?",
                    f"Get the {synonym}",
                    f"I need the {synonym}",
                    f"Show me the {synonym}",
                    f"Tell me the {synonym}",
                    f"Find the {synonym}",
                    f"Can you tell me the {synonym}?",
                    f"Please provide the {synonym}",
                    f"What is the {synonym}?",
                    f"Do you have the {synonym}?",
                    f"Could you find the {synonym}?",
                    f"{synonym}?"
                ]

                question = random.choice(question_templates)

                # IMPORTANT: Always return as 'upc' field, regardless of synonym used
                expected_response = json.dumps({"upc": product['upc']})

            else:
                # Negative case - UPC is not present
                context_templates = [
                    f"Product {product['number']}, brand: {product['brand']}, stock: {random.randint(100, 9999)}",
                    f"Product {product['number']}, weight: {random.uniform(1, 25):.2f}, brand: {product['brand']}",
                    f"Product {product['number']}, description: PRODUCT ITEM, plant: 9994"
                ]

                context = random.choice(context_templates)
                question = f"What's the {synonym}?"

                # Still return as 'upc' field with null value
                expected_response = json.dumps({"upc": None})

            # Build the training example
            example = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {question}"
                    },
                    {
                        "role": "assistant",
                        "content": expected_response
                    }
                ]
            }

            examples.append(example)

        return examples

    def generate_disambiguation_examples(self, num_examples: int = 1000) -> List[Dict]:
        """Generate examples to disambiguate 'product code' from product number"""
        examples = []

        for _ in range(num_examples):
            product = random.choice(self.sample_products)

            # Create context with both product number and UPC
            context_templates = [
                f"Product number: {product['number']}, UPC: {product['upc']}, brand: {product['brand']}",
                f"Item {product['number']} has barcode {product['upc']}",
                f"SKU: {product['number']}, EAN: {product['upc']}, manufacturer: {product['brand']}",
                f"Product ID {product['number']} with UPC code {product['upc']}"
            ]

            context = random.choice(context_templates)

            # Ask for "product code" - should return UPC, not product number
            questions = [
                "What's the product code?",
                "Get the product code",
                "I need the product code",
                "Tell me the product code for this item",
                "Please provide the product code"
            ]

            question = random.choice(questions)

            # Should return UPC when asked for "product code"
            expected_response = json.dumps({"upc": product['upc']})

            example = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {question}"
                    },
                    {
                        "role": "assistant",
                        "content": expected_response
                    }
                ]
            }

            examples.append(example)

        return examples

    def generate_ean_specific_examples(self, num_examples: int = 1000) -> List[Dict]:
        """Generate examples specifically for EAN terminology"""
        examples = []

        ean_terms = ["EAN", "ean", "EAN code", "ean code", "EAN number", "European Article Number"]

        for _ in range(num_examples):
            product = random.choice(self.sample_products)
            ean_term = random.choice(ean_terms)

            if random.random() < 0.8:
                # Positive case
                context = f"Product {product['number']} has UPC {product['upc']}"
                question = f"What's the {ean_term}?"
                # Map EAN to UPC field
                expected_response = json.dumps({"upc": product['upc']})
            else:
                # Negative case
                context = f"Product {product['number']}, brand: {product['brand']}"
                question = f"Get the {ean_term}"
                expected_response = json.dumps({"upc": None})

            example = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {question}"
                    },
                    {
                        "role": "assistant",
                        "content": expected_response
                    }
                ]
            }

            examples.append(example)

        return examples

    def generate_all_examples(self) -> List[Dict]:
        """Generate all terminology training examples"""
        print("Generating terminology training examples...")

        examples = []

        # Generate different types of examples
        print("- Generating 2000 synonym mapping examples...")
        examples.extend(self.generate_synonym_examples(2000))

        print("- Generating 1000 disambiguation examples...")
        examples.extend(self.generate_disambiguation_examples(1000))

        print("- Generating 1000 EAN-specific examples...")
        examples.extend(self.generate_ean_specific_examples(1000))

        # Shuffle all examples
        random.shuffle(examples)

        print(f"Total examples generated: {len(examples)}")

        return examples

    def save_training_data(self, examples: List[Dict], filename: str):
        """Save training examples to JSONL file"""
        output_path = Path(f'/mnt/d/productavailability/training_data/{filename}')
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')

        print(f"Saved {len(examples)} examples to {output_path}")
        return output_path

def main():
    generator = TerminologyTrainingGenerator()

    # Generate all examples
    examples = generator.generate_all_examples()

    # Save to file
    output_file = generator.save_training_data(examples, 'terminology_training_4k.jsonl')

    print("\nExample entries:")
    for i, example in enumerate(examples[:3]):
        messages = example['messages']
        user_msg = messages[0]['content']
        assistant_msg = messages[1]['content']
        print(f"\nExample {i+1}:")
        print(f"User: {user_msg[:150]}...")
        print(f"Assistant: {assistant_msg}")

    print(f"\nTraining data ready for fine-tuning: {output_file}")
    print("This data specifically teaches:")
    print("1. 'product code' → UPC (not product number)")
    print("2. 'EAN'/'ean' → UPC field")
    print("3. All barcode synonyms → UPC field")

if __name__ == '__main__':
    main()