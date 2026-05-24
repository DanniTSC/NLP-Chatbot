# Social Support NLP Chatbot

Aplicatie Chainlit pentru customer support pe mesaje de social media. Proiectul detecteaza intentul, sentimentul si urgenta, poate rescrie raspunsurile cu un model GPT local prin Ollama si salveaza conversatiile in SQLite.

## Rulare

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
$env:DEBUG = "false"
chainlit run app.py
```

Sau direct:

```powershell
.\run_app.ps1
```

## GPT local optional prin Ollama

Aplicatia nu foloseste OpenAI API si nu are nevoie de API key. Pentru cerinta de integrare a unui model de tip GPT, pipeline-ul poate folosi un model local Ollama doar pentru redactarea raspunsului final. Clasificarea intentului, sentimentul, urgenta si memoria conversationala raman controlate de codul existent.

Implicit, GPT-ul local este dezactivat ca aplicatia sa ruleze rapid si fara Ollama. Activeaza-l doar cand ai Ollama instalat si modelul descarcat.

Instalare/rulare model local:

```powershell
ollama pull llama3.2:3b
$env:USE_LOCAL_GPT = "true"
$env:OLLAMA_MODEL = "llama3.2:3b"
chainlit run app.py
```

Daca Ollama nu este instalat, nu ruleaza sau modelul lipseste, aplicatia revine automat la raspunsurile pe reguli/template-uri.

Configurari utile:

```powershell
$env:USE_LOCAL_GPT = "false"        # forteaza fallback-ul pe template-uri
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_TIMEOUT_SECONDS = "20"
```

Exemple de mesaje:

- `My package never arrived`
- `I want a refund`
- `This is unacceptable, I need help immediately`
- `help`

## Ce am implementat eu

- SQLite memory in `src/conversation_memory.py`: salveaza conversatiile, incarca istoricul anterior si exporta istoricul pentru sidebar.
- `response_generator` in `src/response_generator.py`: reguli contextuale pentru clarificare, empatie la mesaje urgente/negative si raspunsuri pe intent.
- `llm_response_generator` in `src/llm_response_generator.py`: generator optional cu Ollama pentru raspunsuri mai naturale, cu fallback automat pe template-uri.
- Integrarea pipeline-ului in `app.py`: intent, sentiment, urgency, raspuns, salvare in SQLite si incarcare conversatii vechi.
- Sidebar cu istoricul conversatiilor in `public/sidebar.js` si `public/stylesheet.css`: conversatiile se deschid in chat-ul principal.
- Demo conversations in `outputs/example_conversations.md` si seed demo in `src/demo_data.py`.
- Fallback mock pentru intent classification in `src/mock_classifier.py`, folosit automat daca modelul real nu exista.
- Punct de integrare pentru modelul colegilor in `src/intent_classifier.py`.

## Status

- [x] Pot rula aplicatia cu `chainlit run app.py`
- [x] Pot trimite un mesaj si primesc raspuns
- [x] Se detecteaza intentul
- [x] Se calculeaza sentimentul
- [x] Se calculeaza urgency
- [x] Am README cu instructiuni
- [x] Am fallback mock daca modelul real nu exista
- [x] Pot integra usor modelul colegilor
- [x] Conversatia se salveaza in SQLite
- [x] Botul foloseste contextul anterior
- [x] Daca confidence e mic, cere clarificare
- [x] Daca mesajul e urgent/negativ, raspunde empatic
- [x] Poate folosi optional un model GPT local prin Ollama pentru redactarea raspunsului
- [x] Daca GPT-ul local nu este disponibil, revine automat la template-uri
- [x] Am demo conversations salvate


```text
models/vectorizer.pkl
models/intent_classifier.pkl
```

- [ ] Ruleaza din nou aplicatia si demo-urile dupa integrarea modelului real, ca sa verifici ca raspunsurile raman corecte.

## Ce mai e de facut

### 1. Colegul/colega 1 - Data + preprocessing + EDA

Responsabilitati:

- gaseste sau creeaza datasetul
- defineste clasele de intent
- curata datele
- face preprocessing pe text de social media
- face grafice si analiza exploratorie

Clase posibile de intent:

- complaint
- refund_request
- delivery_issue
- technical_support
- product_information
- payment_issue
- account_problem
- positive_feedback
- general_question
- escalation_request

Preprocessing specific social media:

- lowercasing
- eliminare URL-uri
- eliminare mentions: @brand, @user
- normalizare hashtag-uri
- eliminare emoji sau transformare emoji in text
- eliminare punctuatie inutila
- tokenizare
- stopwords removal
- lemmatizare sau stemming, optional

Output asteptat:

- data/raw/
- data/processed/
- notebooks/eda.ipynb
- plots cu distributia intentiilor
- exemple inainte/dupa preprocessing

### 2. Colegul/colega 2 - Intent classification + evaluare

Responsabilitati:

- antreneaza modelul clasic de NLP
- compara mai multe modele
- salveaza cel mai bun model si vectorizerul
- genereaza evaluarea finala

Modele de comparat:

- DummyClassifier ca baseline
- Naive Bayes
- Logistic Regression
- Linear SVM
- Random Forest, optional

Feature extraction:

- Bag of Words
- TF-IDF unigrams
- TF-IDF unigrams + bigrams

Metrici:

- accuracy
- precision
- recall
- F1-score
- confusion matrix
- classification report

Output asteptat:

- models/intent_classifier.pkl
- models/vectorizer.pkl
- notebooks/model_training.ipynb
- outputs/classification_report.txt
- outputs/confusion_matrix.png

Observatie importanta:

- arata clar comparatia intre modele
- chiar daca Logistic Regression castiga, mentioneaza explicit rezultatul final, de exemplu: TF-IDF + Linear SVM sau TF-IDF + Logistic Regression


### Flow-ul aplicatiei:

User: I want a refund, my order never arrived.

Intent: refund_request / delivery_issue

Confidence: 0.87

Sentiment: negative

Urgency: medium/high

Bot: I'm sorry to hear that your order has not arrived. I can help you start a refund or delivery investigation. Could you please provide your order number?

Nu este nevoie de GPT API. Pentru MVP, response generator-ul pe reguli ramane fallback-ul sigur; pentru cerinta de tip GPT, Ollama poate genera local textul final folosind semnalele NLP deja calculate.

## MVP realist

Pentru o nota buna, MVP-ul ar trebui sa includa:

1. Dataset cu mesaje de social media
2. Minim 6-8 intentii
3. Preprocessing explicat
4. 3 modele comparate
5. Cel mai bun model salvat
6. Chatbot Chainlit functional
7. Response generator pe intentii
8. Istoric conversational in SQLite
9. Evaluare cu metrici
10. Exemple de conversatii reale

## Flux recomandat

1. Aveti un CSV cu mesaje si intentii.
2. Curatati textul.
3. Transformati textul in numere cu TF-IDF.
4. Antrenati Logistic Regression, Naive Bayes si SVM.
5. Evaluati cu accuracy, precision, recall si F1.
6. Salvati modelul ales.
7. Chatbotul foloseste modelul salvat.

```text
text user
	↓
preprocessing
	↓
TF-IDF vectorizer
	↓
model ML
	↓
intent + confidence
	↓
template response plan
	↓
local GPT rewrite optional sau template fallback
```

## Structura recomandata a proiectului

```text
social-media-chatbot/
|
├── app.py
├── requirements.txt
├── README.md
|
├── data/
│   ├── raw/
│   ├── processed/
│   └── intents_dataset.csv
|
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   └── 03_model_training.ipynb
|
├── src/
│   ├── config.py
│   ├── preprocessing.py
│   ├── train_model.py
│   ├── predict_intent.py
│   ├── sentiment.py
│   ├── response_generator.py
│   ├── conversation_memory.py
│   └── evaluation.py
|
├── models/
│   ├── vectorizer.pkl
│   └── intent_classifier.pkl
|
├── outputs/
│   ├── confusion_matrix.png
│   ├── classification_report.txt
│   └── example_conversations.md
|
└── database/
		└── chat_history.db
```
