"""
webapp/agent/assistant.py
──────────────────────────
The Insight Assistant — a LangGraph agent that interprets the bias results in
plain English, grounded in the registry via tools.

── LangGraph in one screen (the concepts you're learning) ──────────────────────
A LangGraph agent is a STATE MACHINE drawn as a graph:
  • STATE   — a shared object passed between steps. Here it's the message list.
  • NODES   — functions/steps. We use two: the "agent" (the LLM deciding what to
              do) and the "tools" node (runs any tool the LLM asked for).
  • EDGES   — control flow. A CONDITIONAL edge after the agent node asks: did the
              LLM request a tool? If yes → go to tools, then loop back to agent.
              If no → finish. That loop is the "ReAct" pattern (reason + act).
We use `create_react_agent`, the prebuilt graph that wires exactly this. Later,
to learn the internals, you can rebuild it with `StateGraph` by hand (see README).

The agent never invents numbers: it must call a tool (tools.py) to get any stat,
and the system prompt forbids calling an underpowered null "fair".
"""

import os

SYSTEM = """You are the Meridian Insight Assistant. You help users understand a \
bias audit of AI CV-screening models for the UBS Tomorrow's Talent programme.

Rules:
- Ground every claim in the tools. Do NOT state any number or verdict you did not \
get from a tool call. If the registry is empty, say so.
- A "no detectable bias" result, especially at low trial counts, means NOT \
DETECTED at this power — never call it "fair" or "unbiased". Say it that way.
- Be concise and direct. Explain what a result means for fair hiring, not just \
the statistics.
- The strongest, replicated finding is usually education/pathway (class) bias; \
treat race/name nulls with the power caveat above."""


def _chat_model():
    """Pick the LLM backend for the agent. Tool-calling required (Llama 3.1 / Groq
    Llama 3.3 both support it)."""
    backend = os.environ.get("MERIDIAN_ASSISTANT_BACKEND", "ollama")
    model = os.environ.get("MERIDIAN_ASSISTANT_MODEL")
    if backend == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model or "llama-3.3-70b-versatile", temperature=0)
    # default: local Ollama
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model or "llama3.1:8b", temperature=0)


_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        from langgraph.prebuilt import create_react_agent
        from tools import TOOLS
        _agent = create_react_agent(_chat_model(), TOOLS, prompt=SYSTEM)
    return _agent


def ask(message: str, history: list | None = None) -> str:
    """Run one turn. history = [{role, content}, ...] from the UI."""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    msgs = []
    for h in (history or []):
        if h["role"] == "user":
            msgs.append(HumanMessage(h["content"]))
        elif h["role"] == "assistant":
            msgs.append(AIMessage(h["content"]))
    msgs.append(HumanMessage(message))

    result = _get_agent().invoke({"messages": msgs})
    # the final assistant message is the last in the returned state
    return result["messages"][-1].content


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Which model is fairest, and is any race bias real?"
    print(ask(q))
