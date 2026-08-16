import json

from agentic.logging_utils import log_event, LOG_PATH


def test_log_event_writes_valid_json_line():
    log_event(node="pytest", ticket_id="t-test", event="unit_test", foo="bar")

    last_line = LOG_PATH.read_text().strip().splitlines()[-1]
    record = json.loads(last_line)

    assert record["node"] == "pytest"
    assert record["ticket_id"] == "t-test"
    assert record["event"] == "unit_test"
    assert record["foo"] == "bar"
