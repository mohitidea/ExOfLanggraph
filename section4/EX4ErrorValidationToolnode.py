from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, field_validator, ValidationError
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import ToolMessage, HumanMessage
from typing import Any, Dict
from langchain_core.tools import tool

import os
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
llm = ChatBedrockConverse(model_id= "anthropic.claude-3-sonnet-20240229-v1:0", #"amazon.nova lite-v1:0",region_name="us-east-1",
	temperature=0.5,
	max_tokens=1000)
llm.invoke('hi').content

# --------------------------
# Pydantic schema 
# --------------------------
class WireTransferInput(BaseModel):
    """Inputs for executing a wire transfer."""
    destination_country: str
    amount: float
    @field_validator("destination_country")
    @classmethod
    def check_sanctions(cls, v: str) -> str:
        restricted = ["Mordor", "Narnia", "Atlantis"]
        if v.title() in restricted:
            raise ValueError(f"{v} is restricted for wire transfers.")
        return v
    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive.")
        return v


# --------------------------
# Domain tool (Wire Transfer)
# --------------------------
@tool(args_schema=WireTransferInput)
def execute_wire_transfer(destination_country: str, amount: float) -> Dict[str, Any]:
    """
    Simulate a wire transfer.
    Raises ValueError for any domain-specific policy violations.
    """
    # Example policy: max transfer limit
    max_limit = 10000
    if amount > max_limit:
        raise ValueError(f"Transfer amount ${amount} exceeds max allowed ${max_limit}.")
    # Successful execution
    return {
        "status": "success",
        "message": f" Transfer of ${amount} to {destination_country} completed."
    }


# --------------------------
# Custom ToolNode error handler
# --------------------------
def wire_error_handler(e: Exception) -> str:
    """Convert tool exceptions into a domain-friendly message."""
    # LangChain tool wraps validation errors in ToolException sometimes
    from langchain_core.tools import ToolException
    # If wrapped in ToolException, get the original error
    if isinstance(e, ToolException) and hasattr(e, "__cause__") and e.__cause__:
        e = e.__cause__
    # Pydantic validation errors
    if isinstance(e, ValidationError):
        issues = [f"- {'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        return "Wire transfer input validation failed:\n" + "\n".join(issues)
    # Domain errors raised inside tool
    if isinstance(e, ValueError):
        return f"Wire transfer error: {e}"
    # Fallback
    return f"Unknown error during wire transfer: {str(e)}"


# --------------------------
# Build LangGraph with LLM + ToolNode
# --------------------------
tools = [execute_wire_transfer]
tool_node = ToolNode(tools, handle_tool_errors=wire_error_handler)
def call_llm(state: MessagesState):
    """LLM node: takes messages and returns an AIMessage."""
    llm_with_tools=llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}
builder = StateGraph(MessagesState)
builder.add_node("llm", call_llm)
builder.add_node("tools", tool_node)
# Flow edges
builder.add_edge(START, "llm")
builder.add_conditional_edges("llm", tools_condition)  # Routes to tools or END
builder.add_edge("tools", "llm")  # Tool results go back to LLM
graph = builder.compile()
graph


from rich import print
# --------------------------
# Demo run
# --------------------------
# Good input
good_input = {
    "messages": [
        ("system", "You are a bank assistant. Execute wire transfers using the tool."),
        ("user", "Send $5000 to India.")
    ]
}
good_run = graph.invoke(good_input)
print("\n--- GOOD RUN ---")
for m in good_run["messages"]:
    print(m)


# Bad input (validation + policy failure)
bad_input = {
    "messages": [
        ("system", "You are a bank assistant. Execute wire transfers using the tool."),
        ("user", "Send $15000 to Mordor.")
    ]
}
bad_run = graph.invoke(bad_input)
print("\n--- BAD RUN (shows ToolNode custom error handling) ---")
for m in bad_run["messages"]:
    print(m)
