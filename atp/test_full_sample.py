import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from products.services import ProductService
from chatbot.services.response_generator import ResponseGenerator
from chatbot.services.ollama_client import OllamaClient

print("=== Full Sample Request Test ===\n")

# Get product enrichment for product 10002
product = ProductService.get_product_enrichment('10002')

if product:
    print(f"Product: {product.get('name')}")
    print(f"SKU: {product.get('sku')}")
    print(f"Family: {product.get('family')}")
    print(f"Category: {product.get('catalog_category')}")
    print(f"Subcategories: {product.get('website_subcategories')}")
    print(f"Label: {product.get('label')}")
    
    # Test URL building with actual product data
    url = ProductService.build_product_url(
        family=product.get('family'),
        category=product.get('catalog_category'),
        subcategories=product.get('website_subcategories'),
        label=product.get('label')
    )
    print(f"\nGenerated URL: {url}")
    
    # Test response generation
    print("\n=== Testing Response Generator ===")
    ollama = OllamaClient()
    generator = ResponseGenerator(ollama)
    
    results = [product]  # Simulate query results
    
    response = generator.generate(
        user_query="Can I sample product 10002?",
        intent='product_info',
        results=results,
        context={},
        field_requested='sample'
    )
    
    print(f"\nGenerated Response:\n{response}")
else:
    print("Product 10002 not found!")
