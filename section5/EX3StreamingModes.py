from typing_extensions import TypedDict
from typing import List, Dict, Any
import re
from langgraph.graph.state import StateGraph, START, END
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
# -----------------------------
# Demo Retail Catalog
# -----------------------------
CATALOG = [
    {"name": "Nova Earbuds", "category": "earbuds", "price": 1999, "rating": 4.4},
    {"name": "BassMax Earbuds", "category": "earbuds", "price": 2999, "rating": 4.6},
    {"name": "FitBand Pro", "category": "fitness", "price": 3499, "rating": 4.5},
    {"name": "SmartWatch Mini", "category": "watch", "price": 3999, "rating": 4.3},
]


# -----------------------------
# LLM setup (AWS Bedrock)
# -----------------------------
llm = ChatBedrockConverse(
   model_id="amazon.nova-lite-v1:0",
   region_name="us-east-1",
    temperature=0.7,
    max_tokens=100
)

# -----------------------------
# Graph State
# -----------------------------
class RetailState(TypedDict, total=False):
    query: str
    category: str
    budget: int
    products: List[Dict[str, Any]]
    recommendation: str


# -----------------------------
# Agent 1: Intent Agent
# -----------------------------
def intent_agent(state: RetailState) -> RetailState:
    q = state["query"].lower()
    category = "earbuds" if "earbud" in q else "watch"
    match = re.search(r"(\d{3,7})", q.replace(",", ""))
    budget = int(match.group(1)) if match else 3000
    return {"category": category, "budget": budget}


# -----------------------------
# Agent 2: Catalog Agent
# -----------------------------
def catalog_agent(state: RetailState) -> RetailState:
    results = [
        p for p in CATALOG
        if p["category"] == state["category"]
        and p["price"] <= state["budget"]
    ]
    results.sort(key=lambda x: x["rating"], reverse=True)
    return {"products": results}


# -----------------------------
# Agent 3: Advisor Agent (LLM)
# -----------------------------
def advisor_agent(state: RetailState) -> RetailState:
    if not state["products"]:
        return {"recommendation": "No suitable products found."}
    items = "\n".join(
        f"- {p['name']} (â‚¹{p['price']}, rating {p['rating']})"
        for p in state["products"]
    )
    prompt = (
        f"User query: {state['query']}\n"
       f"Products:\n{items}\n\n"
       "Recommend the best option in 2 short sentences."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"recommendation": response.content}


# -----------------------------
# Build Graph
# -----------------------------
graph = (
   StateGraph(RetailState)
   .add_node("intent_agent", intent_agent)
   .add_node("catalog_agent", catalog_agent)
   .add_node("advisor_agent", advisor_agent)
    .add_edge(START, "intent_agent")
   .add_edge("intent_agent", "catalog_agent")
   .add_edge("catalog_agent", "advisor_agent")
   .add_edge("advisor_agent", END)
    .compile()
)
graph

for chunk in graph.stream(
    {"query": "Suggest earbuds under 3000"},
    stream_mode="values",
    version="v2",
):
    if chunk["type"] == "values":
        print(chunk["data"])


for chunk in graph.stream(
    {"query": "Suggest earbuds under 3000"},
    stream_mode="updates",
    version="v2",
):
    if chunk["type"] == "updates":
        print(chunk["data"])


for chunk in graph.stream(
    {"query": "Suggest earbuds under 3000"},
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content:
            print(msg.content, end="", flush=True)


for chunk in graph.stream(
    {"query": "Suggest earbuds under 3000"},
    stream_mode="debug",
    version="v2",
):
    if chunk["type"] == "debug":
        print(chunk["data"])



