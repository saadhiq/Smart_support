"""Rule-based ticket priority assignment.

There are no priority labels to learn from, so priority comes from simple rules:

1. HIGH if the message mentions urgency, money taken wrongly, fraud/security, or
   being locked out (see HIGH_PATTERNS), whatever the category.
2. MEDIUM if the category is about money or an order in progress (PAYMENT, REFUND,
   ORDER, DELIVERY, SHIPPING, CANCEL), or the message sounds angry (ANGRY_PATTERNS).
3. LOW otherwise (ACCOUNT, CONTACT, FEEDBACK, INVOICE, SUBSCRIPTION questions).
"""

import re

from app.models import Priority

HIGH_PATTERNS = [
    r"\burgent(ly)?\b", r"\basap\b", r"\bimmediately\b", r"\bemergency\b",
    r"\bcharged (me )?twice\b", r"\bdouble[- ]?charged\b", r"\bcharged .*\bwithout\b",
    r"\bfraud\w*\b", r"\bscam\w*\b", r"\bstolen\b", r"\bhack(ed|er)?\b",
    r"\blocked out\b", r"\bcan'?t (log ?in|login|access)\b", r"\bcannot (log ?in|login|access)\b",
    r"\blawyer\b", r"\blegal action\b",
]
ANGRY_PATTERNS = [
    r"\bterrible\b", r"\bworst\b", r"\bunacceptable\b", r"\bridiculous\b",
    r"\bangry\b", r"\bfurious\b", r"\bdisgusting\b", r"\bnever again\b",
]
MEDIUM_CATEGORIES = {"PAYMENT", "REFUND", "ORDER", "DELIVERY", "SHIPPING", "CANCEL"}

_HIGH_RE = re.compile("|".join(HIGH_PATTERNS), re.IGNORECASE)
_ANGRY_RE = re.compile("|".join(ANGRY_PATTERNS), re.IGNORECASE)


def assign_priority(message: str, category: str) -> Priority:
    """Return high, medium or low using the rules in the module docstring."""
    if _HIGH_RE.search(message):
        return Priority.high
    if category in MEDIUM_CATEGORIES or _ANGRY_RE.search(message):
        return Priority.medium
    return Priority.low
