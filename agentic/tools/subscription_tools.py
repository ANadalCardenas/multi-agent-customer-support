from sqlalchemy import create_engine
from data.models import cultpass
from utils import get_session


engine = create_engine("sqlite:///data/external/cultpass.db")


def update_subscription_status(user_id: str, status: str) -> dict:
    """
    Update the status of a user's subscription (e.g. to cancel or pause
    it). Used when a user requests to cancel or pause their CultPass
    subscription.

    Input:
        user_id (str): the cultpass user_id whose subscription changes.
        status (str): the new status value (e.g. "active", "cancelled").

    Output:
        dict with keys: user_id (str), status (str) confirming the update.
    """
    with get_session(engine) as session:
        subscription = session.query(cultpass.Subscription).filter_by(user_id=user_id).first()
        if subscription:
            subscription.status = status
            return {
                "user_id": subscription.user_id,
                "status": subscription.status
            }
        return {"error": "Subscription not found"}


def update_subscription_tier(user_id: str, tier: str) -> dict:
    """
    Change a user's subscription tier (e.g. upgrade from basic to
    premium, or downgrade).

    Input:
        user_id (str): the cultpass user_id whose tier changes.
        tier (str): the new tier value (e.g. "basic", "premium").

    Output:
        dict with keys: user_id (str), tier (str) confirming the update.
    """
    with get_session(engine) as session:
        subscription = session.query(cultpass.Subscription).filter_by(user_id=user_id).first()
        if not subscription:
            return {"error": "Subscription not found"}
        subscription.tier = tier
        return {
            "user_id": subscription.user_id,
            "tier": subscription.tier
        }
