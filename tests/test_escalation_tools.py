from agentic.tools.escalation_tools import escalate_to_supervisor, engine
from data.models import udahub
from utils import get_session

REAL_TICKET_ID = "ffdd7d32-dfa7-42c2-afb8-63e7e5bb7f56"


def test_escalate_to_supervisor_updates_status():
    result = escalate_to_supervisor(REAL_TICKET_ID, "pytest test escalation")
    assert result["status"] == "escalated"
    assert result["reason"] == "pytest test escalation"

    with get_session(engine) as session:
        metadata = session.query(udahub.TicketMetadata).filter_by(ticket_id=REAL_TICKET_ID).first()
        metadata.status = "open"


def test_escalate_to_supervisor_not_found():
    assert escalate_to_supervisor("does-not-exist", "reason") == {"error": "Ticket not found"}
