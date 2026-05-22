Ce ar trebui să facă fiecare din echipă

Eu aș împărți proiectul în 3 bucăți clare.

1. Colegul/colega 1 — Data + preprocessing + EDA

Persoana asta se ocupă de partea de date.

Responsabilități:

- găsește/creează datasetul
- definește clasele de intent
- curăță datele
- face preprocessing pe text de social media
- face grafice și analiză exploratorie

Clase posibile de intent:

complaint
refund_request
delivery_issue
technical_support
product_information
payment_issue
account_problem
positive_feedback
general_question
escalation_request

Preprocessing specific social media:

- lowercasing
- eliminare URL-uri
- eliminare mentions: @brand, @user
- normalizare hashtag-uri
- eliminare emoji sau transformare emoji în text
- eliminare punctuație inutilă
- tokenizare
- stopwords removal
- lemmatizare/stemming, opțional

Output-ul lor:

data/raw/
data/processed/
notebooks/eda.ipynb
plots cu distribuția intențiilor
exemple înainte/după preprocessing
2. Colegul/colega 2 — Intent classification + evaluare

Persoana asta face modelul clasic de NLP.

Modele de comparat:

Baseline: DummyClassifier
Naive Bayes
Logistic Regression
Linear SVM
Random Forest, opțional

Feature extraction:

Bag of Words
TF-IDF unigrams
TF-IDF unigrams + bigrams

Metrici:

accuracy
precision
recall
F1-score
confusion matrix
classification report

Aici profesorul vede clar partea de NLP.

Output-ul lor:

models/intent_classifier.pkl
models/vectorizer.pkl
notebooks/model_training.ipynb
outputs/classification_report.txt
outputs/confusion_matrix.png

Foarte important: să aveți comparație între modele. Chiar dacă Logistic Regression câștigă, arată bine să spui:

Am testat mai multe modele clasice de NLP, iar cel mai bun rezultat a fost obținut cu TF-IDF + Linear SVM / Logistic Regression.

3. Tu — Chatbot engine + Chainlit + istoric conversațional

Asta e partea cea mai vizibilă și cea mai „wow”. Da, aici aș zice să faci tu.

Tu faci aplicația efectivă:

- interfață de chat în Chainlit
- încărcarea modelului de intent classification
- salvarea conversațiilor în SQLite
- folosirea contextului conversațional
- generarea răspunsului
- afișarea intenției detectate, scorului de încredere, sentimentului

Flow-ul tău:

User: I want a refund, my order never arrived.
↓
Intent: refund_request / delivery_issue
Confidence: 0.87
Sentiment: negative
Urgency: medium/high
↓
Bot: I'm sorry to hear that your order has not arrived. I can help you start a refund or delivery investigation. Could you please provide your order number?

Aici nu ai nevoie de GPT API. Poți face un Response Generator bazat pe reguli/template-uri.