# Complete NLP Pipeline Architecture

## Overview

The chatbot implements a comprehensive 8-stage NLP pipeline that processes customer support messages and generates intelligent responses. All modules are integrated into `app.py` with clear logging at each stage.

---

## Complete Processing Pipeline

### User Message Flow

```
Chainlit UI
    ↓
@cl.on_message handler
    ↓
run_nlp_pipeline()
    ├─ STEP 1: Text Preprocessing (clean_text)
    ├─ STEP 2: Load Conversation Context
    ├─ STEP 3: Intent Classification
    ├─ STEP 4: Refine Intent with Context
    ├─ STEP 5: Sentiment Analysis
    ├─ STEP 6: Urgency Detection
    ├─ STEP 7: Response Generation
    └─ STEP 8: Package Results
    ↓
Display Response + NLP Metadata
    ↓
Save to SQLite
    ↓
Update Conversation History
```

---

## Module Integration

### 1. **Text Preprocessing** (`src/preprocessing.py`)
```python
from src.preprocessing import clean_text

cleaned = clean_text(user_message)
# Removes:
# - URLs (https://..., www....)
# - Mentions (@username)
# - Special characters
# - Extra whitespace
# Output: "my order never arrived" (normalized lowercase)
```

**Pipeline Step**: `clean_text()` is called first to normalize all text before NLP processing.

---

### 2. **Intent Classification** (`src/intent_classifier.py` + fallback `src/mock_classifier.py`)
```python
from src.intent_classifier import classify_intent

intent_result = classify_intent(cleaned_text)
# Returns: {
#   "intent": "delivery_issue",
#   "confidence": 0.87,
#   "matched_keywords": ["order", "arrived"]
# }
```

**Supported Intents**:
- `delivery_issue` - Package/shipping problems
- `refund_request` - Money back requests
- `payment_issue` - Billing/payment problems
- `account_problem` - Login/account access
- `technical_support` - App/website bugs
- `product_information` - Product questions
- `complaint` - Customer dissatisfaction
- `positive_feedback` - Praise/thanks
- `general_question` - Other inquiries

**Fallback Logic**: If trained models are unavailable, uses keyword-based mock classifier automatically.

---

### 3. **Sentiment Analysis** (`src/sentiment.py`)
```python
from src.sentiment import analyze_sentiment

sentiment_result = analyze_sentiment(cleaned_text)
# Returns: {
#   "sentiment": "negative",  # positive, negative, neutral
#   "score": -0.8  # -1.0 to 1.0
# }
```

**Lexicon-based Detection**:
- Counts positive terms ("thanks", "great", "amazing", etc.)
- Counts negative terms ("angry", "terrible", "broken", etc.)
- Calculates sentiment score and label

---

### 4. **Urgency Detection** (`src/urgency.py`)
```python
from src.urgency import detect_urgency

urgency_result = detect_urgency(cleaned_text)
# Returns: {
#   "urgency": "high",  # low, medium, high
#   "score": 0.78  # 0.0 to 1.0
# }
```

**Detection Rules**:
- **High urgency**: "urgent", "immediately", "asap", "unacceptable", "furious"
- **Medium urgency**: "paid", "charged", "late", "refund", "complaint"
- **Critical boost**: Emergency terms triple the urgency level

---

### 5. **Context Resolution** (`src/conversation_memory.py`)
```python
from src.conversation_memory import resolve_intent_with_context

# Uses conversation history to refine classification
intent_result = resolve_intent_with_context(
    intent_result,
    cleaned_text,
    conversation_history
)
```

**Context Features**:
- If confidence is low and previous message had a clear intent, inherit that intent
- Detects follow-up messages using contextual keywords ("also", "still", "update", etc.)
- Extracts order IDs and refund reasons from full conversation

---

### 6. **Response Generation** (`src/response_generator.py`)
```python
from src.response_generator import build_response

response = build_response(
    intent_result,
    sentiment_result,
    urgency_result,
    conversation_history=history,
    user_message=cleaned_text,
)
# Returns personalized support response
```

**Response Rules**:
- **Base response**: Intent-specific template
- **Context response**: If order ID detected, use specialized response
- **Sentiment prefix**: Add empathy if sentiment is negative
- **Urgency prefix**: Add urgency handling if needed
- **High urgency boost**: Escalate to high-priority support language

---

### 7. **Conversation Memory** (`src/conversation_memory.py`)
```python
from src.conversation_memory import save_interaction, load_recent_interactions

# Save current interaction
save_interaction(
    session_id=session_id,
    user_message=original_message,
    bot_response=response,
    intent_result=intent_result,
    sentiment_result=sentiment_result,
    urgency_result=urgency_result,
)

# Load previous context
history = load_recent_interactions(session_id, limit=5)
```

**Features**:
- SQLite database (`database/chatbot.db`)
- Stores all interactions with NLP metadata
- Enables multi-turn conversations with context
- Exports history to JSON for sidebar

---

## Complete Pipeline Function

### Main Entry Point in `app.py`

```python
async def run_nlp_pipeline(user_message: str, session_id: str) -> dict[str, Any]:
    """
    Execute the complete NLP chatbot workflow.
    
    Pipeline stages:
    1. TEXT PREPROCESSING: Clean and normalize input
    2. LOAD CONTEXT: Get recent conversation history
    3. INTENT CLASSIFICATION: Detect customer intent
    4. REFINE INTENT: Use conversation context
    5. SENTIMENT ANALYSIS: Detect emotional tone
    6. URGENCY DETECTION: Assess importance
    7. RESPONSE GENERATION: Build support response
    8. PACKAGE RESULTS: Return all NLP outputs
    """
    
    # Stage 1: Preprocessing
    cleaned_text = clean_text(user_message)
    logger.info(f"[PREPROCESSING] Original: {user_message[:60]}...")
    logger.info(f"[PREPROCESSING] Cleaned:  {cleaned_text[:60]}...")
    
    # Stage 2: Context
    conversation_history = load_recent_interactions(str(session_id))
    logger.info(f"[CONTEXT] Loaded {len(conversation_history)} interactions")
    
    # Stages 3-7: NLP Processing
    intent_result = classify_intent(cleaned_text)
    intent_result = resolve_intent_with_context(intent_result, cleaned_text, history)
    sentiment_result = analyze_sentiment(cleaned_text)
    urgency_result = detect_urgency(cleaned_text)
    bot_response = build_response(intent_result, sentiment_result, urgency_result, history, cleaned_text)
    
    # Log each stage
    logger.info(f"[INTENT] {intent_result['intent']} ({intent_result['confidence']})")
    logger.info(f"[SENTIMENT] {sentiment_result['sentiment']} ({sentiment_result['score']})")
    logger.info(f"[URGENCY] {urgency_result['urgency']} ({urgency_result['score']})")
    logger.info(f"[RESPONSE] {bot_response[:60]}...")
    
    # Stage 8: Return results
    return {
        "user_message": user_message,
        "cleaned_text": cleaned_text,
        "intent_result": intent_result,
        "sentiment_result": sentiment_result,
        "urgency_result": urgency_result,
        "bot_response": bot_response,
        "session_id": session_id,
    }
```

---

## Chat Event Handlers

### `@cl.on_chat_start`
**Initialization sequence:**
1. Initialize SQLite database
2. Seed demo conversations
3. Create new session
4. Send welcome message with instructions
5. Display recent conversations from history

### `@cl.on_message`
**Processing sequence:**
1. Extract user message
2. Check for special commands (`/history`, `/open`, `/new`)
3. Initialize/retrieve session ID
4. **Run complete NLP pipeline**
5. Build response with metadata
6. Send message to Chainlit UI
7. Save interaction to SQLite
8. Export history snapshot for sidebar

---

## Logging & Visibility

Every stage logs its progress to console:

```
[STARTUP] Initializing new chat session
[DB] Database initialized
[DEMO] Seeded 4 demo conversations
[SESSION] New session ID: 550e8400-e29b-41d4-a716-446655440000

[SESSION] ID: 550e8400-...
[SESSION] Message #1
[PREPROCESSING] Original: My order never arrived...
[PREPROCESSING] Cleaned:  my order never arrived...
[CONTEXT] Loaded 0 recent interactions
[INTENT] Detected: delivery_issue (87%)
[INTENT_REFINED] Final: delivery_issue
[SENTIMENT] Tone: negative (score: -0.8)
[URGENCY] Level: high (score: 0.78)
[RESPONSE] Generated: I have the order...
[PIPELINE] Completed successfully
[SAVE] Interaction saved to database
```

---

## Example Conversation Flow

### User Message
```
"I want a refund for order #12345, your product is terrible!"
```

### Pipeline Processing
```
1. PREPROCESSING:
   Original: "I want a refund for order #12345, your product is terrible!"
   Cleaned:  "i want a refund for order 12345 your product is terrible"

2. INTENT CLASSIFICATION:
   Intent: refund_request
   Confidence: 0.92
   Keywords: ["refund", "order"]

3. SENTIMENT ANALYSIS:
   Sentiment: negative
   Score: -0.9

4. URGENCY DETECTION:
   Urgency: medium
   Score: 0.55

5. RESPONSE GENERATION:
   - Prefix: "I am sorry you are dealing with this."
   - Base: "I can help start a refund request..."
   - Include: Order ID from context
   - Final: "I am sorry you are dealing with this. I have 
            the order/reference ID from the conversation. I can 
            continue the refund request; please add the refund 
            reason if you have not already."
```

### UI Output
```
Bot Response:
I am sorry you are dealing with this. I have the order/reference ID 
from the conversation. I can continue the refund request; please add 
the refund reason if you have not already.

---
**NLP metadata**

| Signal | Value |
| --- | --- |
| Intent | `refund_request` |
| Confidence | `92%` |
| Matched keywords | `refund, order` |
| Sentiment | `negative` (`-0.9`) |
| Urgency | `medium` (`0.55`) |
```

---

## Module Dependencies

```
app.py (Chainlit async handlers)
├── run_nlp_pipeline() (main orchestrator)
│   ├── clean_text() [preprocessing.py]
│   ├── load_recent_interactions() [conversation_memory.py]
│   ├── classify_intent() [intent_classifier.py]
│   │   └── classify_intent_mock() [mock_classifier.py] (fallback)
│   ├── resolve_intent_with_context() [conversation_memory.py]
│   ├── analyze_sentiment() [sentiment.py]
│   ├── detect_urgency() [urgency.py]
│   ├── build_response() [response_generator.py]
│   │   └── find_order_reference() [conversation_memory.py]
│   └── find_latest_specific_intent() [conversation_memory.py]
│
├── save_interaction() [conversation_memory.py]
├── export_history_snapshot() [conversation_memory.py]
└── config [config.py]
```

---

## Configuration (`src/config.py`)

```python
APP_NAME = "Social Support NLP Chatbot"
LOW_CONFIDENCE_THRESHOLD = 0.55  # Threshold for requesting clarification
SHOW_NLP_METADATA = True  # Display NLP signals in UI
INTENTS = (9 supported intent types)
AMBIGUOUS_MESSAGES = {"help", "hello", "hi", ...}  # Keywords needing clarification
```

---

## Running the Complete System

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Chainlit app
chainlit run app.py

# Or use the PowerShell script
.\run_app.ps1
```

## Database Schema

SQLite table stores all interactions:
```
conversations
├── session_id (TEXT)
├── created_at (TIMESTAMP)
├── user_message (TEXT)
├── bot_response (TEXT)
├── intent (TEXT)
├── intent_confidence (REAL)
├── sentiment (TEXT)
├── sentiment_score (REAL)
├── urgency (TEXT)
├── urgency_score (REAL)
└── matched_keywords (TEXT JSON)
```

---

## Beginner-Friendly Code Features

✅ **Clear comments** - Every function explains what it does  
✅ **Logging at each step** - Console output shows pipeline progress  
✅ **Modular design** - Each NLP module is independent  
✅ **Fallback logic** - Mock classifier if trained model unavailable  
✅ **Type hints** - All functions have type annotations  
✅ **Async support** - Chainlit-compatible async/await  
✅ **Error handling** - Graceful fallbacks and exception handling  
✅ **Documentation** - Docstrings for all functions  

---

## Next Steps for Enhancement

1. **Model Integration**: Replace mock classifier with trained ML model
2. **Advanced Preprocessing**: Add lemmatization, stopword removal
3. **Semantic Understanding**: Integrate embeddings for better context
4. **Multi-language**: Add language detection and translation
5. **Analytics Dashboard**: Display metrics on chatbot performance
6. **A/B Testing**: Compare response strategies
7. **User Feedback**: Collect user ratings for continuous improvement

---

**Architecture Document Created**: May 23, 2026  
**Status**: ✅ Complete & Tested  
**Ready for**: Production deployment with trained models
