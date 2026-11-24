"""SQLModel database tables."""

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class Status(str, Enum):
    """Ticket workflow status."""

    open = "open"
    in_progress = "in_progress"
    closed = "closed"


class Priority(str, Enum):
    """Ticket priority, set by rules in app/priority.py."""

    low = "low"
    medium = "medium"
    high = "high"


class DraftStatus(str, Enum):
    """State of the suggested reply."""

    pending = "pending"
    ready = "ready"
    failed = "failed"


def utc_now() -> datetime:
    """Current time in UTC."""
    return datetime.now(timezone.utc)


class Ticket(SQLModel, table=True):
    """A customer support ticket."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(max_length=320)
    message: str = Field(max_length=2000)
    category: str = Field(index=True)
    category_confidence: float
    needs_review: bool = False
    priority: Priority = Priority.low
    status: Status = Field(default=Status.open, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    draft_status: DraftStatus = DraftStatus.pending
    draft_reply: str | None = None
    draft_faq_ids: str = ""  # comma-separated FAQ ids, e.g. "FAQ-01,FAQ-03"
    draft_no_match: bool = False
    draft_error: str | None = None

    @property
    def used_faq_ids(self) -> list[str]:
        """The cited FAQ ids as a list."""
        return [i for i in self.draft_faq_ids.split(",") if i]
