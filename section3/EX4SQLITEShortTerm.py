import sqlite3
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from rich import print
import operator

# Define state
class State(TypedDict):
    tasks: Annotated[list[str],operator.add]


# Node that updates the state
def task_manager(state: State):
    # Just returns tasks received in input
    return {"tasks":[]}


# Build graph
builder = StateGraph(State)
builder.add_node("manager", task_manager)
builder.add_edge(START, "manager")
builder.add_edge("manager", END)


# check_same_thread=False allows the SQLite connection to be safely accessed from multiple threads instead of being restricted to the thread in which it was created.
conn = sqlite3.connect("tasks_memory.db", check_same_thread=False)
memory = SqliteSaver(conn)
graph = builder.compile(checkpointer=memory)
print(graph)


# -------- SESSION INPUT --------
config = {"configurable": {"thread_id": "user_1"}}
# Session input
input_data = {"tasks": ["Buy Paper"]}
result = graph.invoke(input_data, config)
print(result)


# -------- SAME SESSION  WITH NEW INPUT--------
config = {"configurable": {"thread_id": "user_1"}}
# Session input
input_data = {"tasks": ["Buy Pen"]}
result = graph.invoke(input_data, config)
print(result)

# Restart the kernel and rerun the graph execution. Observe that the 
# information persists across sessions for the same thread, but not 
# across different threads, which demonstrates thread-scoped short-term 
# memory.
# -------- Execute this code snippet the after kernel restart --------
config = {"configurable": {"thread_id": "user_1"}}
# Session input
input_data = {"tasks": ["Buy Paper"]}
result = graph.invoke(input_data, config)
print(result)


# -------- WITH NEW THREAD --------
config = {"configurable": {"thread_id": "user_2"}}
# Session input
input_data = {"tasks": ["Buy Paper"]}
result = graph.invoke(input_data, config)
print(result)

config = {"configurable": {"thread_id": "user_1"}}

from rich import print
# Get the state history based on the config
state_history = graph.get_state_history(config)
# Print or inspect the state history
print(state_history)
#  iterate through the states
for i, state in enumerate(state_history):
    print(f"State {i + 1}: {state}")




