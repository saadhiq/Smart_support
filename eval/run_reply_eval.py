"""Run reply drafts with the real LLM and write a table for manual judging."""

import argparse
import html
import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.replies import DraftResult, draft_reply

EVAL_DIR = Path(__file__).parent
TICKETS_PATH = EVAL_DIR / "reply_test_tickets.json"
REPORT_PATH = EVAL_DIR / "reply_eval.md"
EXPECTED_TICKETS = 10


class EvalTicket(BaseModel):
    """One evaluation ticket."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


def load_tickets(path: Path) -> list[EvalTicket]:
    """Read and validate the evaluation tickets."""
    if not path.exists():
        sys.exit(f"Write {path} first. Format: [{{\"id\": \"T01\", \"text\": \"...\"}}]")
    try:
        tickets = [EvalTicket(**item) for item in json.loads(path.read_text(encoding="utf-8"))]
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        sys.exit(f"Invalid tickets file: {exc}")
    ids = [ticket.id for ticket in tickets]
    if len(ids) != len(set(ids)):
        sys.exit("Ticket ids must be unique.")
    if len(tickets) != EXPECTED_TICKETS:
        print(f"Warning: found {len(tickets)} tickets; the brief asks for {EXPECTED_TICKETS}.")
    return tickets


def cell(text: str) -> str:
    """Make text safe for one Markdown table cell."""
    escaped = html.escape(text, quote=False).replace("|", "\\|")
    return escaped.replace("\r", "").replace("\n", "<br>")


def table_row(ticket: EvalTicket, result: DraftResult) -> str:
    """One report row, with Good/Bad and Reason left empty."""
    ids = ", ".join(result.used_faq_ids) or "-"
    error = cell(result.error) if result.error else "-"
    return (f"| {cell(ticket.id)} | {cell(ticket.text)} | {cell(result.reply)} | {ids} | "
            f"{result.no_match} | {error} |  |  |")


def build_report(rows: list[str]) -> str:
    """The complete Markdown report."""
    header = ("| ID | Ticket | Draft | Used FAQ ids | no_match | Guard/error | Good/Bad | Reason |\n"
              "|---|---|---|---|---|---|---|---|")
    return "# Reply draft evaluation\n\n" + header + "\n" + "\n".join(rows) + "\n"


def parse_args() -> argparse.Namespace:
    """Command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets", type=Path, default=TICKETS_PATH)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--force", action="store_true", help="overwrite an existing report")
    return parser.parse_args()


def main() -> None:
    """Draft every ticket and write the report without overwriting manual judgements."""
    args = parse_args()
    if args.out.exists() and not args.force:
        sys.exit(f"{args.out} already exists and may hold your judgements. Use --force to replace it.")
    tickets = load_tickets(args.tickets)
    rows = [table_row(ticket, draft_reply(ticket.text)) for ticket in tickets]
    args.out.write_text(build_report(rows), encoding="utf-8")
    print(f"tickets={len(rows)} -> {args.out}")


if __name__ == "__main__":
    main()
