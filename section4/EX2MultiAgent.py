from langgraph.prebuilt import create_agent
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
import os
# ---------------------------
# AWS Bedrock LLM Setup
# ---------------------------
#llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)
llm = ChatBedrockConverse(model_id="cohere.command-r-plus-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)
llm.invoke("Hi")

from langchain.tools import tool
from langchain.agents import create_agent
# ============================================================================
# Define low-level API tools
# ============================================================================
@tool
def search_flights(origin: str, destination: str, date: str) -> list[dict]:
   """Return stubbed list of flights."""
   return [
       {"flight": "SG101", "time": "08:00", "price": 350},
       {"flight": "SG202", "time": "11:00", "price": 300},
       {"flight": "SG303", "time": "18:00", "price": 420},
   ]
@tool
def book_flight(flight_id: str, passenger: str) -> str:
   """Book a flight."""
   return f"Flight {flight_id} booked for {passenger}"
@tool
def search_hotels(city: str, checkin: str, nights: int) -> list[dict]:
   """Return stubbed list of hotels."""
   return [
       {"name": "Marina Bay Hotel", "price": 180},
       {"name": "City Center Inn", "price": 120},
       {"name": "Harbor View Suites", "price": 150},
   ]
@tool
def book_hotel(hotel_name: str, nights: int, guest: str) -> str:
   """Book a hotel."""
   return f"Hotel '{hotel_name}' booked for {guest} for {nights} nights"


# ============================================================================
# Create specialized sub-agents
# ============================================================================
# Flight Agent ---------------------------------------------------------------
flight_agent = create_agent(
   llm,
   tools=[search_flights, book_flight],
   system_prompt=(
       "You are a flight booking assistant. "
       "Parse travel requests (origin, destination, dates). "
       "Use search_flights to get flight options. "
       "Choose a good option and use book_flight. "
       "Always confirm the final booked flight."
   )
)
# Hotel Agent ---------------------------------------------------------------
hotel_agent = create_agent(
   llm,
   tools=[search_hotels, book_hotel],
   system_prompt=(
       "You are a hotel booking assistant. "
       "Parse lodging requests (city, dates, nights). "
       "Use search_hotels to get options. "
       "Choose a suitable hotel and use book_hotel. "
       "Always confirm what was booked."
   )
)

# ============================================================================
# Create the supervisor agent
# ============================================================================
supervisor_agent = create_agent(
   llm,
   tools=[flight_agent, hotel_agent],
   system_prompt=(
       "You are a travel planning assistant. "
       "You can book flights and hotels. "
       "Break down requests and call the appropriate tools. "
       "For multi-step tasks, call multiple tools sequentially."
   )
)
supervisor_agent

# Test Run 1
if __name__ == "__main__":
   user_request = (
       "Plan a 3-day trip to Singapore next month. "
       "Book a morning flight from Mumbai and reserve a hotel near Marina Bay."
   )
   print("\nUser Request:\n", user_request)
   print("\n" + "="*80 + "\n")
   for step in supervisor_agent.stream(
       {"messages": [{"role": "user", "content": user_request}]}
   ):
       for update in step.values():
           for message in update.get("messages", []):
               message.pretty_print()


# Test Run 2
# ============================================================================
from rich import print
if __name__ == "__main__":
   user_request = (
       "Plan a 3-day trip to Malysia next month. "
       "Book a morning flight from Bangalore and reserve a hotel near City center."
   )
   print("\nUser Request:\n", user_request)
   print("\n" + "="*80 + "\n")
   for step in supervisor_agent.stream(
       {"messages": [{"role": "user", "content": user_request}]}
   ):
       for update in step.values():
           for message in update.get("messages", []):
               message.pretty_print()

