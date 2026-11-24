"""Tests for the saved classifier and shared text normalisation."""

import json
from pathlib import Path

import pytest
import sklearn

from app.classifier import MODEL_PATH, categories, get_model, predict
from app.text import normalise

EXPECTED_CATEGORIES = {
    "ACCOUNT", "CANCEL", "CONTACT", "DELIVERY", "FEEDBACK", "INVOICE",
    "ORDER", "PAYMENT", "REFUND", "SHIPPING", "SUBSCRIPTION",
}


def test_model_loads_with_expected_categories() -> None:
    """The committed model loads and predicts the 11 dataset categories."""
    assert MODEL_PATH.exists()
    assert get_model() is get_model()
    assert set(categories()) == EXPECTED_CATEGORIES


def test_model_matches_pinned_sklearn_version() -> None:
    """The model was trained with the scikit-learn version now installed."""
    meta_path = Path(MODEL_PATH).with_name("classifier_meta.json")
    assert json.loads(meta_path.read_text(encoding="utf-8"))["sklearn_version"] == sklearn.__version__


@pytest.mark.parametrize("text,expected", [
    ("i want to cancel my order", "ORDER"),
    ("how do i download my invoice", "INVOICE"),
    ("i want a refund of my money", "REFUND"),
    ("unsubscribe me from the newsletter", "SUBSCRIPTION"),
    ("i need to recover my account password", "ACCOUNT"),
])
def test_clear_messages_get_expected_category(text: str, expected: str) -> None:
    """Clear messages get the right category."""
    assert predict(text).category == expected


@pytest.mark.parametrize("text", ["refund", "asdf qwer zxcv", "!!!", "x" * 2000])
def test_confidence_is_a_probability(text: str) -> None:
    """Confidence stays between 0 and 1, even for odd input."""
    assert 0 <= predict(text).confidence <= 1


def test_needs_review_follows_threshold() -> None:
    """Unclear text is flagged and clear text is not."""
    assert predict("asdf qwer zxcv").needs_review is True
    assert predict("unsubscribe me from the newsletter").needs_review is False


@pytest.mark.parametrize("raw,expected", [
    ("Where is {{Order Number}}?", "where is ENT"),
    ("order #48213", "order ENT"),
    ("{{Currency Symbol}}{{Refund Amount}}", "ENT ENT"),
    ("I DON'T   know", "i dont know"),
    ("what’s up", "whats up"),
    ("", ""),
])
def test_normalise(raw: str, expected: str) -> None:
    """Placeholders and digits become ENT; case, punctuation and spacing are normalised."""
    assert normalise(raw) == expected


def test_placeholder_and_digits_normalise_the_same() -> None:
    """A real order number looks identical to the dataset placeholder."""
    assert normalise("order 48213") == normalise("order {{Order Number}}")
