"""Load the trained classifier and predict ticket categories."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

MODEL_PATH = Path(__file__).parent.parent / "models" / "classifier.joblib"
REVIEW_THRESHOLD = 0.5


@dataclass(frozen=True)
class Prediction:
    """A predicted category with its probability."""

    category: str
    confidence: float
    needs_review: bool


@lru_cache
def get_model() -> Pipeline:
    """Load the model from disk once and reuse it for every request."""
    return joblib.load(MODEL_PATH)


def categories() -> list[str]:
    """All category labels the model can predict."""
    return [str(c) for c in get_model().classes_]


def predict(text: str) -> Prediction:
    """Predict the category of one message; flag it for review when unsure."""
    model = get_model()
    proba = model.predict_proba([text])[0]
    best = int(proba.argmax())
    confidence = float(proba[best])
    return Prediction(str(model.classes_[best]), round(confidence, 4),
                      confidence < REVIEW_THRESHOLD)
