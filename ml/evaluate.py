"""Score the saved classifier on the hand-written messages in ml/my_20_messages.csv."""

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.explore import md_table

ROOT = Path(__file__).parent.parent
MODEL_PATH = ROOT / "models" / "classifier.joblib"
MESSAGES_PATH = ROOT / "ml" / "my_20_messages.csv"
REPORT_PATH = ROOT / "ml" / "reports" / "my_20.md"
REVIEW_THRESHOLD = 0.5


def load_messages(model: Pipeline) -> pd.DataFrame:
    """Read the CSV and check every true_category is a class the model knows."""
    df = pd.read_csv(MESSAGES_PATH)
    missing = {"text", "true_category"} - set(df.columns)
    if missing:
        sys.exit(f"{MESSAGES_PATH.name} is missing columns: {sorted(missing)}")
    templates = df.index[df["text"].str.strip().str.fullmatch(r"<\d+:.*>")]
    if len(templates):
        rows = ", ".join(str(i + 1) for i in templates)
        sys.exit(f"Rows {rows} are still template text. Replace them with real messages.")
    df["true_category"] = df["true_category"].str.strip().str.upper()
    unknown = set(df["true_category"]) - set(model.classes_)
    if unknown:
        sys.exit(f"Unknown labels {sorted(unknown)}. Allowed: {list(model.classes_)}")
    return df


def score(model: Pipeline, df: pd.DataFrame) -> pd.DataFrame:
    """Add predicted label, confidence, correctness and needs-review flag."""
    proba = model.predict_proba(df["text"])
    return df.assign(
        predicted=model.classes_[proba.argmax(axis=1)],
        confidence=proba.max(axis=1).round(3),
    ).assign(
        correct=lambda d: d["predicted"] == d["true_category"],
        needs_review=lambda d: d["confidence"] < REVIEW_THRESHOLD,
    )


def summary(df: pd.DataFrame) -> str:
    """Accuracy overall and split by the needs-review flag."""
    n = len(df)
    review = df[df["needs_review"]]
    sure = df[~df["needs_review"]]
    return (
        f"- Accuracy: **{df['correct'].sum()}/{n} = {df['correct'].mean():.0%}** "
        f"(each message is {100 / n:.0f} percentage points)\n"
        f"- Confidence >= {REVIEW_THRESHOLD}: {sure['correct'].sum()}/{len(sure)} correct\n"
        f"- Confidence < {REVIEW_THRESHOLD} (would be flagged 'needs review'): "
        f"{review['correct'].sum()}/{len(review)} correct\n"
    )


def main() -> None:
    """Score the hand-written messages and write ml/reports/my_20.md."""
    if not MESSAGES_PATH.exists():
        sys.exit(f"Write {MESSAGES_PATH} first (columns: text,true_category).")
    model = joblib.load(MODEL_PATH)
    df = score(model, load_messages(model))
    cols = ["text", "true_category", "predicted", "confidence", "correct", "needs_review"]
    report = (
        "# Hand-written messages\n\nMessages and labels written by hand before seeing "
        f"any predictions.\n\n{summary(df)}\n{md_table(df[cols])}\n\n"
        "## Wrong predictions explained\n\n_To be written by hand._\n"
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"accuracy={df['correct'].mean():.2f} ({df['correct'].sum()}/{len(df)}) -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
