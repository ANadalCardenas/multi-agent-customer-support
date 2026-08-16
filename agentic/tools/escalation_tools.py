from data.models import udahub
from sqlalchemy import create_engine
from utils import get_session

engine = create_engine("sqlite:///data/core/udahub.db")


def escalate_to_supervisor(ticket_id: str, reason: str) -> dict:
    """
    Hand a ticket back to the supervisor when the current agent cannot
    resolve it. Marks the ticket's metadata status as "escalated" so
    it queues for human review.

    Input:
        ticket_id (str): the udahub ticket_id being escalated.
        reason (str): why the agent could not resolve the ticket.

    Output:
        dict with keys: ticket_id (str), status (str) = "escalated".
    """
    with get_session(engine) as session:
        ticket_metadata = session.query(udahub.TicketMetadata).filter_by(ticket_id=ticket_id).first()
        if ticket_metadata:
            ticket_metadata.status = "escalated"
            return {
                "ticket_id": ticket_metadata.ticket_id,
                "status": ticket_metadata.status,
                "reason": reason
            }
        else:
            return {"error": "Ticket not found"}
