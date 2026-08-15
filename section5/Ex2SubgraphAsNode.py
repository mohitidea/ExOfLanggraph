from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START, END
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage

llm = ChatBedrockConverse(
   model_id="amazon.nova-lite-v1:0",
   region_name="us-east-1",
    temperature=0.7,
    max_tokens=100
)

# -----------------------------
# Subgraph State (SHARED keys)
# Note: These keys are also present in the parent state.
# -----------------------------
class DiscountState(TypedDict):
    purchase_amount: float
    discount: float


def discount_calculation(state: DiscountState):
    amt = state["purchase_amount"]
    if amt >= 1000:
        discount = 20
    elif amt >= 500:
        discount = 10
    elif amt >= 200:
        discount = 5
    else:
        discount = 0
    # Writes back to the SAME state key used by parent: "discount"
    return {"discount": discount}



# Build the subgraph
subgraph_builder = StateGraph(DiscountState)
subgraph_builder.add_node("discount_calculation", discount_calculation)
subgraph_builder.add_edge(START, "discount_calculation")
subgraph_builder.add_edge("discount_calculation", END)
discount_subgraph = subgraph_builder.compile()
discount_subgraph


# -----------------------------
# Parent State (includes shared keys)
# -----------------------------
class CustomerState(TypedDict):
    name: str
    purchase_amount: float
    discount: float
    discount_report: str


def generate_discount_report(state: CustomerState):
    #  No subgraph.invoke() here
    # The subgraph already computed "discount" and wrote it into shared state.
    discount = state["discount"]
    # Basic report
    report = f"{state['name']} is eligible for a {discount}% discount on their purchase."
    # Personalized message via LLM
    prompt = (
       f"Generate a short, friendly personalized message for {state['name']} "
        f"who received a {discount}% discount."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    report += " " + response.content
    return {"discount_report": report}

# Build the parent graph
parent_builder = StateGraph(CustomerState)
#  Add the compiled subgraph directly as a node (no wrapper needed)
parent_builder.add_node("apply_discount", discount_subgraph)
# Normal node (uses discount written by subgraph)
parent_builder.add_node("generate_discount_report", generate_discount_report)
# Flow: START -> subgraph(node) -> report node -> END
parent_builder.add_edge(START, "apply_discount")
parent_builder.add_edge("apply_discount", "generate_discount_report")
parent_builder.add_edge("generate_discount_report", END)
discount_report_graph = parent_builder.compile()
discount_report_graph

# -----------------------------
# Sample invocation
# -----------------------------
if __name__ == "__main__":
    customer_state = {
       "name": "Raj",
       "purchase_amount": 750,
       "discount": 0,       # initial placeholder (will be updated by subgraph)
       "discount_report": ""  # initial placeholder (will be filled in parent node)
    }
    result = discount_report_graph.invoke(customer_state)
    print(result["discount_report"])
