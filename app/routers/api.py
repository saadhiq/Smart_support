"""REST API routes for tickets and team login."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app import tickets
from app.auth import check_credentials, log_in, log_out, require_team
from app.classifier import categories
from app.db import get_session
from app.models import Ticket
from app.schemas import LoginRequest, TicketCreate, TicketRead, TicketStatusUpdate

router = APIRouter(prefix="/api", tags=["api"])
SessionDep = Annotated[Session, Depends(get_session)]
TeamDep = Annotated[str, Depends(require_team)]


def ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    """Fetch a ticket or raise 404."""
    ticket = tickets.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ticket {ticket_id} not found.")
    return ticket


@router.post("/login")
def login(body: LoginRequest, request: Request) -> dict[str, bool]:
    """Log the team in; sets a signed session cookie."""
    if not check_credentials(body.username, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password.")
    log_in(request, body.username)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request) -> dict[str, bool]:
    """Log out and clear the session."""
    log_out(request)
    return {"ok": True}


@router.post("/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketRead)
def create_ticket(body: TicketCreate, session: SessionDep, background: BackgroundTasks) -> Ticket:
    """Public: submit a ticket. Classified and prioritised now; reply drafted in the background."""
    ticket = tickets.create_ticket(session, body)
    background.add_task(tickets.generate_draft, ticket.id)
    return ticket


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(session: SessionDep, _: TeamDep,
                 category: Annotated[str | None, Query()] = None) -> list[Ticket]:
    """Team only: list tickets, newest first, optionally filtered by category."""
    if category is not None:
        category = category.strip().upper()
        if category not in categories():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Unknown category '{category}'. Allowed: {', '.join(categories())}.",
            )
    return tickets.list_tickets(session, category)


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, session: SessionDep, _: TeamDep) -> Ticket:
    """Team only: one ticket."""
    return ticket_or_404(session, ticket_id)


@router.patch("/tickets/{ticket_id}/status", response_model=TicketRead)
def update_status(ticket_id: int, body: TicketStatusUpdate,
                  session: SessionDep, _: TeamDep) -> Ticket:
    """Team only: change a ticket's status."""
    return tickets.update_status(session, ticket_or_404(session, ticket_id), body.status)


@router.post("/tickets/{ticket_id}/draft", status_code=status.HTTP_202_ACCEPTED,
             response_model=TicketRead)
def regenerate_draft(ticket_id: int, session: SessionDep, _: TeamDep,
                     background: BackgroundTasks) -> Ticket:
    """Team only: draft the suggested reply again (runs in the background)."""
    ticket = tickets.mark_draft_pending(session, ticket_or_404(session, ticket_id))
    background.add_task(tickets.generate_draft, ticket_id)
    return ticket
