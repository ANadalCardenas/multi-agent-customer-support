from data.models import cultpass
from sqlalchemy import create_engine
from utils import get_session

engine = create_engine("sqlite:///data/external/cultpass.db")


def get_user_status(user_id: str) -> dict:
    """
    Look up a CultPass user by their user_id and return their basic
    account status. Used to check whether a user's account is blocked
    before troubleshooting login or access issues.

    Input:
        user_id (str): the cultpass user_id to look up.

    Output:
        dict with keys: full_name (str), email (str), is_blocked (bool).
    """
    with get_session(engine) as session:
        user = session.query(cultpass.User).filter_by(user_id=user_id).first()
        if user:
            return {
                "full_name": user.full_name,
                "email": user.email,
                "is_blocked": user.is_blocked
            }
        else:
            return {"error": "User not found"}


def update_user_email(user_id: str, new_email: str) -> dict:
    """
    Update the registered email address for a CultPass user.

    Input:
        user_id (str): the cultpass user_id whose email should change.
        new_email (str): the new email address to set.

    Output:
        dict with keys: user_id (str), email (str) confirming the update.
    """
    with get_session(engine) as session:
        user = session.query(cultpass.User).filter_by(user_id=user_id).first()
        if user:
            user.email = new_email
            return {
                "user_id": user.user_id,
                "email": user.email
            }
        else:
            return {"error": "User not found"}
