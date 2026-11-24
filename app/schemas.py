"""Pydantic request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import DraftStatus, Priority, Status


class TicketCreate(BaseModel):
    """What a customer sends. Whitespace is trimmed before length checks."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=5, max_length=2000)


class TicketStatusUpdate(BaseModel):
    """A status change; only open, in_progress and closed are accepted."""

    model_config = ConfigDict(extra="forbid")

    status: Status


class TicketRead(BaseModel):
    """A ticket as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    message: str
    category: str
    category_confidence: float
    needs_review: bool
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    draft_status: DraftStatus
    draft_reply: str | None
    used_faq_ids: list[str]
    draft_no_match: bool
    draft_error: str | None


class LoginRequest(BaseModel):
    """Team login credentials."""

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)
