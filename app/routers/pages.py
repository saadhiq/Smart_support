"""Server-rendered HTML pages for customers and the team."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session

from app import tickets
from app.auth import check_credentials, is_logged_in, log_in, log_out
from app.classifier import categories
from app.db import get_session
from app.models import Status
from app.replies import load_faq
from app.schemas import TicketCreate

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
SessionDep = Annotated[Session, Depends(get_session)]


def redirect(url: str) -> RedirectResponse:
    """303 redirect, so the browser follows a POST with a GET."""
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


def field_errors(exc: ValidationError) -> dict[str, str]:
    """Map each invalid form field to its first error message."""
    errors: dict[str, str] = {}
    for e in exc.errors():
        field = str(e["loc"][0]) if e["loc"] else "form"
        errors.setdefault(field, e["msg"])
    return errors


@router.get("/", response_class=HTMLResponse)
def customer_form(request: Request, ticket: int | None = None) -> Response:
    """The customer form; after a submit it shows the new ticket number."""
    return templates.TemplateResponse(request, "index.html",
                                      {"form": {}, "errors": {}, "ticket_id": ticket})


@router.post("/", response_class=HTMLResponse)
def submit_ticket(request: Request, session: SessionDep, background: BackgroundTasks,
                  name: Annotated[str, Form()] = "", email: Annotated[str, Form()] = "",
                  message: Annotated[str, Form()] = "") -> Response:
    """Validate and create a ticket; on errors re-show the form with what was typed."""
    form = {"name": name, "email": email, "message": message}
    try:
        data = TicketCreate(**form)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request, "index.html", {"form": form, "errors": field_errors(exc), "ticket_id": None},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    ticket = tickets.create_ticket(session, data)
    background.add_task(tickets.generate_draft, ticket.id)
    return redirect(f"/?ticket={ticket.id}")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> Response:
    """The team login form."""
    if is_logged_in(request):
        return redirect("/team")
    return templates.TemplateResponse(request, "login.html", {"error": None, "username": ""})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: Annotated[str, Form()] = "",
                 password: Annotated[str, Form()] = "") -> Response:
    """Check credentials; on success go to the team page."""
    if not check_credentials(username, password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Invalid username or password.", "username": username},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    log_in(request, username)
    return redirect("/team")


@router.post("/logout")
def logout(request: Request) -> Response:
    """Log out and go back to the login page."""
    log_out(request)
    return redirect("/login")


@router.get("/team", response_class=HTMLResponse)
def team_list(request: Request, session: SessionDep, category: str = "") -> Response:
    """Login required. All tickets, newest first, with a category filter."""
    if not is_logged_in(request):
        return redirect("/login")
    category = category.strip().upper()
    if category not in categories():
        category = ""
    return templates.TemplateResponse(request, "team.html", {
        "tickets": tickets.list_tickets(session, category or None),
        "categories": categories(),
        "selected": category,
    })


@router.get("/team/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_page(request: Request, ticket_id: int, session: SessionDep,
                updated: bool = False) -> Response:
    """Login required. One ticket with a status form."""
    if not is_logged_in(request):
        return redirect("/login")
    ticket = tickets.get_ticket(session, ticket_id)
    if ticket is None:
        return templates.TemplateResponse(request, "not_found.html", {"ticket_id": ticket_id},
                                          status_code=status.HTTP_404_NOT_FOUND)
    faq = {e.id: e for e in load_faq()}
    return templates.TemplateResponse(request, "ticket.html", {
        "ticket": ticket, "statuses": list(Status), "updated": updated,
        "used_faq": [faq[i] for i in ticket.used_faq_ids if i in faq],
    })


@router.post("/team/tickets/{ticket_id}/draft")
def ticket_regenerate(request: Request, ticket_id: int, session: SessionDep,
                      background: BackgroundTasks) -> Response:
    """Login required. Draft the suggested reply again."""
    if not is_logged_in(request):
        return redirect("/login")
    ticket = tickets.get_ticket(session, ticket_id)
    if ticket is None:
        return redirect("/team")
    tickets.mark_draft_pending(session, ticket)
    background.add_task(tickets.generate_draft, ticket_id)
    return redirect(f"/team/tickets/{ticket_id}")


@router.post("/team/tickets/{ticket_id}/status")
def ticket_status(request: Request, ticket_id: int, session: SessionDep,
                  new_status: Annotated[str, Form(alias="status")] = "") -> Response:
    """Login required. Change the status, then reload the ticket page."""
    if not is_logged_in(request):
        return redirect("/login")
    ticket = tickets.get_ticket(session, ticket_id)
    if ticket is None:
        return redirect("/team")
    try:
        value = Status(new_status)
    except ValueError:
        return redirect(f"/team/tickets/{ticket_id}")
    tickets.update_status(session, ticket, value)
    return redirect(f"/team/tickets/{ticket_id}?updated=1")
