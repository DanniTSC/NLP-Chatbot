from src.intent_classifier import classify_intent

test_messages = [
    'I want a refund',
    'Can you help me with technical issues',
    'I am very angry with your service',
    'How do I reset my password',
    'My package was damaged'
]

print("Testing Intent Classification with Trained Model\n")
print("=" * 70)

for msg in test_messages:
    result = classify_intent(msg)
    print(f"Message: {msg}")
    print(f"  Intent: {result['intent']}")
    print(f"  Confidence: {result['confidence']}")
    print()
