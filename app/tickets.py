"""Ticket service functions shared by the API and the HTML pages."""

from sqlmodel import Session, col, select

from app.classifier import predict
from app.db import get_engine
from app.models import DraftStatus, Status, Ticket, utc_now
from app.priority import assign_priority
from app.replies import draft_reply
from app.schemas import TicketCreate


def create_ticket(session: Session, data: TicketCreate) -> Ticket:
    """Classify, prioritise and store a new ticket."""
    pred = predict(data.message)
    ticket = Ticket(
        name=data.name,
        email=str(data.email),
        message=data.message,
        category=pred.category,
        category_confidence=pred.confidence,
        needs_review=pred.needs_review,
        priority=assign_priority(data.message, pred.category),
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def list_tickets(session: Session, category: str | None = None) -> list[Ticket]:
    """All tickets, newest first, optionally filtered by category."""
    query = select(Ticket).order_by(col(Ticket.created_at).desc(), col(Ticket.id).desc())
    if category:
        query = query.where(Ticket.category == category)
    return list(session.exec(query).all())


def get_ticket(session: Session, ticket_id: int) -> Ticket | None:
    """One ticket by id, or None."""
    return session.get(Ticket, ticket_id)


def mark_draft_pending(session: Session, ticket: Ticket) -> Ticket:
    """Reset the draft before regenerating it."""
    ticket.draft_status = DraftStatus.pending
    ticket.draft_error = None
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def generate_draft(ticket_id: int) -> None:
    """Background task: draft a reply and store it on the ticket.

    Runs after the response is sent, so it opens its own database session.
    """
    with Session(get_engine()) as session:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None:
            return
        result = draft_reply(ticket.message)
        ticket.draft_reply = result.reply
        ticket.draft_faq_ids = ",".join(result.used_faq_ids)
        ticket.draft_no_match = result.no_match
        ticket.draft_error = result.error
        failed = result.error is not None and not result.used_faq_ids
        ticket.draft_status = DraftStatus.failed if failed else DraftStatus.ready
        session.add(ticket)
        session.commit()


def update_status(session: Session, ticket: Ticket, status: Status) -> Ticket:
    """Change a ticket's status and its updated_at time."""
    ticket.status = status
    ticket.updated_at = utc_now()
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
