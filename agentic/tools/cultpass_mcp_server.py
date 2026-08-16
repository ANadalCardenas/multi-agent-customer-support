import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastmcp import FastMCP
from utils import get_session
from data.models import cultpass
from sqlalchemy import create_engine
mcp = FastMCP("cultpass")
engine = create_engine("sqlite:///data/external/cultpass.db")

@mcp.tool
def get_subscription_status(user_id:str) -> dict:
    """Get the subscription status of a user."""
    
    with get_session(engine) as session:
        subscription = session.query(cultpass.Subscription).filter_by(user_id=user_id).first()
        if subscription:
            return {"status": subscription.status, "tier": subscription.tier}
        else:
            return {"error": "User not found"}

if __name__=="__main__":
    mcp.run()