from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from agentic.agents.account_agent import account_agent
from agentic.agents.subscription_agent import subscription_agent
from agentic.agents.reservation_agent import reservation_agent
from agentic.agents.knowledge_agent import knowledge_agent
from agentic.tools.escalation_tools import escalate_to_supervisor
from agentic.logging_utils import log_event
from agentic.tools.memory_tools import (
    get_user_ticket_history,
    persist_ticket_messages,
    get_ticket_metadata,
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
)


class State(MessagesState):
    next_agent: str
    escalation_reason: str
    escalated: bool
    finished: bool
    ticket_id: str


class SupervisorOutput(BaseModel):
    finished: bool
    escalated: bool
    ticket_id: str
    escalation_reason: str
    next_agent: str


SUPERVISOR_PROMPT = SystemMessage(
    content=(
        "You are the Supervisor for CultPass customer support. You do not "
        "answer tickets yourself — you read the conversation so far and "
        "decide what happens next, filling in a structured decision.\n\n"
        "There are 4 specialized agents you can route to:\n"
        "- account_agent: login problems, blocked accounts, changing the "
        "registered email.\n"
        "- subscription_agent: performing an action ON a subscription — "
        "cancelling/pausing it, or upgrading/downgrading its tier. Not for "
        "questions about what a subscription includes, costs, or how it "
        "works — those go to knowledge_agent.\n"
        "- reservation_agent: browsing available experiences, creating or "
        "cancelling a reservation.\n"
        "- knowledge_agent: general questions, policies, pricing, or "
        "informational questions (e.g. \"what's included in my "
        "subscription\") — even if the word 'subscription' appears, route "
        "here unless the user wants to actually change something.\n\n"
        "Decision process, in order:\n\n"
        "1. Check if the ticket is already resolved. If the last message in "
        "the conversation is a complete, satisfactory answer from one of "
        "the specialized agents (not a request for escalation), set "
        "finished=true. When finished=true, next_agent and escalated are "
        "irrelevant — leave next_agent as an empty string and escalated as "
        "false.\n\n"
        "2. Check if this needs to be escalated to a human. Set "
        "escalated=true if:\n"
        "   - The last specialized agent explicitly could not resolve the "
        "request (e.g. it called escalate_to_supervisor), or\n"
        "   - The request does not clearly fit any of the 4 domains above "
        "and you are not confident enough to route it safely, or\n"
        "   - The ticket metadata shows it has been open for a long time "
        "(compare its created_at to the current time) without being "
        "resolved — treat this as high urgency and prefer escalating over "
        "routing it for yet another attempt.\n"
        "   When escalated=true, always fill escalation_reason with a "
        "short, specific explanation (e.g. \"user requested a refund "
        "exception, requires supervisor approval\"). Leave next_agent "
        "empty.\n\n"
        "3. Otherwise, this is a new or still-unresolved request that fits "
        "one of the 4 domains. Set next_agent to the single best match "
        "(account_agent, subscription_agent, reservation_agent, or "
        "knowledge_agent), with finished=false and escalated=false. If the "
        "ticket metadata's tags or main_issue_type already point clearly "
        "to one of the 4 domains, treat that as a strong signal — trust it "
        "even if the message content alone is ambiguous.\n\n"
        "You will also receive a separate message with the ticket's "
        "metadata (current time, tags, main_issue_type, status, channel, "
        "created_at) — always take it into account alongside the "
        "conversation content when deciding.\n\n"
        "Always copy the ticket_id exactly as it appears in the "
        "conversation (look for a message like \"ThreadId: <ticket_id>\") "
        "into the ticket_id field — never invent or omit it.\n\n"
        "Be conservative: if you are unsure which agent should handle the "
        "request, prefer escalated=true over guessing a next_agent, since "
        "a wrong routing wastes a turn and confuses the user."
    )
)


def _get_tool_calls(messages) -> list[str]:
    names = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            names.append(call["name"])
    return names


def supervisor(state: State) -> dict:
    if state.get("escalated"):
        log_event(
            node="supervisor",
            ticket_id=state.get("ticket_id", ""),
            event="routing_decision",
            source="agent_escalation",
            escalation_reason=state.get("escalation_reason", ""),
            next_agent="escalation_node",
        )
        print(
            f"Supervisor handling escalated ticket {state['ticket_id']} "
            f"for reason: {state['escalation_reason']}"
        )
        return {"finished": True}

    structured_llm = llm.with_structured_output(SupervisorOutput)
    ticked_id = state.get("ticket_id", "")
    metadata = get_ticket_metadata(ticked_id) if ticked_id else {}
    metadata_message = SystemMessage(
        content=(
            f"Ticket metadata:\n"
            f"- ticket_id: {ticked_id}\n"
            f"- created_at: {metadata.get('created_at', '')}\n"
            f"- status: {metadata.get('status', '')}\n"
            f"- main_issue_type: {metadata.get('main_issue_type', '')}\n"
            f"- tags: {metadata.get('tags', '')}\n"
            f"- channel: {metadata.get('channel', '')}\n"
            f"date now: {datetime.now(timezone.utc).isoformat()}\n"
        )   
    )
    decision = structured_llm.invoke([SUPERVISOR_PROMPT, metadata_message] + state["messages"])

    log_event(
        node="supervisor",
        ticket_id=decision.ticket_id or state.get("ticket_id", ""),
        event="routing_decision",
        source="llm_classification",
        next_agent=decision.next_agent,
        finished=decision.finished,
        escalated=decision.escalated,
        escalation_reason=decision.escalation_reason,
        ticket_tags = metadata.get("tags", ""),
    )

    return {
        "next_agent": decision.next_agent,
        "finished": decision.finished,
        "escalated": decision.escalated,
        "escalation_reason": decision.escalation_reason,
        "ticket_id": decision.ticket_id or state.get("ticket_id", ""),
    }


def account_node(state: State) -> dict:
    result = account_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    tool_calls = _get_tool_calls(new_messages)
    escalated = "escalate_to_supervisor" in tool_calls

    log_event(
        node="account_node",
        ticket_id=state.get("ticket_id", ""),
        event="agent_turn",
        tools_used=tool_calls,
        escalated=escalated,
    )

    return {
        "messages": new_messages,
        "escalated": escalated,
    }

def knowledge_node(state: State) -> dict:
    result = knowledge_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    tool_calls = _get_tool_calls(new_messages)
    escalated = "escalate_to_supervisor" in tool_calls

    log_event(
        node="knowledge_node",
        ticket_id=state.get("ticket_id", ""),
        event="agent_turn",
        tools_used=tool_calls,
        escalated=escalated,
    )

    return {
        "messages": new_messages,
        "escalated": escalated,
    }

def subscription_node(state: State) -> dict:
    result = subscription_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    tool_calls = _get_tool_calls(new_messages)
    escalated = "escalate_to_supervisor" in tool_calls

    log_event(
        node="subscription_node",
        ticket_id=state.get("ticket_id", ""),
        event="agent_turn",
        tools_used=tool_calls,
        escalated=escalated,
    )

    return {
        "messages": new_messages,
        "escalated": escalated,
    }

def reservation_node(state: State) -> dict:
    result = reservation_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    tool_calls = _get_tool_calls(new_messages)
    escalated = "escalate_to_supervisor" in tool_calls

    log_event(
        node="reservation_node",
        ticket_id=state.get("ticket_id", ""),
        event="agent_turn",
        tools_used=tool_calls,
        escalated=escalated,
    )

    return {
        "messages": new_messages,
        "escalated": escalated,
    }

def escalation_node(state: State) -> dict:
    escalate_to_supervisor(state["ticket_id"], state["escalation_reason"])
    log_event(
        node="escalation_node",
        ticket_id=state.get("ticket_id", ""),
        event="ticket_escalated",
        escalation_reason=state.get("escalation_reason", ""),
    )
    print(
        f"Supervisor escalated ticket {state['ticket_id']} "
        f"for reason: {state['escalation_reason']}"
    )
    return {
        "finished": True,
    }

def finished_node(state: State) -> dict:
    persist_ticket_messages(state["ticket_id"], state["messages"])
    log_event(
        node="finished_node",
        ticket_id=state.get("ticket_id", ""),
        event="ticket_finished",
    )
    print(f"Ticket {state['ticket_id']} marked as finished and persisted.")
    return {
        "finished": True,
    }

def route_from_supervisor(state: State) -> str:
    if state.get("finished"):
        return "finished"
    elif state.get("escalated"):
        return "escalated"
    else:
        return state.get("next_agent", "finished")

path_map = {
    "account_agent": "account_node",
    "subscription_agent": "subscription_node",
    "reservation_agent": "reservation_node",
    "knowledge_agent": "knowledge_node",
    "escalated": "escalation_node",
    "finished": "finished_node",
}

workflow_graph = StateGraph(State)
checkpointer = MemorySaver()

workflow_graph.add_node("supervisor", supervisor)
workflow_graph.add_node("account_node", account_node)
workflow_graph.add_node("subscription_node", subscription_node)
workflow_graph.add_node("reservation_node", reservation_node)
workflow_graph.add_node("knowledge_node", knowledge_node)
workflow_graph.add_node("escalation_node", escalation_node)
workflow_graph.add_node("finished_node", finished_node)

workflow_graph.add_edge(START, "supervisor")
workflow_graph.add_conditional_edges("supervisor", route_from_supervisor, path_map)
workflow_graph.add_edge("account_node", "supervisor")
workflow_graph.add_edge("subscription_node", "supervisor")
workflow_graph.add_edge("reservation_node", "supervisor")
workflow_graph.add_edge("knowledge_node", "supervisor")
workflow_graph.add_edge("escalation_node", "finished_node")
workflow_graph.add_edge("finished_node", END)

orchestrator = workflow_graph.compile(checkpointer=checkpointer)

