import uuid

from langchain_core.messages import HumanMessage

from agentic.tools.memory_tools import (
    get_user_ticket_history,
    persist_ticket_messages,
    get_ticket_metadata,
    engine,
)
from data.models import udahub
from utils import get_session

ALICE_ID = "a4ab87"
REAL_TICKET_ID = "ffdd7d32-dfa7-42c2-afb8-63e7e5bb7f56"


def test_get_user_ticket_history_returns_known_ticket():
    history = get_user_ticket_history(ALICE_ID)
    assert any(ticket["ticket_id"] == REAL_TICKET_ID for ticket in history)


def test_get_user_ticket_history_unknown_user():
    assert get_user_ticket_history("does-not-exist") == []


def test_get_ticket_metadata_returns_known_ticket():
    metadata = get_ticket_metadata(REAL_TICKET_ID)
    assert metadata["tags"] == "login, access"


def test_get_ticket_metadata_unknown_ticket():
    assert get_ticket_metadata("does-not-exist") == {}


def test_persist_ticket_messages_is_idempotent():
    message = HumanMessage(content="pytest smoke message", id=str(uuid.uuid4()))

    persist_ticket_messages(REAL_TICKET_ID, [message])
    persist_ticket_messages(REAL_TICKET_ID, [message])

    ticket = next(
        t for t in get_user_ticket_history(ALICE_ID) if t["ticket_id"] == REAL_TICKET_ID
    )
    matches = [m for m in ticket["messages"] if m["content"] == "pytest smoke message"]
    assert len(matches) == 1

    with get_session(engine) as session:
        session.query(udahub.TicketMessage).filter_by(message_id=message.id).delete()
