from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
    }


def format_comparison_table(results: list[dict[str, float]]) -> str:
    headers = [
        "model",
        "vectorizer",
        "accuracy",
        "precision_macro",
        "recall_macro",
        "f1_macro",
    ]

    rows = [headers]
    for result in results:
        rows.append([
            result["model_name"],
            result["vectorizer_name"],
            f"{result['accuracy']:.4f}",
            f"{result['precision_macro']:.4f}",
            f"{result['recall_macro']:.4f}",
            f"{result['f1_macro']:.4f}",
        ])

    column_widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    lines = []
    header_line = " | ".join(row.ljust(width) for row, width in zip(rows[0], column_widths))
    lines.append(header_line)
    lines.append("-|-".join("-" * width for width in column_widths))

    for row in rows[1:]:
        lines.append(" | ".join(value.ljust(width) for value, width in zip(row, column_widths)))

    return "\n".join(lines)


def save_classification_report(report_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    print(f"[OK] Saved classification report to: {output_path}")


def save_confusion_matrix_plot(
    matrix: np.ndarray,
    labels: list[str],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 8))
    plt.imshow(matrix, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.colorbar()

    tick_marks = np.arange(len(labels))
    plt.xticks(tick_marks, labels, rotation=45, ha="right")
    plt.yticks(tick_marks, labels)

    thresh = matrix.max() / 2
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(
                j,
                i,
                int(matrix[i, j]),
                horizontalalignment="center",
                color="white" if matrix[i, j] > thresh else "black",
            )

    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved confusion matrix to: {output_path}")
