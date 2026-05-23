from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC

from src.evaluation import (
    compute_metrics,
    format_comparison_table,
    save_classification_report,
    save_confusion_matrix_plot,
)
from src.preprocessing import clean_text

RANDOM_STATE = 42
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "processed" / "intents_dataset.csv"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
CLASSIFIER_PATH = MODELS_DIR / "intent_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "vectorizer.pkl"
REPORT_PATH = OUTPUTS_DIR / "classification_report.txt"
CONFUSION_MATRIX_PATH = OUTPUTS_DIR / "confusion_matrix.png"


VECTORIZE_CONFIGS = [
    {
        "name": "bag_of_words",
        "vectorizer": CountVectorizer(lowercase=True, stop_words="english"),
    },
    {
        "name": "tfidf_unigram",
        "vectorizer": TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 1)),
    },
    {
        "name": "tfidf_unigram_bigram",
        "vectorizer": TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), min_df=2),
    },
]

CLASSIFIER_CONFIGS = [
    "dummy",
    "naive_bayes",
    "logistic_regression",
    "linear_svm",
    "random_forest",
]


def _build_classifier(name: str):
    if name == "dummy":
        return DummyClassifier(strategy="most_frequent")
    if name == "naive_bayes":
        from sklearn.naive_bayes import MultinomialNB

        return MultinomialNB()
    if name == "logistic_regression":
        return LogisticRegression(
            max_iter=2000,
            random_state=RANDOM_STATE,
            solver="lbfgs",
        )
    if name == "linear_svm":
        return LinearSVC(max_iter=10000, random_state=RANDOM_STATE)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)

    raise ValueError(f"Unknown classifier: {name}")


def load_dataset(dataset_path: Path) -> tuple[pd.Series, pd.Series]:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}. Please generate intents_dataset.csv first."
        )

    df = pd.read_csv(dataset_path)
    if "text" in df.columns:
        texts = df["text"].astype(str)
    elif "clean_text" in df.columns:
        texts = df["clean_text"].astype(str)
    else:
        raise ValueError("Dataset must contain either 'text' or 'clean_text' column.")

    labels = df["intent"].astype(str)
    texts = texts.map(clean_text)
    return texts, labels


def evaluate_combination(
    vectorizer_name: str,
    vectorizer,
    classifier_name: str,
    classifier,
    X_train: pd.Series,
    X_test: pd.Series,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:
    X_train_transformed = vectorizer.fit_transform(X_train)
    X_test_transformed = vectorizer.transform(X_test)

    classifier.fit(X_train_transformed, y_train)
    y_pred = classifier.predict(X_test_transformed)

    labels = sorted(y_test.unique())
    metrics = compute_metrics(list(y_test), list(y_pred), labels=labels)
    metrics.update(
        {
            "model_name": classifier_name,
            "vectorizer_name": vectorizer_name,
            "report": classification_report(y_test, y_pred, labels=labels, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels),
            "labels": labels,
            "classifier": classifier,
            "vectorizer": vectorizer,
        }
    )
    return metrics


def find_best_result(results: list[dict]) -> dict:
    return max(results, key=lambda item: item["f1_macro"])


def save_best_model_and_artifacts(best_result: dict) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_result["vectorizer"], VECTORIZER_PATH)
    print(f"[OK] Saved vectorizer to: {VECTORIZER_PATH}")
    joblib.dump(best_result["classifier"], CLASSIFIER_PATH)
    print(f"[OK] Saved classifier to: {CLASSIFIER_PATH}")

    model_header = (
        f"MODEL TRAINING REPORT\n"
        f"{'='*80}\n"
        f"\nSelected Model:\n"
        f"  Vectorizer: {best_result['vectorizer_name']}\n"
        f"  Classifier: {best_result['model_name']}\n"
        f"  F1 Score (macro): {best_result['f1_macro']:.4f}\n"
        f"  Accuracy: {best_result['accuracy']:.4f}\n"
        f"  Precision (macro): {best_result['precision_macro']:.4f}\n"
        f"  Recall (macro): {best_result['recall_macro']:.4f}\n"
        f"\n{'='*80}\n\n"
    )
    
    full_report = model_header + best_result["report"]
    save_classification_report(full_report, REPORT_PATH)
    save_confusion_matrix_plot(
        best_result["confusion_matrix"],
        best_result["labels"],
        CONFUSION_MATRIX_PATH,
    )


def train_and_save_best_model() -> dict:
    texts, labels = load_dataset(DATASET_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        stratify=labels,
        random_state=RANDOM_STATE,
    )

    results: list[dict] = []
    for vectorizer_config in VECTORIZE_CONFIGS:
        vectorizer_name = vectorizer_config["name"]
        vectorizer = vectorizer_config["vectorizer"]

        for classifier_name in CLASSIFIER_CONFIGS:
            classifier = _build_classifier(classifier_name)

            print(f"Training: {vectorizer_name} + {classifier_name}")
            result = evaluate_combination(
                vectorizer_name,
                vectorizer,
                classifier_name,
                classifier,
                X_train,
                X_test,
                y_train,
                y_test,
            )
            results.append(result)

    comparison_text = format_comparison_table(results)
    print("\nModel comparison:\n")
    print(comparison_text)

    best_result = find_best_result(results)
    print("\nBest model:")
    print(
        f"{best_result['vectorizer_name']} + {best_result['model_name']} "
        f"(F1 macro = {best_result['f1_macro']:.4f})"
    )

    save_best_model_and_artifacts(best_result)

    summary_lines = [
        "Final model selection:",
        f"- Best feature extractor: {best_result['vectorizer_name']}",
        f"- Best classifier: {best_result['model_name']}",
        f"- Final evaluation metric: F1 macro = {best_result['f1_macro']:.4f}",
        f"- Saved model: {CLASSIFIER_PATH}",
        f"- Saved vectorizer: {VECTORIZER_PATH}",
        f"- Saved report: {REPORT_PATH}",
        f"- Saved confusion matrix image: {CONFUSION_MATRIX_PATH}",
    ]
    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    return {
        "results": results,
        "best_result": best_result,
        "comparison_text": comparison_text,
        "summary_text": summary_text,
    }


if __name__ == "__main__":
    train_and_save_best_model()
