from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "customer_support_clean.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "intents_dataset.csv"


def build_intents_dataset(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_columns = {"clean_text", "intent"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"Input file is missing required columns: {', '.join(sorted(missing))}"
        )

    intents_df = df[["clean_text", "intent"]].copy()
    intents_df = intents_df.rename(columns={"clean_text": "text"})
    intents_df = intents_df.dropna(subset=["text", "intent"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    intents_df.to_csv(output_path, index=False)

    print(f"Created intents dataset: {output_path}")
    print(f"Rows: {len(intents_df)}")
    print("Intent counts:")
    print(intents_df["intent"].value_counts().to_string())


if __name__ == "__main__":
    build_intents_dataset(INPUT_FILE, OUTPUT_FILE)
