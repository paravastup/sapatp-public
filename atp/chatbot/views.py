"""
Views for the chatbot application
"""

import json
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone

from .models import ChatSession, ChatMessage, MessageFeedback
from .services.ollama_client import OllamaClient
from .services.intent_classifier import IntentClassifier
from .services.entity_extractor import EntityExtractor
from .services.query_executor import QueryExecutor
from .services.response_generator import ResponseGenerator
from .services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


def _detect_field_request(user_message: str, intent: str) -> str:
    """
    Detect which specific field the user is asking about

    Args:
        user_message: User's message
        intent: Classified intent

    Returns:
        Field name like 'upc', 'brand', 'delivery', 'stock', etc.
    """
    message_lower = user_message.lower()

    # Field keyword mappings - ORDER MATTERS! Check specific before general
    field_keywords = {
        'upc': ['upc', 'ean', 'barcode', 'bar code', 'scan code'],
        'brand': ['brand', 'manufacturer', 'make', 'who makes'],
        'origin': ['origin', 'country', 'from where', 'made in', 'where made'],
        'delivery': ['delivery', 'eta', 'arrive', 'arriving', 'coming', 'next shipment', 'when will'],
        'stock': ['stock', 'inventory', 'quantity', 'how many', 'available', 'in stock', 'have any'],
        'weight': ['weight', 'how heavy', 'kg', 'pounds', 'lbs'],
        'case_pack': ['case pack', 'case', 'pack size', 'units per case', 'per case'],
        'vendor_sku': ['vendor', 'sku', 'supplier code', 'vendor code'],
        'list_price': ['list price', 'msrp', 'retail price', 'original price'],  # Specific list price
        'web_price': ['web price', 'online price', 'discounted price', 'sale price'],  # Specific web price
        'price': ['price', 'cost', 'how much', 'pricing', 'priced at', 'costs'],  # General price (shows both)
        'description': ['description', 'details', 'what is', 'describe', 'tell me about'],  # DataFeed data (removed 'about' - too greedy)
        'category': ['category', 'type', 'classification', 'group'],  # DataFeed data
        'material': ['material', 'made of', 'material type'],  # DataFeed data
        'dimensions': ['dimensions', 'size', 'measurements', 'length', 'width', 'height'],  # DataFeed data
        'collection': ['collection', 'line', 'series'],  # DataFeed data
        'image': ['image', 'picture', 'photo', 'show me'],  # DataFeed data
        'sample': ['sample', 'sampling', 'try', 'request sample', 'get sample', 'order sample'],  # Product URL
        'all_info': ['everything', 'all info', 'all details', 'information', 'tell me about']
    }

    # Check if this is a simple follow-up (e.g., "how about 10001?", "what about X?")
    # These should inherit field from context, not detect new fields
    simple_followup_patterns = ['how about', 'what about', 'and for']
    is_simple_followup = any(pattern in message_lower for pattern in simple_followup_patterns)

    # If it's a simple follow-up with just a product number and NO field keywords, inherit from context
    # But if they say "what about the price of X", we should detect "price"
    if is_simple_followup and len(message_lower.split()) <= 4:
        logger.info("Simple follow-up detected - will inherit field from context")
        return None

    # Check for explicit field mentions (e.g., "the stock", "the price")
    for field, keywords in field_keywords.items():
        for keyword in keywords:
            # Check for explicit mentions like "the stock", "the UPC", etc.
            if f"the {keyword}" in message_lower or f"for {keyword}" in message_lower:
                logger.info(f"Detected explicit field request: {field} (via 'the/for {keyword}')")
                return field
            # Also check regular keyword presence
            if keyword in message_lower:
                logger.info(f"Detected field request: {field} (via '{keyword}')")
                return field

    # Default based on intent (only if no explicit field found)
    if intent == 'delivery_query':
        return 'delivery'
    elif intent == 'stock_query':
        return 'stock'
    elif intent == 'product_info':
        return 'all_info'

    return None


@login_required
def debug_view(request):
    """Debug view to test chatbot setup"""
    from django.conf import settings

    session = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at').first()

    if not session:
        session = ChatSession.objects.create(user=request.user)

    context = {
        'session_id': session.id,
        'user': request.user,
        'ollama_url': settings.OLLAMA_BASE_URL,
    }

    return render(request, 'chatbot/debug.html', context)


def _generate_large_query_choice_response(total_products: int, brand: str = None,
                                          category: str = None, material: str = None) -> str:
    """
    Generate response offering user a choice for large queries

    Args:
        total_products: Total number of products found
        brand: Brand filter if applied
        category: Category filter if applied
        material: Material filter if applied

    Returns:
        Formatted response text with options
    """
    # Build description of what was found
    description_parts = []
    if brand:
        description_parts.append(f"**{brand}**")
    if category:
        description_parts.append(f"**{category}**")
    if material:
        description_parts.append(f"**{material}**")

    description = " ".join(description_parts) if description_parts else "your search"

    response = f"I found **{total_products} products** matching {description}.\n\n"
    response += f"Due to the large number of results, I can:\n\n"
    response += f"1. **Show first 200 products now** (takes ~30 seconds)\n"
    response += f"2. **Download only** (all {total_products} products) - Available via the bell icon 🔔. No email sent.\n"
    response += f"3. **Download + Email** (all {total_products} products) - Get both notification AND email backup.\n\n"
    response += f"Type **'show'**, **'download'**, or **'email'**."

    return response


@login_required
@ensure_csrf_cookie
def chat_view(request):
    """
    Main chat interface view
    """
    logger.info(f"Chat view accessed by user: {request.user.username}")

    # Get most recent active session (don't auto-create)
    session = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at').first()

    if session:
        logger.info(f"Using existing session {session.id} for user {request.user.username}")
        session_id = session.id
    else:
        logger.info(f"No active session found for user {request.user.username}")
        session_id = ''  # Empty - frontend will create when user sends first message

    context = {
        'session_id': session_id,
        'user': request.user,
    }

    return render(request, 'chatbot/chat.html', context)


@login_required
@require_http_methods(["POST"])
def create_session(request):
    """
    Create a new chat session
    All previous sessions remain active and visible in sidebar
    """
    try:
        # Simply create new session - keep all old sessions active
        # All sessions stay is_active=True for sidebar visibility
        session = ChatSession.objects.create(user=request.user)

        logger.info(f"Created new session {session.id} for user {request.user.username}")

        return JsonResponse({
            'success': True,
            'session_id': session.id
        })

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def process_message(request):
    """
    Process user message and generate response
    """
    try:
        logger.info(f"Processing message from user: {request.user.username}")

        # Parse request data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()

        logger.info(f"Session ID: {session_id}, Message: {user_message[:50] if user_message else 'empty'}")

        if not user_message:
            logger.warning("Empty message received")
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)

        # Get session
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=404)

        # Initialize services
        ollama = OllamaClient()
        intent_classifier = IntentClassifier(ollama)
        entity_extractor = EntityExtractor()
        query_executor = QueryExecutor(request.user)
        # Use RAG-enhanced response generator for accurate, natural responses
        from .services.response_generator_rag import RAGResponseGenerator
        response_generator = RAGResponseGenerator(ollama)
        conversation_manager = ConversationManager(session)

        # Save user message
        user_msg = conversation_manager.add_message('user', user_message)

        # Get conversation context and history
        context = conversation_manager.get_context()
        history = conversation_manager.get_history()

        # Classify intent
        intent, confidence = intent_classifier.classify(user_message, history)
        logger.info(f"Intent: {intent} (confidence: {confidence})")

        # EXPORT REQUEST DETECTION WITH CACHED RESULTS
        # If user says "email them", "export", "download", etc. AND has cached results,
        # treat as export_request even if LLM classified it differently
        export_keywords = ['email', 'send', 'mail', 'export', 'download', 'excel', 'csv', 'pdf']
        user_msg_lower = user_message.lower().strip()
        has_export_keyword = any(kw in user_msg_lower for kw in export_keywords)
        cached_results = conversation_manager.get_cached_results()

        if has_export_keyword and cached_results and len(cached_results) > 0:
            logger.info(f"[EXPORT OVERRIDE] Detected export keyword with {len(cached_results)} cached results. Overriding intent to 'export_request'")
            intent = 'export_request'
            confidence = 0.95

        # LARGE QUERY CHOICE DETECTION
        # If user is responding to large query choice (pending query exists)
        pending_query = conversation_manager.get_pending_query()
        if pending_query:
            user_msg_lower = user_message.lower().strip()

            # IMPORTANT: Don't override if user is asking about specific products
            # e.g., "show me the image of 10002" should NOT trigger large_query_show_partial
            has_specific_product = bool(entities.get('product_numbers'))

            # User wants to see first 200 (only if NOT asking about specific products)
            show_keywords = ['show', 'first', '200', 'partial', 'see them', 'display', 'view', 'now']
            if not has_specific_product and any(kw in user_msg_lower for kw in show_keywords):
                intent = 'large_query_show_partial'
                confidence = 0.95
                logger.info("[LARGE QUERY] User selected: Show First 200")

            # User wants download only (no email) - only if NOT asking about specific products
            download_only_keywords = ['download', 'export']
            if not has_specific_product and any(kw in user_msg_lower for kw in download_only_keywords) and not any(kw in user_msg_lower for kw in ['email', 'mail']):
                intent = 'large_query_download_only'
                confidence = 0.95
                logger.info("[LARGE QUERY] User selected: Download Only (no email)")

            # User wants email + download - only if NOT asking about specific products
            email_keywords = ['email', 'send', 'mail']
            if not has_specific_product and any(kw in user_msg_lower for kw in email_keywords):
                intent = 'large_query_email_all'
                confidence = 0.95
                logger.info("[LARGE QUERY] User selected: Download + Email")

        # SMART ACTION REPEAT DETECTION
        # Check if user wants to repeat last action (e.g., "do the same with 10001")
        is_action_repeat = conversation_manager.detect_action_repeat(user_message)
        if is_action_repeat:
            last_action = conversation_manager.get_last_action()
            if last_action.get('intent'):
                logger.info(f"Action repeat detected! Using last intent: {last_action['intent']}")
                intent = last_action['intent']  # Override with last intent
                confidence = 0.95  # High confidence for detected repeats

        # Extract entities (pass conversation history for context)
        entities = entity_extractor.extract(user_message, intent, context, history)

        # If action repeat and last field requested, add to entities
        if is_action_repeat:
            last_action = conversation_manager.get_last_action()
            if last_action.get('field'):
                entities['field_requested'] = last_action['field']
                logger.info(f"Applying last field request: {last_action['field']}")

        logger.info(f"Entities: {entities}")

        # Check if plant selection is needed
        if not context.get('selected_plant'):
            user_plants = request.user.plant.all()

            if user_plants.count() > 1:
                # Check if user specified a plant in message
                selected_plant = None
                for plant in user_plants:
                    if plant.code in user_message or plant.description.lower() in user_message.lower():
                        selected_plant = plant
                        break

                if selected_plant:
                    conversation_manager.set_selected_plant(selected_plant.code)
                    context = conversation_manager.get_context()
                else:
                    # Need to ask user to select plant
                    response_text = "I see you have access to multiple plants. Which one would you like to check?"
                    assistant_msg = conversation_manager.add_message(
                        'assistant',
                        response_text,
                        {'intent': 'plant_selection_required'}
                    )

                    return JsonResponse({
                        'success': True,
                        'response': response_text,
                        'requires_plant_selection': True,
                        'available_plants': [
                            {
                                'code': p.code,
                                'description': p.description
                            }
                            for p in user_plants
                        ],
                        'intent': 'plant_selection',
                        'confidence': 1.0
                    })

            elif user_plants.count() == 1:
                # Auto-select single plant
                conversation_manager.set_selected_plant(user_plants.first().code)
                context = conversation_manager.get_context()
            else:
                # No plants assigned
                response_text = "You don't have access to any plants. Please contact your administrator."
                conversation_manager.add_message('assistant', response_text)
                return JsonResponse({
                    'success': True,
                    'response': response_text,
                    'intent': 'error',
                    'confidence': 1.0
                })

        # Execute query based on intent
        results = None
        response_text = ""

        if intent in ['stock_query', 'delivery_query', 'product_info', 'comparison']:
            # Get plant and products
            plant_code = context.get('selected_plant')
            products = entities.get('product_numbers', [])

            if not products:
                products = entities.get('vendor_skus', [])

            # Check for bulk query (e.g., "Show me all Brand Zeta products")
            if not products and entities.get('is_bulk_query'):
                # Import ProductService if available
                try:
                    from products.services import ProductService

                    # Get SKUs based on brand, category, or material
                    brand = entities.get('datafeed_brand')
                    category = entities.get('datafeed_category')
                    material = entities.get('datafeed_material')

                    logger.info(f"[BULK QUERY] Detected! brand={brand}, category={category}, material={material}")

                    if brand or category or material:
                        logger.info(f"[BULK QUERY] Fetching SKUs for filters...")
                        skus = ProductService.get_skus_for_bulk_query(
                            brand=brand,
                            category=category,
                            material=material,
                            limit=1000  # Allow up to 1000 products (no practical limit)
                        )
                        products = skus
                        logger.info(f"[BULK QUERY] Found {len(products)} products: {products[:5]}...")
                        logger.info(f"[BULK QUERY] Plant code: {plant_code}")

                        # Store total count in context
                        context['total_products_found'] = len(products)

                        # THRESHOLD: If 200+ products, offer user choice instead of executing immediately
                        if len(products) > 200:
                            logger.info(f"[LARGE QUERY CHOICE] {len(products)} products - offering user choice")

                            # Store pending query for later execution
                            conversation_manager.store_pending_query({
                                'products': products,
                                'plant_code': plant_code,
                                'mode': 'M',  # Default to material number mode
                                'intent': intent,
                                'search_type': entities.get('search_type', 'arc_sku'),
                                'brand': entities.get('datafeed_brand'),
                                'category': entities.get('datafeed_category'),
                                'material': entities.get('datafeed_material')
                            })

                            # Generate choice response (function exists at line 115)
                            response_text = _generate_large_query_choice_response(
                                total_products=len(products),
                                brand=entities.get('datafeed_brand'),
                                category=entities.get('datafeed_category'),
                                material=entities.get('datafeed_material')
                            )

                            # Save assistant message
                            assistant_msg = conversation_manager.add_message(
                                'assistant',
                                response_text,
                                {'intent': 'large_query_choice', 'total_products': len(products)}
                            )

                            # Return response that triggers choice buttons in frontend
                            return JsonResponse({
                                'success': True,
                                'response': response_text,
                                'needs_user_choice': True,
                                'choice_type': 'large_query',
                                'total_products': len(products),
                                'intent': 'large_query_choice',
                                'confidence': 1.0,
                                'message_id': assistant_msg.id
                            })
                    else:
                        logger.warning("[BULK QUERY] No brand/category/material found!")
                except ImportError as e:
                    logger.error(f"[BULK QUERY] ProductService not available: {e}")
                except Exception as e:
                    logger.error(f"[BULK QUERY] Error fetching SKUs: {e}")

            # Check threshold for stock queries (not bulk product discovery)
            # For bulk queries, use RAG regardless of result count
            is_bulk_query = entities.get('is_bulk_query', False)
            if products and len(products) > 200 and not is_bulk_query:
                logger.info(f"[LARGE QUERY CHOICE] {len(products)} products (stock query) - offering user choice")

                # Get plant code from context or user plants
                if not plant_code:
                    plant_code = context.get('selected_plant')

                if plant_code:
                    # Store pending query
                    conversation_manager.store_pending_query({
                        'products': products,
                        'plant_code': plant_code,
                        'mode': 'O' if entities.get('search_type') == 'vendor_sku' else 'M',
                        'intent': intent,
                        'search_type': entities.get('search_type', 'arc_sku'),
                        'brand': entities.get('datafeed_brand'),
                        'category': entities.get('datafeed_category'),
                        'material': entities.get('datafeed_material')
                    })

                    # Generate choice response
                    response_text = _generate_large_query_choice_response(
                        total_products=len(products),
                        brand=entities.get('datafeed_brand'),
                        category=entities.get('datafeed_category'),
                        material=entities.get('datafeed_material')
                    )

                    # Save assistant message
                    assistant_msg = conversation_manager.add_message(
                        'assistant',
                        response_text,
                        {'intent': 'large_query_choice', 'total_products': len(products)}
                    )

                    # Return response that triggers choice buttons in frontend
                    return JsonResponse({
                        'success': True,
                        'response': response_text,
                        'needs_user_choice': True,
                        'choice_type': 'large_query',
                        'total_products': len(products),
                        'intent': 'large_query_choice',
                        'confidence': 1.0,
                        'message_id': assistant_msg.id
                    })

            if products and plant_code:
                # Determine search mode
                mode = 'O' if entities.get('search_type') == 'vendor_sku' else 'M'
                search_type = 'vendor_sku' if mode == 'O' else 'arc_sku'

                # Set current products in context (for future follow-up questions)
                conversation_manager.set_current_products(products, search_type)

                # Execute SAP query
                logger.info(f"[SAP QUERY] Executing for {len(products)} products")
                results = query_executor.execute_search(plant_code, products, mode)
                logger.info(f"[SAP QUERY] Got {len(results)} results back")

                # Cache results with product information
                conversation_manager.cache_results(results, products, search_type)

                # Detect specific field requested
                # PRIORITY: Explicit field in current message > Last action field > Intent default
                current_field = _detect_field_request(user_message, intent)

                # Get field from last action context (for follow-up questions)
                last_action = conversation_manager.get_last_action()
                last_field = last_action.get('field') if last_action else None

                # Use current field if explicitly mentioned, otherwise inherit from last action
                if current_field and current_field != 'all_info':
                    field_requested = current_field
                    logger.info(f"Field explicitly requested in message: {field_requested}")
                elif last_field and current_field is None:
                    # Inherit from last action if no new field detected
                    field_requested = last_field
                    logger.info(f"Field inherited from last action: {field_requested}")
                else:
                    field_requested = current_field  # Could be None or 'all_info'
                    logger.info(f"Field defaulted based on intent: {field_requested}")

                # Check if this is a follow-up query (for cleaner responses)
                followup_phrases = ['how about', 'what about', 'and for', 'how many']
                is_followup = any(phrase in user_message.lower() for phrase in followup_phrases)

                # Add follow-up flag to context for response formatting
                enhanced_context = context.copy() if context else {}
                enhanced_context['is_followup'] = is_followup

                # Generate response (pass field_requested for smarter responses)
                response_text = response_generator.generate(
                    user_message,
                    intent,
                    results,
                    enhanced_context,
                    field_requested=field_requested
                )

                # Track this action for intelligent follow-ups
                conversation_manager.track_action(
                    intent=intent,
                    field_requested=field_requested,
                    action_description=f"Queried {intent} for products {products}"
                )

                # Mark message as having executed SAP query
                user_msg.sap_query_executed = True
                user_msg.save()

            else:
                # Missing information OR bulk query (product discovery without stock check)
                if not products:
                    response_text = "I need product number(s) to help you. Could you provide them?"
                elif entities.get('is_bulk_query'):
                    # Bulk query - use RAG for natural product discovery (no stock check)
                    logger.info(f"[RAG BULK QUERY] Using RAG for {len(products)} products")
                    try:
                        response_text = response_generator.generate_with_rag(
                            user_query=user_message,
                            intent='product_info',
                            entities=entities,
                            context=context
                        )
                    except Exception as e:
                        logger.error(f"[RAG ERROR] {e}, falling back to standard list")
                        # Fallback: We have products from bulk query but no plant - show product list
                        logger.info("[BULK RESPONSE] Generating formatted product list")
                        brand = entities.get('datafeed_brand')
                        category = entities.get('datafeed_category')
                        material = entities.get('datafeed_material')

                        filter_type = brand or category or material
                        response_text = f"I found **{len(products)}** products"
                        if filter_type:
                            response_text += f" for **{filter_type}**"
                        response_text += ":\n\n"

                        # List all products (no limit)
                        for i, sku in enumerate(products, 1):
                            # Try to get product name from DataFeed
                            try:
                                from products.services import ProductService
                                product_data = ProductService.get_product_enrichment(sku)
                                if product_data:
                                    name = product_data.get('name', '')
                                    response_text += f"{i}. **{sku}**"
                                    if name:
                                        response_text += f" - {name[:50]}"
                                    response_text += "\n"
                                else:
                                    response_text += f"{i}. **{sku}**\n"
                            except Exception as e:
                                logger.error(f"[BULK RESPONSE] Error enriching {sku}: {e}")
                                response_text += f"{i}. **{sku}**\n"

                        response_text += "\n*To check stock levels, please select a plant first.*"
                        logger.info(f"[BULK RESPONSE] Generated response with {len(products)} products")
                elif not plant_code:
                    # Check if user is asking for product info that doesn't need stock (image, price, UPC, sample, etc.)
                    field_requested = _detect_field_request(user_message, intent)
                    non_stock_fields = ['image', 'price', 'list_price', 'web_price', 'upc', 'brand', 'origin',
                                       'description', 'category', 'material', 'dimensions', 'collection', 'weight',
                                       'case_pack', 'vendor_sku', 'sample']

                    if field_requested in non_stock_fields and products:
                        # User wants product info that doesn't require stock check - fetch from DataFeed
                        logger.info(f"[PRODUCT INFO] Field '{field_requested}' requested for {len(products)} products (no plant needed)")
                        try:
                            from products.services import ProductService
                            results = []
                            for sku in products:
                                enrichment = ProductService.get_product_enrichment(sku)
                                if enrichment:
                                    results.append(enrichment)

                            if results:
                                # Generate response with field_requested
                                response_text = response_generator.generate(
                                    user_message,
                                    intent,
                                    results,
                                    context,
                                    field_requested=field_requested
                                )
                            else:
                                response_text = f"I couldn't find information for {', '.join(products)}."
                        except Exception as e:
                            logger.error(f"[PRODUCT INFO ERROR] {e}")
                            response_text = f"Sorry, I encountered an error retrieving product information."
                    else:
                        # Stock/delivery query needs plant selection
                        logger.info("[STOCK QUERY] No plant selected, asking for plant")
                        response_text = "Please select a plant first to check stock levels."

        elif intent == 'large_query_show_partial':
            # Execute query for first 200 products only
            pending = conversation_manager.get_pending_query()
            if pending:
                products = pending['products'][:200]  # Limit to 200
                plant_code = pending['plant_code']
                mode = pending['mode']
                search_type = pending.get('search_type', 'arc_sku')

                logger.info(f"[LARGE QUERY PARTIAL] Executing for first 200 of {len(pending['products'])} products")

                # Set current products in context
                conversation_manager.set_current_products(products, search_type)

                # Execute SAP query for 200 products
                results = query_executor.execute_search(plant_code, products, mode)
                logger.info(f"[LARGE QUERY PARTIAL] Got {len(results)} results back")

                # Cache results with truncation info
                conversation_manager.cache_results(results, products, search_type)

                # Generate response with truncation notice
                response_text = response_generator.generate(
                    user_message,
                    'product_info',
                    results,
                    {'truncated': True, 'total_available': len(pending['products'])}
                )

                # Clear pending query
                conversation_manager.clear_pending_query()

        elif intent == 'large_query_download_only':
            # Download only (no email) - save file and create notification
            pending = conversation_manager.get_pending_query()
            if pending:
                total_products = len(pending['products'])
                logger.info(f"[LARGE QUERY DOWNLOAD] Triggering download-only for {total_products} products")

                response_text = f"Perfect! I'm preparing your complete report with all **{total_products} products**...\n\nThis may take 30-60 seconds to query SAP and generate the file. Watch the bell icon 🔔 - you'll get a notification when your download is ready!"

                # Save assistant message
                assistant_msg = conversation_manager.add_message(
                    'assistant',
                    response_text,
                    {'intent': intent, 'total_products': total_products}
                )

                # Frontend will trigger download-only endpoint
                return JsonResponse({
                    'success': True,
                    'response': response_text,
                    'trigger_large_query_download': True,  # Different flag for download-only
                    'total_products': total_products,
                    'intent': intent,
                    'confidence': confidence,
                    'message_id': assistant_msg.id
                })
            else:
                response_text = "I don't have any pending query. Please start a new search."

        elif intent == 'large_query_email_all':
            # Trigger email export for all products
            pending = conversation_manager.get_pending_query()
            if pending:
                total_products = len(pending['products'])
                logger.info(f"[LARGE QUERY EMAIL] Triggering email for all {total_products} products")

                response_text = f"Perfect! I'm preparing your complete report with all **{total_products} products**...\n\nThis may take 30-60 seconds to query SAP and generate the file. Watch the bell icon 🔔 - you'll get a notification when your download is ready!"

                # Save assistant message
                assistant_msg = conversation_manager.add_message(
                    'assistant',
                    response_text,
                    {'intent': intent, 'total_products': total_products}
                )

                # Frontend will auto-trigger email via trigger_large_query_email
                return JsonResponse({
                    'success': True,
                    'response': response_text,
                    'trigger_large_query_email': True,
                    'email_address': request.user.email,
                    'total_products': total_products,
                    'intent': intent,
                    'confidence': confidence,
                    'message_id': assistant_msg.id
                })
            else:
                response_text = "I don't have any pending query. Please start a new search."

        elif intent == 'export_request':
            # Handle export
            cached_results = conversation_manager.get_cached_results()

            # Detect export format from user message (more flexible)
            user_msg_lower = user_message.lower()
            export_format = 'excel'  # default

            if any(word in user_msg_lower for word in ['email', 'send', 'mail']):
                export_format = 'email'
            elif any(word in user_msg_lower for word in ['csv', 'comma']):
                export_format = 'csv'
            elif any(word in user_msg_lower for word in ['pdf', 'document', 'report']):
                export_format = 'pdf'
            elif any(word in user_msg_lower for word in ['excel', 'xlsx', 'spreadsheet']):
                export_format = 'excel'

            if cached_results:
                results = cached_results  # Pass cached results for export
                # Store export format in entities for frontend
                entities['export_format'] = export_format

                # Generate natural response using response_generator
                response_text = response_generator.generate(
                    user_message,
                    intent,
                    results,
                    {'export_format': export_format}
                )
            else:
                response_text = "I don't have any results to export. Please run a search first."

        elif intent == 'plant_selection':
            # Handle plant selection
            plant_code = entities.get('plant_code')
            if plant_code:
                # Verify user has access
                if request.user.plant.filter(code=plant_code).exists():
                    conversation_manager.set_selected_plant(plant_code)
                    response_text = f"Great! I've selected plant {plant_code}. What would you like to check?"
                else:
                    response_text = f"You don't have access to plant {plant_code}."
            else:
                response_text = "Which plant would you like to use?"

        elif intent == 'help':
            response_text = response_generator.generate_help_response()

        elif intent == 'greeting':
            response_text = response_generator.generate_greeting_response({
                'username': request.user.username
            })

        else:
            # Generic or clarification
            response_text = response_generator.generate(
                user_message,
                intent,
                None,
                context
            )

        # Save assistant message (include results for export functionality)
        assistant_msg = conversation_manager.add_message(
            'assistant',
            response_text,
            {
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'results': results if results else None  # Save results for inline export buttons
            }
        )

        # Log intent for analytics
        from .models import IntentLog
        IntentLog.objects.create(
            message=user_msg,
            detected_intent=intent,
            confidence=confidence,
            entities=json.dumps(entities)
        )

        # Prepare response
        # LOG THE ACTUAL RESPONSE BEING SENT
        logger.info(f"[RESPONSE TO FRONTEND] Length: {len(response_text)}, Text: {response_text[:200]}")

        response_data = {
            'success': True,
            'response': response_text,
            'intent': intent,
            'confidence': confidence,
            'results': results,
            'message_id': assistant_msg.id,  # For feedback buttons
            'export_ready': intent == 'export_request' and results is not None,  # Flag for inline export buttons
            'export_format': entities.get('export_format') if intent == 'export_request' else None,  # What format user requested
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred processing your message. Please try again.',
            'detail': str(e) if request.user.is_staff else None
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_history(request, session_id):
    """
    Get conversation history for a session
    """
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user
        )

        messages = session.messages.all().order_by('timestamp')

        history = [
            {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'metadata': msg.get_metadata()
            }
            for msg in messages
        ]

        return JsonResponse({
            'success': True,
            'history': history,
            'session_id': session.id
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_all_sessions(request):
    """
    Get all chat sessions for the current user (for sidebar history)
    """
    try:
        # Get last 20 ACTIVE sessions, ordered by most recent activity
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:20]

        session_list = []
        for session in sessions:
            # Get first user message as preview
            first_msg = session.messages.filter(role='user').first()
            preview = first_msg.content[:60] if first_msg else 'New conversation'

            # Get message count
            msg_count = session.messages.count()

            session_list.append({
                'id': session.id,
                'preview': preview,
                'message_count': msg_count,
                'updated_at': session.updated_at.isoformat(),
                'is_active': session.is_active
            })

        return JsonResponse({
            'success': True,
            'sessions': session_list
        })

    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_session(request, session_id):
    """
    Delete (archive) a specific chat session
    """
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user
        )

        # Soft delete - mark as inactive instead of hard delete
        session.is_active = False
        session.save()

        logger.info(f"User {request.user.username} deleted session {session_id}")

        return JsonResponse({
            'success': True,
            'message': 'Conversation deleted'
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_all_sessions(request):
    """
    Delete (archive) all chat sessions for the current user
    """
    try:
        # Check how many active sessions exist
        active_sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        )

        # If no active sessions, nothing to delete
        if active_sessions.count() == 0:
            return JsonResponse({
                'success': True,
                'message': 'Nothing to delete',
                'count': 0,
                'nothing_to_delete': True
            })

        # Soft delete - mark all sessions as inactive
        deleted_count = active_sessions.update(is_active=False)

        logger.info(f"User {request.user.username} deleted {deleted_count} sessions")

        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} conversation(s) deleted',
            'count': deleted_count,
            'nothing_to_delete': False
        })

    except Exception as e:
        logger.error(f"Error deleting all sessions: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_autocomplete(request):
    """
    Get autocomplete suggestions for search bar
    """
    try:
        query = request.GET.get('q', '').strip()

        # Import autocomplete service
        from .services.autocomplete_service import AutocompleteService

        # Get suggestions
        autocomplete = AutocompleteService(user=request.user)
        suggestions = autocomplete.get_suggestions(query, max_suggestions=7)

        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"Error getting autocomplete suggestions: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'suggestions': []
        })


@login_required
@require_http_methods(["POST"])
def submit_feedback(request):
    """
    Submit user feedback (thumbs up/down) for a message
    """
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')  # 1 for thumbs up, -1 for thumbs down
        comment = data.get('comment', '')
        issue_type = data.get('issue_type', '')

        logger.info(f"Feedback from user {request.user.username}: message={message_id}, rating={rating}")

        # Validate rating
        if rating not in [1, -1]:
            return JsonResponse({
                'success': False,
                'error': 'Invalid rating. Must be 1 (thumbs up) or -1 (thumbs down)'
            }, status=400)

        # Get the message
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                role='assistant',
                session__user=request.user
            )
        except ChatMessage.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Message not found or access denied'
            }, status=404)

        # Create or update feedback
        feedback, created = MessageFeedback.objects.update_or_create(
            message=message,
            defaults={
                'rating': rating,
                'comment': comment,
                'issue_type': issue_type if rating == -1 else ''
            }
        )

        # Update analytics
        from django.utils import timezone
        from .models import ChatAnalytics

        today = timezone.now().date()
        analytics, _ = ChatAnalytics.objects.get_or_create(date=today)

        if created:
            # First time feedback
            if rating == 1:
                analytics.thumbs_up_count += 1
            else:
                analytics.thumbs_down_count += 1
        else:
            # Updating feedback - adjust counts
            old_feedback = MessageFeedback.objects.get(message=message)
            if old_feedback.rating != rating:
                if rating == 1:
                    analytics.thumbs_up_count += 1
                    analytics.thumbs_down_count -= 1
                else:
                    analytics.thumbs_down_count += 1
                    analytics.thumbs_up_count -= 1

        analytics.save()

        logger.info(f"Feedback saved: {feedback}")

        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback.id
        })

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred submitting your feedback'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def export_email(request):
    """
    Export results via email with comprehensive audit logging
    Regular users can only send to their own email
    Admins can send to any email address
    """
    from .models import EmailAuditLog

    audit_log = None

    try:
        import csv
        import io
        from django.core.mail import EmailMessage
        from django.conf import settings

        data = json.loads(request.body)
        email_address = data.get('email_address', '').strip()
        results = data.get('results', [])
        session_id = data.get('session_id')

        if not email_address:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required'
            }, status=400)

        if not results:
            return JsonResponse({
                'success': False,
                'error': 'No results to export'
            }, status=400)

        # Get IP address and user agent for audit
        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Detect if sending to personal email (non-company domain)
        company_domains = ['democorp.example.com', 'democorp-intl.example.com']  # Configure as needed
        is_personal_email = not any(email_address.lower().endswith('@' + domain) for domain in company_domains)

        # Check if admin override (sending to different email)
        is_admin_override = (request.user.is_staff or request.user.is_superuser) and (email_address != request.user.email)

        # Security check: Regular users can only email to themselves
        if not (request.user.is_staff or request.user.is_superuser):
            if email_address != request.user.email:
                # Log blocked attempt
                audit_log = EmailAuditLog.objects.create(
                    user=request.user,
                    recipient_email=email_address,
                    subject='Blocked - Unauthorized recipient',
                    csv_filename='N/A',
                    csv_content='',
                    product_count=len(results),
                    status='blocked',
                    error_message=f'User attempted to send to {email_address} but only allowed to send to {request.user.email}',
                    is_to_personal_email=is_personal_email,
                    is_admin_override=False,
                    ip_address=ip_address,
                    user_agent=user_agent[:500]  # Truncate to fit
                )

                logger.warning(
                    f"[AUDIT] Blocked email export: {request.user.username} tried to send to {email_address}"
                )
                return JsonResponse({
                    'success': False,
                    'error': 'You can only send reports to your own email address'
                }, status=403)

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Product Number',
            'Description',
            'Brand',
            'Current Stock',
            'Unit',
            'Next Delivery Date',
            'Delivery Quantity',
            'UPC/EAN',
            'Weight (kg)',
            'Country of Origin',
            'Vendor',
            'Purchase Order',
            'Case Pack Size'
        ])

        # Write data rows
        for item in results:
            writer.writerow([
                item.get('MATNR', item.get('product', '')),
                item.get('MAKTX', item.get('description', '')),
                item.get('ZZBRAND', item.get('brand', '')),
                item.get('STOCK', item.get('stock', item.get('LABST', '0'))),
                item.get('MEINS', item.get('unit', '')),
                item.get('EEIND', item.get('next_delivery', item.get('EINDT', ''))),
                item.get('OMENG', item.get('delivery_qty', item.get('MENGE', '0'))),
                item.get('EAN11', item.get('upc', '')),
                item.get('BRGEW', item.get('weight', '')),
                item.get('HERKL', item.get('origin', '')),
                item.get('ZBRDES', item.get('vendor', '')),
                item.get('EBELN', item.get('po', '')),
                item.get('UMREZ', item.get('case_pack', ''))
            ])

        csv_content = output.getvalue()
        output.close()

        # Create email
        subject = f'ATP Product Report - {len(results)} Product(s)'
        message = f'''Hello,

Your ATP product report is attached.

Report Details:
- Products: {len(results)}
- Generated by: {request.user.username}
- Date: {json.dumps({"time": "now"})}

This is an automated email from the ATP Product Availability System.

Best regards,
ATP System'''

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_address],
        )

        # Attach CSV file
        from datetime import datetime
        filename = f'atp_product_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        email.attach(filename, csv_content, 'text/csv')

        # Send email
        email.send(fail_silently=False)

        # Get session if available
        session_obj = None
        if session_id:
            try:
                from .models import ChatSession
                session_obj = ChatSession.objects.get(id=session_id, user=request.user)
            except:
                pass

        # Log successful email export with full audit trail
        audit_log = EmailAuditLog.objects.create(
            user=request.user,
            recipient_email=email_address,
            subject=subject,
            csv_filename=filename,
            csv_content=csv_content,  # Store FULL CSV for audit
            product_count=len(results),
            session=session_obj,
            status='success',
            is_to_personal_email=is_personal_email,
            is_admin_override=is_admin_override,
            ip_address=ip_address,
            user_agent=user_agent[:500]
        )

        # Save CSV file for download from admin
        from django.core.files.base import ContentFile
        audit_log.csv_file.save(filename, ContentFile(csv_content.encode('utf-8')), save=True)

        # Create notification for user
        from .models import ExportNotification
        notification_message = f"Export ready: {len(results)} products"
        ExportNotification.objects.create(
            user=request.user,
            export_log=audit_log,
            message=notification_message,
            is_read=False
        )

        logger.info(
            f"[AUDIT] Email export successful: {request.user.username} → {email_address} "
            f"({len(results)} products) [Audit Log ID: {audit_log.id}]"
        )

        # Add security alert if sending to personal email
        if is_personal_email:
            logger.warning(
                f"[SECURITY] User {request.user.username} sent data to personal email: {email_address}"
            )

        return JsonResponse({
            'success': True,
            'message': f'Report emailed to {email_address}. Check the bell icon for download link.',
            'audit_log_id': audit_log.id
        })

    except Exception as e:
        # Log failed attempt
        if audit_log is None:
            try:
                audit_log = EmailAuditLog.objects.create(
                    user=request.user,
                    recipient_email=email_address if 'email_address' in locals() else 'unknown',
                    subject='Failed to send',
                    csv_filename='N/A',
                    csv_content='',
                    product_count=len(results) if 'results' in locals() else 0,
                    status='failed',
                    error_message=str(e)[:500],
                    is_to_personal_email=False,
                    is_admin_override=False,
                    ip_address=ip_address if 'ip_address' in locals() else None,
                    user_agent=user_agent[:500] if 'user_agent' in locals() else ''
                )
            except:
                pass  # If audit log creation fails, just continue

        logger.error(f"[AUDIT] Error exporting via email: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred sending the email. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def export_large_query(request):
    """
    Process large query (>200 products) and email the complete report
    Uses pending query data stored in session context
    """
    try:
        import csv
        import io
        from django.core.mail import EmailMessage
        from django.conf import settings

        data = json.loads(request.body)
        session_id = data.get('session_id')
        email_address = data.get('email_address', request.user.email).strip()

        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID is required'
            }, status=400)

        # Get session and conversation manager
        session = ChatSession.objects.get(id=session_id, user=request.user)
        conversation_manager = ConversationManager(session)

        # Get pending query data
        pending_query = conversation_manager.get_pending_query()
        if not pending_query:
            return JsonResponse({
                'success': False,
                'error': 'No pending query found. Please try your search again.'
            }, status=400)

        # Security check: Regular users can only email to themselves
        if not (request.user.is_staff or request.user.is_superuser):
            if email_address != request.user.email:
                return JsonResponse({
                    'success': False,
                    'error': 'You can only send reports to your own email address'
                }, status=403)

        # Extract query parameters
        products = pending_query.get('products', [])
        plant_code = pending_query.get('plant_code')
        mode = pending_query.get('mode', 'M')
        brand = pending_query.get('brand')
        category = pending_query.get('category')
        material = pending_query.get('material')

        if not products or not plant_code:
            return JsonResponse({
                'success': False,
                'error': 'Invalid query data'
            }, status=400)

        logger.info(f"[LARGE QUERY EMAIL] Processing {len(products)} products for {email_address}")

        # Return immediate acknowledgment
        response_msg = f"I'm processing all **{len(products)} products** and will email the report to **{email_address}** shortly. This may take a few minutes..."

        # Execute SAP queries for all products
        query_executor = QueryExecutor(request.user)
        results = query_executor.execute_search(plant_code, products, mode)

        logger.info(f"[LARGE QUERY EMAIL] Got {len(results)} results, generating CSV")

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Product Number',
            'Description',
            'Brand',
            'Current Stock',
            'Unit',
            'Next Delivery Date',
            'Delivery Quantity',
            'UPC/EAN',
            'Weight (kg)',
            'Country of Origin',
            'Vendor',
            'Purchase Order',
            'Case Pack Size'
        ])

        # Write data rows
        for item in results:
            if 'error' not in item:  # Skip error entries
                writer.writerow([
                    item.get('MATNR', ''),
                    item.get('MAKTX', ''),
                    item.get('ZZBRAND', ''),
                    item.get('STOCK', '0'),
                    item.get('MEINS', ''),
                    item.get('EEIND', ''),
                    item.get('OMENG', '0'),
                    item.get('EAN11', ''),
                    item.get('BRGEW', ''),
                    item.get('HERKL', ''),
                    item.get('ZBRDES', ''),
                    item.get('EBELN', ''),
                    item.get('UMREZ', '')
                ])

        csv_content = output.getvalue()
        output.close()

        # Build description
        description_parts = []
        if brand:
            description_parts.append(f"{brand}")
        if category:
            description_parts.append(f"{category}")
        if material:
            description_parts.append(f"{material}")
        description = " - ".join(description_parts) if description_parts else "Bulk Query"

        # Create email
        subject = f'ATP Large Query Report - {len(results)} Products - {description}'
        message = f'''Hello {request.user.username},

Your ATP large query report is attached.

Report Details:
- Query: {description}
- Total Products: {len(results)}
- Plant: {plant_code}
- Generated by: {request.user.username}
- Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}

This is an automated email from the ATP Product Availability System.

Best regards,
ATP System'''

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@atp.com'),
            to=[email_address]
        )

        # Attach CSV
        email.attach(f'atp_report_{description}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv',
                     csv_content, 'text/csv')

        # Send email
        email.send()

        # Get IP address for audit
        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Detect personal email
        company_domains = ['democorp.example.com', 'democorp-intl.example.com']
        is_personal_email = not any(email_address.lower().endswith('@' + domain) for domain in company_domains)
        is_admin_override = (request.user.is_staff or request.user.is_superuser) and (email_address != request.user.email)

        # Save to audit log with CSV file
        from .models import EmailAuditLog, ExportNotification
        from django.core.files.base import ContentFile

        filename = f'atp_report_{description}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'

        audit_log = EmailAuditLog.objects.create(
            user=request.user,
            recipient_email=email_address,
            subject=subject,
            csv_filename=filename,
            csv_content=csv_content,
            product_count=len(results),
            session=session,
            status='success',
            is_to_personal_email=is_personal_email,
            is_admin_override=is_admin_override,
            ip_address=ip_address,
            user_agent=user_agent[:500]
        )

        # Save CSV file for download
        audit_log.csv_file.save(filename, ContentFile(csv_content.encode('utf-8')), save=True)

        # Create notification for user
        notification_message = f"Export ready: {len(results)} products from {description}"
        ExportNotification.objects.create(
            user=request.user,
            export_log=audit_log,
            message=notification_message,
            is_read=False
        )

        # Clear pending query
        conversation_manager.clear_pending_query()

        logger.info(f"[LARGE QUERY EMAIL] Sent {len(results)} products to {email_address}, Audit Log: {audit_log.id}")

        return JsonResponse({
            'success': True,
            'message': f'Report with {len(results)} products ready for download',
            'response': f"✅ Your report with **{len(results)} products** is ready!\n\n🔔 Click the bell icon in the navbar to download the file.\n\n📧 A copy has also been emailed to **{email_address}** as backup.",
            'audit_log_id': audit_log.id
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid session'
        }, status=404)
    except Exception as e:
        logger.error(f"Error processing large query email: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error processing request: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def download_large_query(request):
    """
    Process large query download (>200 products) WITHOUT sending email
    Saves file, creates notification, logs audit - but skips email step
    """
    try:
        import csv
        import io
        from django.conf import settings

        data = json.loads(request.body)
        session_id = data.get('session_id')

        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID is required'
            }, status=400)

        # Get session and conversation manager
        session = ChatSession.objects.get(id=session_id, user=request.user)
        conversation_manager = ConversationManager(session)

        # Get pending query data
        pending_query = conversation_manager.get_pending_query()
        if not pending_query:
            return JsonResponse({
                'success': False,
                'error': 'No pending query found. Please try your search again.'
            }, status=400)

        # Extract query parameters
        products = pending_query.get('products', [])
        plant_code = pending_query.get('plant_code')
        mode = pending_query.get('mode', 'M')
        brand = pending_query.get('brand')
        category = pending_query.get('category')
        material = pending_query.get('material')

        if not products or not plant_code:
            return JsonResponse({
                'success': False,
                'error': 'Invalid query data'
            }, status=400)

        logger.info(f"[LARGE QUERY DOWNLOAD] Processing {len(products)} products (download-only)")

        # Execute SAP queries for all products
        query_executor = QueryExecutor(request.user)
        results = query_executor.execute_search(plant_code, products, mode)

        logger.info(f"[LARGE QUERY DOWNLOAD] Got {len(results)} results, generating CSV")

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Product Number',
            'Description',
            'Brand',
            'Current Stock',
            'Unit',
            'Next Delivery Date',
            'Delivery Quantity',
            'UPC/EAN',
            'Weight (kg)',
            'Country of Origin',
            'Vendor',
            'Purchase Order',
            'Case Pack Size'
        ])

        # Write data rows
        for item in results:
            if 'error' not in item:  # Skip error entries
                writer.writerow([
                    item.get('MATNR', ''),
                    item.get('MAKTX', ''),
                    item.get('ZZBRAND', ''),
                    item.get('STOCK', '0'),
                    item.get('MEINS', ''),
                    item.get('EEIND', ''),
                    item.get('OMENG', '0'),
                    item.get('EAN11', ''),
                    item.get('BRGEW', ''),
                    item.get('HERKL', ''),
                    item.get('ZBRDES', ''),
                    item.get('EBELN', ''),
                    item.get('UMREZ', '')
                ])

        csv_content = output.getvalue()
        output.close()

        # Build description
        description_parts = []
        if brand:
            description_parts.append(f"{brand}")
        if category:
            description_parts.append(f"{category}")
        if material:
            description_parts.append(f"{material}")
        description = " - ".join(description_parts) if description_parts else "Bulk Query"

        # Get IP address for audit
        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Save to audit log with CSV file (NO EMAIL SENT)
        from .models import EmailAuditLog, ExportNotification
        from django.core.files.base import ContentFile

        filename = f'atp_report_{description}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        subject = f'ATP Download - {len(results)} Products - {description}'

        audit_log = EmailAuditLog.objects.create(
            user=request.user,
            recipient_email=request.user.email,  # Log user's email but don't send
            subject=subject + ' (Download Only - No Email Sent)',
            csv_filename=filename,
            csv_content=csv_content,
            product_count=len(results),
            session=session,
            status='success',
            is_to_personal_email=False,
            is_admin_override=False,
            ip_address=ip_address,
            user_agent=user_agent[:500]
        )

        # Save CSV file for download
        audit_log.csv_file.save(filename, ContentFile(csv_content.encode('utf-8')), save=True)

        # Create notification for user
        notification_message = f"Download ready: {len(results)} products from {description}"
        ExportNotification.objects.create(
            user=request.user,
            export_log=audit_log,
            message=notification_message,
            is_read=False
        )

        # Clear pending query
        conversation_manager.clear_pending_query()

        logger.info(f"[LARGE QUERY DOWNLOAD] Saved {len(results)} products (download-only), Audit Log: {audit_log.id}")

        return JsonResponse({
            'success': True,
            'message': f'Report with {len(results)} products ready for download',
            'response': f"✅ Your report with **{len(results)} products** is ready!\n\n🔔 Click the bell icon in the navbar to download the file.\n\n📧 No email was sent (download-only mode).",
            'audit_log_id': audit_log.id
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid session'
        }, status=404)
    except Exception as e:
        logger.error(f"Error processing large query download: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error processing request: {str(e)}'
        }, status=500)


# =============================================================================
# NOTIFICATION API ENDPOINTS
# =============================================================================

@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    Get unread export notifications for the current user
    Returns notifications in reverse chronological order
    """
    from .models import ExportNotification

    try:
        # Get unread notifications for this user
        notifications = ExportNotification.objects.filter(
            user=request.user,
            is_read=False
        ).select_related('export_log').order_by('-created_at')[:10]  # Limit to 10 most recent

        # Serialize notifications
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'message': notif.message,
                'created_at': notif.created_at.isoformat(),
                'export_id': notif.export_log.id,
                'product_count': notif.export_log.product_count,
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': notifications.count()
        })

    except Exception as e:
        logger.error(f"Error fetching notifications: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    """
    Mark a notification as read
    Accepts either a single notification_id or 'all' to mark all as read
    """
    from .models import ExportNotification

    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')

        if notification_id == 'all':
            # Mark all notifications as read for this user
            count = ExportNotification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)

            logger.info(f"[NOTIFICATIONS] Marked {count} notifications as read for user {request.user.username}")

            return JsonResponse({
                'success': True,
                'message': f'Marked {count} notifications as read'
            })
        else:
            # Mark specific notification as read
            notification = ExportNotification.objects.get(
                id=notification_id,
                user=request.user
            )
            notification.is_read = True
            notification.save()

            logger.info(f"[NOTIFICATIONS] Marked notification {notification_id} as read")

            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })

    except ExportNotification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def download_export(request, export_id):
    """
    Secure download endpoint for export files
    Only allows users to download their own exports
    Admins can download any export
    """
    from .models import EmailAuditLog
    from django.http import FileResponse, Http404
    import os

    try:
        # Get the export log
        export_log = EmailAuditLog.objects.get(id=export_id)

        # Security check: User can only download their own exports (unless admin)
        if not (request.user.is_staff or request.user.is_superuser):
            if export_log.user != request.user:
                logger.warning(
                    f"[SECURITY] User {request.user.username} attempted to download "
                    f"export {export_id} belonging to {export_log.user.username}"
                )
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to download this file'
                }, status=403)

        # Check if file exists
        if not export_log.csv_file:
            logger.error(f"[DOWNLOAD] No file attached to export {export_id}")
            return JsonResponse({
                'success': False,
                'error': 'Export file not found'
            }, status=404)

        # Check if file exists on disk
        if not os.path.exists(export_log.csv_file.path):
            logger.error(f"[DOWNLOAD] File missing on disk: {export_log.csv_file.path}")
            return JsonResponse({
                'success': False,
                'error': 'Export file has been deleted or is unavailable'
            }, status=404)

        # Log the download
        logger.info(
            f"[DOWNLOAD] User {request.user.username} downloading export {export_id} "
            f"({export_log.product_count} products)"
        )

        # Serve the file
        response = FileResponse(
            open(export_log.csv_file.path, 'rb'),
            as_attachment=True,
            filename=export_log.csv_filename
        )
        response['Content-Type'] = 'text/csv'
        return response

    except EmailAuditLog.DoesNotExist:
        logger.error(f"[DOWNLOAD] Export {export_id} not found")
        raise Http404("Export not found")
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error downloading export {export_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error downloading file'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def export_history(request):
    """
    Show user's export history with download links
    """
    from .models import EmailAuditLog

    try:
        # Get user's exports (most recent first)
        if request.user.is_staff or request.user.is_superuser:
            # Admins can see all exports
            exports = EmailAuditLog.objects.all().order_by('-sent_at')[:100]
        else:
            # Regular users see only their own
            exports = EmailAuditLog.objects.filter(
                user=request.user
            ).order_by('-sent_at')[:50]

        # Mark all notifications as read when viewing history page
        from .models import ExportNotification
        ExportNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        context = {
            'exports': exports,
            'user': request.user
        }

        return render(request, 'chatbot/export_history.html', context)

    except Exception as e:
        logger.error(f"[EXPORT HISTORY] Error: {e}", exc_info=True)
        return render(request, 'chatbot/export_history.html', {
            'error': 'Error loading export history',
            'exports': [],
            'user': request.user
        })