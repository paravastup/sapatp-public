import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from chatbot.services.rag_retriever import ProductRetriever
from chatbot.services.response_generator_rag import RAGResponseGenerator
from chatbot.services.ollama_client import OllamaClient

# Test RAG
print("Testing RAG system...")
retriever = ProductRetriever()

if retriever.is_ready():
    print(f"RAG index loaded: {retriever.index.ntotal} products")
    
    # Test search
    query = "wine glasses"
    products = retriever.search(query, k=5, filters={'brand': 'Brand_Kappa'})
    print(f"\nSearch results for '{query}' (brand=Brand_Kappa): {len(products)} products")
    
    if products:
        for i, p in enumerate(products[:3], 1):
            print(f"  {i}. {p.sku}: {p.label or p.product_name} - ${p.web_price}")
        
        # Test response generation
        print("\nTesting response generation...")
        ollama = OllamaClient()
        rag_gen = RAGResponseGenerator(ollama)
        
        response = rag_gen.generate_with_rag(
            user_query="Show me Brand_Kappa wine glasses",
            intent='product_info',
            entities={'datafeed_brand': 'Brand_Kappa'},
            context={}
        )
        print(f"\nRAG Response:\n{response}")
    else:
        print("No products found!")
else:
    print("RAG index not ready!")
