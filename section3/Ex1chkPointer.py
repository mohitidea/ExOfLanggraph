from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

class AgentState(TypedDict, total=False):
    a: Optional[str]  #Annotated[Optional[str],operator.add]
    b: Optional[str]

def node_a(state: AgentState) -> AgentState:
    state["a"] = "Hello"
    return state
 
def node_b(state: AgentState) -> AgentState:
    state["b"] = state["a"] + " World!"
    return state

builder = StateGraph(AgentState)
 
builder.add_node("A", node_a)
builder.add_node("B", node_b)
 
builder.set_entry_point("A")
builder.add_edge("A", "B")
 
#  Compile with a checkpoint saver
graph = builder.compile(checkpointer=InMemorySaver())
print(graph)

config = {"configurable": {"thread_id": "thread_1"}}
final_state = graph.invoke({"a":"Hi"}, config=config)
print(final_state)

from rich import print
# Get the state history based on the config
state_history = graph.get_state_history(config)
# Print or inspect the state history
print(state_history)
from rich import print
#  iterate through the states
for i, state in enumerate(state_history):
    print(f"State {i + 1}: {state}")

#last state
print("Final state:\n" + str(graph.get_state(config)))