from agentic.tools.reservation_tools import (
    list_available_experiences,
    create_reservation,
    cancel_reservation,
)

ALICE_ID = "a4ab87"


def test_list_available_experiences():
    experiences = list_available_experiences()
    assert len(experiences) > 0
    assert "experience_id" in experiences[0]
    assert all(exp["slots_available"] > 0 for exp in experiences)


def test_create_and_cancel_reservation():
    experience_id = list_available_experiences()[0]["experience_id"]

    created = create_reservation(ALICE_ID, experience_id)
    assert created["status"] == "reserved"
    assert created["user_id"] == ALICE_ID

    cancelled = cancel_reservation(created["reservation_id"])
    assert cancelled["status"] == "cancelled"


def test_cancel_reservation_not_found():
    assert cancel_reservation("does-not-exist") == {"error": "Reservation not found"}
