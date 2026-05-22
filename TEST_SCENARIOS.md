# 🧪 Practical Test Scenarios

Use these real-world scenarios to verify each feature works correctly.

---

## Scenario 1: Delivery Problem with Context

**Goal:** Test intent classification + context usage + finding order reference

**Messages to send IN ORDER:**
```
1. "My package didn't arrive yet"
2. "The order number is ORD-2024-5678"
3. "It was supposed to be here 3 days ago"
4. "Can I get a status update?"
```

**Expected behavior:**
- **Message 1:** Intent = delivery_issue, confidence ~75%
- **Message 2:** Bot extracts ORD-2024-5678 and acknowledges it
- **Message 3:** Bot remembers delivery_issue context, confidence improves
- **Message 4:** "yes" → Bot uses context, responds about delivery investigation

**NLP metadata should show:**
- Matched keywords: "order ORD-2024-5678" extracted
- Sentiment: neutral (factual) or negative (if user seems frustrated)
- Urgency: medium (time-sensitive)

✅ **PASS if:** Bot response includes "I have the order/reference ID from the conversation"

---

## Scenario 2: Angry Customer with Urgency

**Goal:** Test empathetic response + urgency detection

**Messages:**
```
1. "I'm absolutely FURIOUS about this situation!"
2. "I NEED help RIGHT NOW!"
3. "This is completely unacceptable!"
```

**Expected behavior:**
- Bot response includes BOTH:
  - "I am sorry you are dealing with this."
  - "I will treat this as a high-priority support case in this demo flow."

**NLP metadata:**
- Sentiment: negative (definitely!)
- Urgency: high (definitely!)
- Confidence: varies by message

✅ **PASS if:** All three messages get empathetic + urgency prefix in responses

---

## Scenario 3: Ambiguous Follow-ups (Low Confidence)

**Goal:** Test context-based resolution of ambiguous short messages

**Messages:**
```
1. "I have an issue with my payment"
2. "Still doesn't work"
3. "Can you help?"
4. "yes"
```

**Expected behavior:**
- **Message 1:** Intent = payment_issue, confidence ~80%
- **Message 2:** Low confidence ("Still doesn't work"), BUT bot remembers payment_issue → uses context
- **Message 3:** Low confidence response asks for clarification OR uses context
- **Message 4:** Just "yes" → Bot asks for clarification if no prior context established

**NLP metadata - Message 2:**
- Matched keywords: `context:payment_issue` (shows it remembered!)
- Confidence: might increase due to context

✅ **PASS if:** Bot doesn't ask "what's that about?" but continues payment_issue thread

---

## Scenario 4: Refund Request with Order Reference

**Goal:** Test template response with order reference detection

**Messages:**
```
1. "I want a refund"
2. "Order ID: REF-12345"
3. "Reason: Product doesn't match description"
```

**Expected behavior:**
- **Message 1:** Intent = refund_request, asks for order ID
- **Message 2:** Bot identifies order reference REF-12345
- **Message 3:** Bot responds with context-aware refund template

**NLP metadata:**
- Intent: refund_request (consistent all 3 messages)
- Matched keywords: REF-12345 found
- Sentiment: neutral or slightly negative

✅ **PASS if:** Response mentions the order/reference ID

---

## Scenario 5: Account Access Problem

**Goal:** Test technical_support/account_problem intent

**Messages:**
```
1. "I can't access my account"
2. "It says invalid password"
3. "But I definitely typed it correctly"
4. "Can you help me reset it?"
```

**Expected behavior:**
- **Message 1:** Intent = account_problem, confidence ~85%
- **Message 2:** Bot asks for email/username (but not password!)
- **Message 3:** Context continues account thread
- **Message 4:** Context treated as part of account_problem

**NLP metadata:**
- Consistent intent: account_problem
- Sentiment: neutral (factual problem)
- Urgency: medium (account access is important)

✅ **PASS if:** Bot asks for email but explicitly warns NOT to share password

---

## Scenario 6: Product Information

**Goal:** Test product_information intent

**Messages:**
```
1. "Tell me about your products"
2. "What are the specifications?"
3. "How much does it weigh?"
```

**Expected behavior:**
- Intent = product_information throughout
- Bot asks which product specifically
- Asks what detail needed

**NLP metadata:**
- Intent: product_information
- Confidence: ~80%
- Sentiment: neutral
- Urgency: low

✅ **PASS if:** Bot asks "which product" rather than routing to general queue

---

## Scenario 7: Positive Feedback

**Goal:** Test positive_feedback intent

**Messages:**
```
1. "Great service, thank you so much!"
2. "Really happy with my purchase"
3. "Keep up the good work!"
```

**Expected behavior:**
- Intent = positive_feedback
- Bot thanks customer
- Records feedback

**NLP metadata:**
- Sentiment: positive (definitely!)
- Confidence: ~90%+
- Urgency: low

✅ **PASS if:** Sentiment shows "positive" in metadata

---

## Scenario 8: Chat History Persistence

**Goal:** Test that conversations survive browser restart

**Steps:**
```
1. Send: "I have a delivery problem"
2. Send: "Order ORD-999"
3. CLOSE BROWSER TAB (or use Ctrl+W)
4. Refresh page or open new tab to http://localhost:8000
5. Check the left sidebar: do you see "Conversations"?
6. Click the saved session and confirm it lists the delivery_issue transcript.
```

✅ **PASS if:** 
- Previous conversation appears in the left SQLite history sidebar
- Shows: "Session with 2 messages - Intents: delivery_issue - Last: [today's date]"

---

## Scenario 9: Multiple Sessions

**Goal:** Test that multiple sessions accumulate correctly

**Session 1:**
```
"Refund request"
"Order ABC-123"
```

**Close browser, start new session**

**Session 2:**
```
"Payment issue"
"Card was declined"
```

**Close browser, start new session**

**Session 3:**
```
"Can't access my account"
```

**Now start new session - check the left Conversations sidebar**

✅ **PASS if:**
- See 3 sessions listed
- Each shows different intents: refund_request, payment_issue, account_problem
- Most recent (Session 3) is first

---

## Scenario 10: Database Inspection

**Goal:** Verify data integrity in SQLite

**Run these SQL queries:**

```sql
-- Total saved conversations
SELECT COUNT(*) FROM conversations;

-- All sessions with message counts
SELECT session_id, COUNT(*) as msg_count 
FROM conversations 
GROUP BY session_id;

-- Specific session details
SELECT user_message, intent, confidence, sentiment, urgency 
FROM conversations 
WHERE session_id LIKE '%your-session-id%'
ORDER BY timestamp;

-- Sentiment distribution
SELECT sentiment, COUNT(*) 
FROM conversations 
GROUP BY sentiment;

-- Intent distribution  
SELECT intent, COUNT(*) 
FROM conversations 
GROUP BY intent;
```

✅ **PASS if:**
- All messages from your test scenarios are present
- Confidence scores are between 0.0 and 1.0
- Sentiment is one of: positive, negative, neutral
- Urgency is one of: low, medium, high
- Timestamps are in ISO format

---

## Quick Verification Checklist

After running the scenarios above:

- [ ] Chat history displays on new session
- [ ] Context is used for follow-up messages
- [ ] Low confidence messages ask for clarification
- [ ] Negative sentiment triggers empathetic prefix
- [ ] High urgency triggers priority prefix
- [ ] Order references are detected and stored
- [ ] Multiple sessions accumulate correctly
- [ ] Database contains all messages
- [ ] NLP metadata displays correctly
- [ ] No error messages in console

---

## If Something Fails

**Step 1:** Check the NLP metadata box under the response
- Does the data look reasonable?
- Are confidence scores in 0-1 range?
- Are intent/sentiment/urgency values valid?

**Step 2:** Query the database directly
```powershell
sqlite3 database/chatbot.db
SELECT * FROM conversations WHERE timestamp > datetime('now', '-1 hour');
.exit
```

**Step 3:** Check for errors
```powershell
# Look at terminal output where chainlit is running
# Any Python exceptions?
```

**Step 4:** Reset and retry
```powershell
Remove-Item database/chatbot.db -Force
# Restart: chainlit run app.py
```

---

## Success Criteria

✅ All 10 scenarios pass = Your chatbot is production-ready!

You can now:
- Demonstrate to stakeholders
- Hand off to colleagues for model integration  
- Deploy to production (with proper scaling)
