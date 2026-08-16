import uuid

from sqlalchemy import create_engine
from data.models import cultpass
from utils import get_session


engine = create_engine("sqlite:///data/external/cultpass.db")

EXPERIENCE_LIMIT = 100


def list_available_experiences() -> list[dict]:
    """
    List CultPass experiences that still have available slots, so a
    user can choose one to reserve.

    Input:
        (none)

    Output:
        list of dicts, each with: experience_id (str), title (str),
        location (str), when (datetime), slots_available (int),
        is_premium (bool).
    """
    with get_session(engine) as session:
        experiences = session.query(cultpass.Experience).filter(
            cultpass.Experience.slots_available > 0
        ).limit(EXPERIENCE_LIMIT).all()

        return [
            {
                "experience_id": exp.experience_id,
                "title": exp.title,
                "location": exp.location,
                "when": exp.when,
                "slots_available": exp.slots_available,
                "is_premium": exp.is_premium
            }
            for exp in experiences
        ]


def create_reservation(user_id: str, experience_id: str) -> dict:
    """
    Reserve a spot for a user in a given experience.

    Input:
        user_id (str): the cultpass user_id making the reservation.
        experience_id (str): the experience to reserve a spot in.

    Output:
        dict with keys: reservation_id (str), status (str).
    """
    with get_session(engine) as session:
        new_reservation = cultpass.Reservation(
            reservation_id=str(uuid.uuid4())[:6],
            user_id=user_id,
            experience_id=experience_id,
            status="reserved",
        )
        session.add(new_reservation)

        return {
            "user_id": new_reservation.user_id,
            "experience_id": new_reservation.experience_id,
            "reservation_id": new_reservation.reservation_id,
            "status": new_reservation.status
        }


def cancel_reservation(reservation_id: str) -> dict:
    """
    Cancel an existing reservation.

    Input:
        reservation_id (str): the reservation to cancel.

    Output:
        dict with keys: reservation_id (str), status (str) confirming
        the cancellation.
    """
    with get_session(engine) as session:
        reservation = session.query(cultpass.Reservation).filter_by(reservation_id=reservation_id).first()
        if reservation:
            reservation.status = "cancelled"
            return {
                "reservation_id": reservation.reservation_id,
                "status": reservation.status
            }
        else:
            return {"error": "Reservation not found"}
