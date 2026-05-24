# Example Conversations

These examples were generated from the current hybrid pipeline:
mock/real intent classifier facade, sentiment analyzer, urgency detector,
SQLite-aware context logic, template fallback generator, and optional local
GPT rewriting through Ollama.

## Delivery issue

**User:** My package never arrived

**Bot:** I am sorry you are dealing with this. I can help with the delivery issue. Please send your order ID so I can check the package status and tracking details.

| Signal | Value |
| --- | --- |
| Intent | `delivery_issue` |
| Confidence | `0.94` |
| Sentiment | `negative` |
| Urgency | `medium` |

## Refund request

**User:** I want a refund for order REF9876

**Bot:** I have the order/reference ID from the conversation. I can continue the refund request; please add the refund reason if you have not already.

| Signal | Value |
| --- | --- |
| Intent | `refund_request` |
| Confidence | `0.64` |
| Sentiment | `neutral` |
| Urgency | `low` |

## Hybrid response source comparison

Same input, same NLP signals, different response source.

**User:** I want a refund, my order never arrived.

**Template fallback response:** I am sorry you are dealing with this. To start a refund request, I will need your order ID.

**Local GPT response (`llama3.2:3b`, expected style):** I am sorry your order has not arrived. I can help start a refund request, but I will need your order number first so the support team can review the case. Please send the order ID and I will guide you through the next step.

| Signal | Value |
| --- | --- |
| Intent | `refund_request` |
| Confidence | `0.87` |
| Sentiment | `negative` |
| Urgency | `medium` |
| Response source | `template_fallback` or `local_gpt: llama3.2:3b` |

## Payment issue urgent

**User:** This is unacceptable, I was double charged and need help immediately

**Bot:** I am sorry you are dealing with this. I will treat this as a high-priority support case in this demo flow. I can help with the payment issue. Please confirm the payment method and whether you were charged once or multiple times.

| Signal | Value |
| --- | --- |
| Intent | `payment_issue` |
| Confidence | `0.92` |
| Sentiment | `negative` |
| Urgency | `high` |

## Account problem

**User:** I cannot access my account

**Bot:** I am sorry you are dealing with this. I can help with the account problem. Please share the email or username linked to the account, but do not send your password.

| Signal | Value |
| --- | --- |
| Intent | `account_problem` |
| Confidence | `0.94` |
| Sentiment | `negative` |
| Urgency | `low` |

## Ambiguous low confidence

**User:** help

**Bot:** I am not fully sure how to classify this request yet. Could you add one more detail about the problem, such as delivery, refund, payment, account, technical support, or product information?

| Signal | Value |
| --- | --- |
| Intent | `general_question` |
| Confidence | `0.35` |
| Sentiment | `neutral` |
| Urgency | `low` |

## Negative urgent empathy

**User:** This is unacceptable, I paid and need help immediately

**Bot:** I am sorry you are dealing with this. I will treat this as a high-priority support case in this demo flow. I can help with the payment issue. Please confirm the payment method and whether you were charged once or multiple times.

| Signal | Value |
| --- | --- |
| Intent | `payment_issue` |
| Confidence | `0.60` |
| Sentiment | `negative` |
| Urgency | `high` |

## Context follow-up with previous order ID

**User:** My order ID ORD1234 never arrived

**Bot:** I am sorry you are dealing with this. I have the order/reference ID from the conversation. I can continue with the delivery investigation and check the package status in this demo flow.

| Signal | Value |
| --- | --- |
| Intent | `delivery_issue` |
| Confidence | `0.80` |
| Sentiment | `negative` |
| Urgency | `medium` |

**User:** yes

**Bot:** I have the order/reference ID from the conversation. I can continue with the delivery investigation and check the package status in this demo flow.

| Signal | Value |
| --- | --- |
| Intent | `delivery_issue` |
| Confidence | `0.55` |
| Sentiment | `neutral` |
| Urgency | `low` |
