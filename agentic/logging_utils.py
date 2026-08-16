import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "agent_events.jsonl"

logger = logging.getLogger("agentic")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(LOG_PATH)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_event(node: str, ticket_id: str, event: str, **details) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node": node,
        "ticket_id": ticket_id,
        "event": event,
        **details,
    }
    logger.info(json.dumps(record))
