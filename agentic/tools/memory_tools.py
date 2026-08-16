from sqlalchemy import create_engine
from data.models import udahub
from utils import get_session

engine = create_engine("sqlite:///data/core/udahub.db")


def get_user_ticket_history(user_id: str) -> list[dict]:
    """
    Retrieve the ticket history for a given user, across all of their
    past tickets, to provide context for personalized responses.

    Args:
        user_id (str): the cultpass user_id (external_user_id in udahub).

    Returns:
        list of dicts, each with: ticket_id (str), channel (str),
        created_at (datetime), status (str), main_issue_type (str),
        tags (str), messages (list of {role, content}).
    """
    with get_session(engine) as session:
        udahub_user = session.query(udahub.User).filter_by(external_user_id=user_id).first()
        if not udahub_user:
            return []

        tickets = session.query(udahub.Ticket).filter_by(user_id=udahub_user.user_id).all()

        return [
            {
                "ticket_id": ticket.ticket_id,
                "channel": ticket.channel,
                "created_at": ticket.created_at,
                "status": ticket.ticket_metadata.status if ticket.ticket_metadata else None,
                "main_issue_type": ticket.ticket_metadata.main_issue_type if ticket.ticket_metadata else None,
                "tags": ticket.ticket_metadata.tags if ticket.ticket_metadata else None,
                "messages": [
                    {"role": message.role.value, "content": message.content}
                    for message in ticket.messages
                ],
            }
            for ticket in tickets
        ]


def persist_ticket_messages(ticket_id: str, messages) -> None:
    """
    Persist new conversation messages to a ticket's message history.
    Idempotent: safe to call multiple times with the full message list,
    since it skips messages already stored (matched by message id).

    Args:
        ticket_id (str): the udahub ticket_id these messages belong to.
        messages: a list of LangChain BaseMessage objects (from graph state).
    """
    role_map = {"human": udahub.RoleEnum.user, "ai": udahub.RoleEnum.ai}

    with get_session(engine) as session:
        existing_ids = {
            row.message_id
            for row in session.query(udahub.TicketMessage.message_id).filter_by(ticket_id=ticket_id)
        }

        for message in messages:
            role = role_map.get(message.type)
            if role is None or not message.content or message.id in existing_ids:
                continue

            session.add(udahub.TicketMessage(
                message_id=message.id,
                ticket_id=ticket_id,
                role=role,
                content=message.content,
            ))


def get_ticket_metadata(ticket_id: str) -> dict:
    """
    Retrieve metadata for the current ticket (tags, issue type, status,
    channel, creation time), used to inform routing decisions alongside
    the conversation content.

    Args:
        ticket_id (str): the udahub ticket_id.

    Returns:
        dict with keys: channel, created_at, status, main_issue_type,
        tags. Empty dict if the ticket does not exist.
    """
    with get_session(engine) as session:
        ticket = session.query(udahub.Ticket).filter_by(ticket_id=ticket_id).first()
        if not ticket:
            return {}

        metadata = ticket.ticket_metadata
        return {
            "channel": ticket.channel,
            "created_at": ticket.created_at,
            "status": metadata.status if metadata else None,
            "main_issue_type": metadata.main_issue_type if metadata else None,
            "tags": metadata.tags if metadata else None,
        }
