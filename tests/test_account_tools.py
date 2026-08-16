from agentic.tools.account_tools import get_user_status, update_user_email

ALICE_ID = "a4ab87"


def test_get_user_status_found():
    result = get_user_status(ALICE_ID)
    assert result["email"] == "alice.kingsley@wonderland.com"
    assert result["is_blocked"] is True


def test_get_user_status_not_found():
    assert get_user_status("does-not-exist") == {"error": "User not found"}


def test_update_user_email_roundtrip():
    original_email = get_user_status(ALICE_ID)["email"]

    result = update_user_email(ALICE_ID, "pytest-temp@example.com")
    assert result["email"] == "pytest-temp@example.com"
    assert get_user_status(ALICE_ID)["email"] == "pytest-temp@example.com"

    update_user_email(ALICE_ID, original_email)


def test_update_user_email_not_found():
    assert update_user_email("does-not-exist", "x@example.com") == {"error": "User not found"}
