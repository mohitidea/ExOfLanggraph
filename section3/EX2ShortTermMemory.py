from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Define a simple model node
def call_model(state: MessagesState):
    last_user_message = state["messages"][-1].content
    response = AIMessage(content=f"You said: {last_user_message}")
    return {"messages": state["messages"] + [response]}

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.set_entry_point("call_model")
builder.add_edge("call_model", END)

# Add short-term memory using in-memory checkpointer
checkpointer = InMemorySaver()
# Add Checkpointer
graph = builder.compile(checkpointer=checkpointer)
builder.compile(checkpointer=checkpointer)

res1= graph.invoke( {"messages": [HumanMessage(content="Hi, I'm ABC")]},
{"configurable": {"thread_id": "thread-1"}})

from rich import print

print("Response-1", res1)

res2=graph.invoke(
{"messages": [HumanMessage(content="I want to learn ML")]},
{"configurable": {"thread_id": "thread-1"}}
)
print("Response-2", res2)

res3=graph.invoke(
{"messages": [HumanMessage(content="I want to learn AI and ML")]},
{"configurable": {"thread_id": "thread-2"}}
)

print("Response-3", res3)

