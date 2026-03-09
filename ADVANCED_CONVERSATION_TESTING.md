# Advanced Conversational Intelligence Testing Guide

## Overview
This guide validates the production-ready conversational intelligence features implemented to make the chatbot match ChatGPT/Claude/Gemini quality.

## 🎯 Critical Production Requirements
- **ZERO context loss** in multi-turn conversations
- **100% action repeat recognition** for "do the same" patterns
- **Smart field-specific responses** (no information dumps)
- **Pronoun resolution** like human conversations
- **Response time < 3 seconds** for all queries

---

## Test Environment Setup

### 1. Access Chat Interface
- **URL**: http://localhost:5000/atp/chat/
- **Login**: admin / [REDACTED]
- **Verify Ollama**: Check logs show "Ollama configured: http://172.22.80.1:11434"

### 2. Monitor Backend Logs (Optional)
```bash
# Terminal 1: Watch application logs
docker-compose -f docker-compose-port5000-secure.yml logs -f web

# Terminal 2: Filter for intelligence features
docker-compose -f docker-compose-port5000-secure.yml logs web | grep -i "action\|track\|repeat\|follow-up"
```

---

## 🧪 Test Scenarios

### TEST 1: Follow-up Question Detection ⭐

**Purpose**: Verify bot remembers products without asking again (most critical production requirement)

#### Scenario 1.1: Basic Follow-up
```plaintext
👤 "What's the stock of product 46888?"
🤖 [Shows stock for 46888]

👤 "What's the UPC code?"
🤖 [Shows UPC for 46888 - SHOULD NOT ASK FOR PRODUCT NUMBER]
```

**✅ PASS Criteria**:
- No "I need product number(s)" error
- UPC shown for product 46888
- Response focused on UPC field only

**❌ FAIL Indicators**:
- "I need product number(s) to help you"
- Bot shows full product info instead of just UPC
- Bot asks which product you mean

#### Scenario 1.2: Pronoun Resolution
```plaintext
👤 "Check stock for 12345"
🤖 [Stock for 12345]

👤 "What's its delivery date?"
🤖 [Delivery for 12345 using "its" → 12345]

👤 "Show me the brand"
🤖 [Brand for 12345]
```

**✅ PASS Criteria**:
- "its" correctly resolves to product 12345
- No request for product clarification
- Each response targeted to specific field

**Backend Validation**:
```bash
# Check logs for follow-up detection
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "Follow-up detected"

# Expected:
# "Follow-up detected: Using current product 12345"
```

---

### TEST 2: Action Repeat Intelligence ⭐⭐⭐

**Purpose**: Verify "do the same with X" patterns work (user's #1 complaint)

#### Scenario 2.1: Classic "Do the same"
```plaintext
👤 "What's the UPC of product 46961?"
🤖 [UPC/EAN: 0123456789012]

👤 "Do the same with 46888"
🤖 [UPC/EAN for 46888 - SAME ACTION, DIFFERENT PRODUCT]
```

**✅ PASS Criteria**:
- Intent inherited: product_info
- Field inherited: upc
- Product changed to 46888
- Response format matches first query

**❌ FAIL Indicators**:
- "I'm not quite sure what you're looking for"
- Shows full product info instead of just UPC
- Asks for clarification

#### Scenario 2.2: All Repeat Phrase Patterns
Test each phrase individually:

```plaintext
👤 "Show me the brand for 11111"
🤖 [Brand for 11111]

👤 "Same thing for 22222"      → Brand for 22222 ✅
👤 "Also check 33333"           → Brand for 33333 ✅
👤 "How about 44444?"          → Brand for 44444 ✅
👤 "What about 55555?"         → Brand for 55555 ✅
👤 "Check that for 66666"      → Brand for 66666 ✅
👤 "Repeat for 77777"          → Brand for 77777 ✅
```

**Backend Validation**:
```bash
# Check for action repeat detection
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "Action repeat detected"

# Expected:
# "Action repeat detected! Using last intent: product_info"
# "Applying last field request: brand"
```

---

### TEST 3: Field-Specific Response Generation

**Purpose**: Verify targeted responses (no information dumps)

#### Scenario 3.1: Each Field Type
```plaintext
👤 "What's the UPC for 46888?"
🤖 [ONLY UPC/EAN shown, NOT full product info] ✅

👤 "Show brand for 12345"
🤖 [ONLY Brand shown] ✅

👤 "What's the origin of 67890?"
🤖 [ONLY Origin/Country shown] ✅

👤 "How heavy is 11111?"
🤖 [ONLY Weight shown] ✅

👤 "What's the case pack for 22222?"
🤖 [ONLY Case Pack units shown] ✅
```

**✅ PASS Criteria**:
- Each response shows ONLY requested field
- Response includes product number and description
- Format: "**[PRODUCT]** - [Description]\n• [Field]: [Value]"

**Field Keyword Detection**:
- **UPC**: upc, ean, barcode, code
- **Brand**: brand, manufacturer, make
- **Origin**: origin, country, from where, made in
- **Weight**: weight, how heavy, kg
- **Case Pack**: case pack, pack, units per case
- **Vendor SKU**: vendor, sku, supplier code
- **Delivery**: delivery, eta, arrive, coming
- **Stock**: stock, inventory, quantity, how many

---

### TEST 4: Context Switching

**Purpose**: Verify context updates correctly when switching products

#### Scenario 4.1: Single → Multi → Single
```plaintext
👤 "Check stock for 11111"
🤖 [Stock for 11111]
   Context: current_product = 11111

👤 "What's the UPC?"
🤖 [UPC for 11111]

👤 "Now check stock for 22222, 33333, 44444"
🤖 [Stock for all 3 products]
   Context: last_product_numbers = [22222, 33333, 44444]

👤 "What are their brands?"
🤖 [Brands for 22222, 33333, 44444 - NOT 11111] ✅

👤 "Just show me 22222"
🤖 [Info for 22222]
   Context: current_product = 22222

👤 "What's its origin?"
🤖 [Origin for 22222 only] ✅
```

**✅ PASS Criteria**:
- Context switches cleanly between single/multi products
- Previous products not mixed with new queries
- Plural pronouns ("their", "these") handled for multi-product

---

### TEST 5: Intent Inheritance

**Purpose**: Verify different intents tracked separately

#### Scenario 5.1: Cross-Intent Action Repeat
```plaintext
👤 "What's the delivery date for 11111?"
🤖 [Delivery info]
   Tracked: intent=delivery_query, field=delivery

👤 "Do the same with 22222"
🤖 [Delivery for 22222] ✅

👤 "What's the stock of 33333?"
🤖 [Stock info]
   Tracked: intent=stock_query, field=stock

👤 "Same for 44444"
🤖 [Stock for 44444] ✅
   (Should inherit stock_query, NOT delivery_query)
```

**✅ PASS Criteria**:
- Action tracking updates with each new intent
- "Same for 44444" shows STOCK not delivery
- Intent inheritance follows last action

---

### TEST 6: Error Handling

**Purpose**: Graceful degradation for edge cases

#### Scenario 6.1: Invalid Product
```plaintext
👤 "Check stock for 99999999"
🤖 "I couldn't find any products matching your query"

👤 "What's the UPC?"
🤖 [Should ask for valid product, NOT use 99999999]
```

#### Scenario 6.2: Ambiguous Follow-up
```plaintext
👤 "Check stock for 11111, 22222"
🤖 [Stock for both]

👤 "What about the UPC?"
🤖 [UPC for BOTH 11111 and 22222] ✅
```

---

## 📊 Backend Context Verification

### Check Session Context
```bash
# Enter Django shell in container
docker exec -it atp_web python manage.py shell

# Get latest active session
from chatbot.models import ChatSession
session = ChatSession.objects.filter(is_active=True).order_by('-updated_at').first()

# View context
import json
print(json.dumps(session.get_context(), indent=2))
```

**Expected Context Structure**:
```json
{
  "selected_plant": "9995",
  "current_product": "46888",
  "last_product_numbers": ["46888"],
  "last_intent": "product_info",
  "last_field_requested": "upc",
  "last_action_description": "Queried product_info for products ['46888']",
  "last_action_time": "2025-10-31T...",
  "last_results": [...],
  "last_query_time": "2025-10-31T...",
  "last_search_type": "arc_sku"
}
```

### Verify Action Tracking in Logs
```bash
# Filter for intelligence features
docker-compose -f docker-compose-port5000-secure.yml logs web | grep -E "Tracked action|Action repeat|Follow-up detected|Applying last field"
```

**Expected Log Entries**:
```
Tracked action: product_info, field: upc
Action repeat detected! Using last intent: product_info
Applying last field request: upc
Follow-up detected: Using current product 46888
Set current products: ['46888']
```

---

## 🎯 Production Readiness Checklist

### Critical Features (Must be 100%)
- [ ] Follow-up questions work without product number errors
- [ ] All "do the same" phrase patterns recognized:
  - [ ] "do the same", "same thing", "same for", "same with"
  - [ ] "also check", "also show", "also get"
  - [ ] "how about", "what about"
  - [ ] "check that for", "repeat for"
- [ ] Field-specific responses show ONLY requested field
- [ ] Context persists across 10+ messages
- [ ] Pronoun resolution works ("it", "its", "this", "that")
- [ ] Multi-product context switches correctly
- [ ] Intent inheritance accurate for action repeats

### Performance
- [ ] First message: < 3 seconds
- [ ] Follow-up messages: < 2 seconds
- [ ] No database errors (emoji handling working)
- [ ] No JSON parsing errors (markdown stripping working)
- [ ] No CSRF token errors

### Intelligence Quality
- [ ] Matches ChatGPT/Claude quality for context persistence
- [ ] No "I need product number(s)" errors on valid follow-ups
- [ ] Natural conversation flow (not robotic)
- [ ] Handles ambiguity gracefully
- [ ] Error messages are helpful (not cryptic)

---

## 🚨 Common Issues & Fixes

### Issue: "I need product number(s)" on Follow-up

**Symptom**: Bot asks for product after you just provided one

**Debug Steps**:
```bash
# Check if follow-up detected
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "Follow-up detected"

# Check session context has current_product
docker exec -it atp_web python manage.py shell
>>> from chatbot.models import ChatSession
>>> s = ChatSession.objects.filter(is_active=True).last()
>>> print(s.get_context().get('current_product'))
```

**Root Cause**: Entity extractor not detecting follow-up question
**Fix**: Check `entity_extractor.py:_add_context_entities()` line 214-249

---

### Issue: Action Repeat Not Working

**Symptom**: "Do the same with X" asks for clarification

**Debug Steps**:
```bash
# Check if action repeat detected
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "Action repeat detected"

# Check last_intent in context
docker exec -it atp_web python manage.py shell
>>> from chatbot.models import ChatSession
>>> s = ChatSession.objects.filter(is_active=True).last()
>>> print(s.get_context().get('last_intent'))
```

**Root Cause**:
1. Repeat phrase not in detection list
2. last_intent not stored in context

**Fix**: Check `conversation_manager.py:detect_action_repeat()` line 515-535

---

### Issue: Full Product Info Instead of Field-Specific

**Symptom**: Shows all fields instead of just UPC

**Debug Steps**:
```bash
# Check if field_requested detected
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "field_requested"
```

**Root Cause**: Field keywords not matching
**Fix**: Check `views.py:_detect_field_request()` line 24-63

---

## 📈 Performance Benchmarks

### Response Times (Target)
| Scenario | Target | Acceptable | Needs Work |
|----------|--------|------------|------------|
| First message | < 2s | < 3s | > 3s |
| Follow-up (cached context) | < 1.5s | < 2s | > 2s |
| Action repeat | < 1.5s | < 2s | > 2s |
| Multi-product query | < 3s | < 4s | > 4s |

### Accuracy Targets
- Intent classification: > 90%
- Entity extraction: > 95%
- Follow-up detection: 100%
- Action repeat detection: 100%
- Field detection: > 95%

---

## ✅ Success Criteria Summary

The chatbot is **PRODUCTION READY** when:

1. **Zero Context Loss** ✅
   - 20+ message conversations maintain context
   - No "I need product number" errors on valid follow-ups

2. **Action Repeat Intelligence** ✅
   - All 10+ phrase patterns work 100% of time
   - Intent and field correctly inherited

3. **Smart Responses** ✅
   - Field-specific responses (not full dumps)
   - Natural conversation flow
   - Appropriate error handling

4. **Performance** ✅
   - Response time < 3 seconds
   - No crashes or 500 errors
   - Handles 100+ requests without issues

5. **User Experience** ✅
   - Feels like ChatGPT/Claude/Gemini
   - Users don't notice it's AI
   - Natural back-and-forth dialogue

---

**Document Version**: 1.0
**Last Updated**: November 1, 2025
**Test Coverage**: 25+ conversational scenarios
**Critical Features**: Follow-up detection, Action repeat, Field-specific responses
**Status**: Hybrid rule-based + LLM intelligence system
