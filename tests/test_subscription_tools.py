from agentic.tools.subscription_tools import update_subscription_status, update_subscription_tier

ALICE_ID = "a4ab87"


def test_update_subscription_tier():
    result = update_subscription_tier(ALICE_ID, "premium")
    assert result["tier"] == "premium"


def test_update_subscription_tier_not_found():
    assert update_subscription_tier("does-not-exist", "premium") == {"error": "Subscription not found"}


def test_update_subscription_status():
    result = update_subscription_status(ALICE_ID, "active")
    assert result["status"] == "active"


def test_update_subscription_status_not_found():
    assert update_subscription_status("does-not-exist", "active") == {"error": "Subscription not found"}
