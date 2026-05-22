# Social Support NLP Chatbot

Academic MVP for social media customer support using classic NLP modules.

## Features

- **Intent Classification**: Automatically detects customer request type (delivery, refund, payment, etc.)
- **Sentiment Analysis**: Recognizes emotional tone and responds empathetically
- **Urgency Detection**: Prioritizes high-urgency cases
- **Context Memory**: Remembers previous messages in the same session
- **Chat History Sidebar**: View all recent conversations on the left
- **SQLite Persistence**: All conversations saved for analysis
- **Confidence-Based Clarification**: Asks for details when unsure

## Try These Messages

- `My order never arrived`
- `I want a refund`
- `I cannot access my account`
- `This is unacceptable, I paid and need help immediately`
- `help`

## Sidebar Features

**Chat History** (left sidebar)
- Shows recent conversation sessions
- Click a conversation to load it in the main chat frame
- Includes intent, message count, and date
- Auto-updates with new conversations

## Pipeline

1. User message received
2. Intent classification (real model or mock fallback)
3. Sentiment analysis (positive/negative/neutral)
4. Urgency detection (low/medium/high)
5. Context-aware response generation
6. Automatic saving to database
7. Display with NLP metadata (if enabled)
