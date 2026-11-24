"""Team login and session handling."""

import secrets

from fastapi import HTTPException, Request, status

from app.config import get_settings

SESSION_KEY = "team_user"


def check_credentials(username: str, password: str) -> bool:
    """Compare against the team account in constant time."""
    s = get_settings()
    user_ok = secrets.compare_digest(username.encode(), s.team_username.encode())
    pass_ok = secrets.compare_digest(password.encode(), s.team_password.encode())
    return user_ok and pass_ok


def log_in(request: Request, username: str) -> None:
    """Mark the session as logged in."""
    request.session[SESSION_KEY] = username


def log_out(request: Request) -> None:
    """Clear the session."""
    request.session.clear()


def is_logged_in(request: Request) -> bool:
    """True when the session belongs to the team account."""
    return request.session.get(SESSION_KEY) == get_settings().team_username


def require_team(request: Request) -> str:
    """FastAPI dependency: 401 unless the team is logged in."""
    if not is_logged_in(request):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Login required.")
    return request.session[SESSION_KEY]
