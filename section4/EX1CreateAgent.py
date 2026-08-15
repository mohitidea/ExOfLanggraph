import os
import json
from typing import List, Dict
from langchain_core.tools import tool
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, END, START, MessagesState
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from rich import print
# --- Initialize LLM ---
llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0", #cohere.command-r-plus-v1:0","amazon.nova-lite-v1:0", #
    region_name="us-east-1",
    temperature=0.5,
    max_tokens=1024
)

@tool
def get_weather(city: str) -> str:
    """Return a one-line weather summary for 'city'."""
    fake = {"Mysore": "23°C, partly cloudy", "New Delhi": "32°C, hot and humid", "Bangalore": "25°C, foggy"}
    return f"Weather in {city}: {fake.get(city, '20°C, clear skies')}"
@tool
def find_attractions(city: str) -> str:
    """Return a short list of top attractions for the city in JSON string form."""
    attractions = {
        "Mysore": [
            {"name": "Mysore Palace", "type": "Historical", "visit_time_mins": 90},
            {"name": "Mysore Zoo", "type": "Zoology", "visit_time_mins": 120},
        ],
        "Bangalore": [
            {"name": "LalBagh", "type": "entertainment", "visit_time_mins": 60},
        ]
    }
    return json.dumps(attractions.get(city, []))
@tool
def get_directions(origin: str, destination: str) -> str:
    """Return a short route summary for the attractions in the given city."""
    return f"Route from {origin} to {destination}: Drive ~30 mins (20 km) via Main St."
tools = [get_weather, find_attractions, get_directions]

# --- System prompt ---
system_prompt = "You are a travel assistant agent. Use all the tools to help plan trips."
# --- Create agent with HumanInTheLoopMiddleware ---
itinerary_agent = create_agent(
    model=llm,
    tools=tools,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "get_weather": False,  # No human approval needed
                "find_attractions":{"allowed_decisions": ["approve", "edit", "reject"]},# {"allowed_decisions": ["approve", "edit", "reject"]},  # Human can approve/edit
                "get_directions":{"allowed_decisions": ["approve", "edit", "reject"]}  # Human can approve/edit
            }
        )
    ],
    checkpointer=InMemorySaver()
)

# --- Initialize StateGraph ---
workflow = StateGraph(MessagesState)
# Add the agent as a node
workflow.add_node("itinerary_agent", itinerary_agent)
# Define the workflow edges
workflow.add_edge(START, "itinerary_agent")
workflow.add_edge("itinerary_agent", END)
# Compile the graph
app = workflow.compile(checkpointer=InMemorySaver())
app


from langgraph.types import Command
import uuid
#  Generate a unique thread_id for this conversation
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}
# Initial Execution
print(f"--- Starting Session: {thread_id} ---")
messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content="I want to visit Mysore for a trip.")
]
# Run until the first interrupt (for find_attractions)
for step in app.stream({"messages": messages}, config):
    print(step)


resume_command = Command(resume={ "decisions": [ {"type": "approve"},]})
for step in app.stream(resume_command, config):
	print(step)

