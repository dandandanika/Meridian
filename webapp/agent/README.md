# Meridian Insight Assistant — LangGraph starter

A grounded chatbot that interprets the bias audit. Built to **learn LangGraph**: it's small enough to read end-to-end, and wired so the agent only ever *interprets* numbers it fetched from tools — never invents them.

## The LangGraph mental model

A LangGraph agent is a **state machine drawn as a graph**:

| Concept | Here |
|---|---|
| **State** | the running list of chat messages |
| **Nodes** | `agent` (the LLM decides what to do) and `tools` (runs requested tools) |
| **Edges** | after `agent`, a **conditional edge**: tool requested? → `tools` → back to `agent`; else → end |

That agent→tools→agent loop is the **ReAct pattern** (reason + act). `assistant.py` uses `create_react_agent`, the prebuilt graph that wires exactly this — so you get a working agent in ~10 lines, then can peel back the layers.

## Files
- `tools.py` — the tools (read the SQLite registry). **The docstrings are the LLM's instructions** for when to call each — written for the model.
- `assistant.py` — picks the chat model (Ollama or Groq), builds the ReAct graph, exposes `ask(message, history)`.

## Run it
```bash
pip install -r requirements.txt
# uses local Ollama by default (needs a tool-calling model):
ollama pull llama3.1:8b
# or use Groq:  export MERIDIAN_ASSISTANT_BACKEND=groq GROQ_API_KEY=...
python assistant.py "Which model is fairest, and is any race bias real?"
```
In the app it's served at `POST /api/assistant` and the `/assistant` page. Run an audit first so the registry has something to talk about.

## Guardrails (why this matters for a bias tool)
The system prompt forbids stating any number not returned by a tool, and forbids calling an underpowered null "fair" — it must say "not detected at this power". An ungrounded chatbot would hallucinate statistics; this one can't.

## Next step in learning LangGraph — build the graph by hand
Replace `create_react_agent` with an explicit `StateGraph` to see the internals:
```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

g = StateGraph(MessagesState)
g.add_node("agent", lambda s: {"messages": [model.bind_tools(TOOLS).invoke(s["messages"])]})
g.add_node("tools", ToolNode(TOOLS))
g.add_edge(START, "agent")
g.add_conditional_edges("agent", tools_condition)   # tool call? → tools : END
g.add_edge("tools", "agent")
app = g.compile()
```
This is the same machine `create_react_agent` builds — now you can add nodes (e.g. a "verify the cited stats" node, or a human-in-the-loop checkpoint), which is the bridge to the **orchestration agent** (auto-deciding more trials / P3 / P4) from the web-app plan.
