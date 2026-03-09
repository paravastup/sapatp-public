"""
Enhanced Response Generator with RAG
Integrates vector search for accurate, context-aware responses
"""
from chatbot.services.response_generator import ResponseGenerator
from chatbot.services.rag_retriever import ProductRetriever
import logging

logger = logging.getLogger(__name__)


class RAGResponseGenerator(ResponseGenerator):
    """Response generator with RAG capabilities"""

    def __init__(self, ollama_client):
        super().__init__(ollama_client)
        try:
            self.retriever = ProductRetriever()
            if self.retriever.is_ready():
                logger.info("✅ RAG enabled - vector search ready")
                self.rag_enabled = True
            else:
                logger.warning("⚠️  RAG index not found - using fallback mode")
                self.rag_enabled = False
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}. Using standard mode.")
            self.rag_enabled = False

    def generate_with_rag(self, user_query: str, intent: str, entities: dict, context: dict = None):
        """
        Generate response using RAG

        Args:
            user_query: User's question
            intent: Classified intent
            entities: Extracted entities (brands, categories, etc.)
            context: Additional context

        Returns:
            Natural language response based on retrieved products
        """
        if not self.rag_enabled:
            # Fallback to standard generation
            logger.info("RAG not available, using standard response")
            return super().generate(user_query, intent, None, context)

        # Extract filters from entities
        filters = {}
        if entities.get('datafeed_brand'):
            filters['brand'] = entities['datafeed_brand']
        if entities.get('datafeed_category'):
            filters['category'] = entities['datafeed_category']
        if entities.get('datafeed_material'):
            filters['material'] = entities['datafeed_material']

        # Retrieve relevant products using RAG
        logger.info(f"RAG search: query='{user_query}', filters={filters}")
        products = self.retriever.search(
            query=user_query,
            k=5,
            filters=filters
        )

        if not products:
            return "I couldn't find any products matching your query. Could you try different search terms or be more specific?"

        # Build context for LLM
        product_context = self.retriever.get_product_context(products, max_products=5)

        # Generate response with RAG context
        system_prompt = """You are a helpful product assistant for ARC Brand_Delta.

IMPORTANT RULES:
- Use ONLY the product information provided below
- Be professional, friendly, and concise (1-2 sentences)
- Use **bold** for product names and important numbers
- Format products as: "**Product Name** (SKU: 12345)"
- If the answer isn't in the data, say so - never make things up
- Don't call glassware "bottles" or "wine" - use exact categories from data"""

        prompt = f"""Product Information Available:
{product_context}

User Question: {user_query}

Answer the user's question using ONLY the product information above. Be helpful and conversational."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Low temperature for factual accuracy
                max_tokens=200
            )

            if response:
                logger.info(f"RAG response generated: {response[:100]}...")
                return response
            else:
                # LLM failed, use template fallback
                return self._generate_template_fallback(products)

        except Exception as e:
            logger.error(f"RAG generation error: {e}")
            return self._generate_template_fallback(products)

    def _generate_template_fallback(self, products):
        """Simple template response if LLM fails"""
        if not products:
            return "No products found."

        if len(products) == 1:
            p = products[0]
            return f"Found: **{p.label or p.product_name}** (SKU: {p.sku}) - {p.catalog_brand}, ${p.web_price}"

        response = f"Found {len(products)} products:\n\n"
        for p in products[:5]:
            response += f"- **{p.sku}**: {p.label or p.product_name} ({p.catalog_brand}) - ${p.web_price}\n"
        return response
