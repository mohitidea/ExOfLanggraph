from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START

class SubgraphState(TypedDict):
	greet: str


def subgraph_node_1(state: SubgraphState):
	return {"greet": "Hi! " + state["greet"]}


subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node("subgraph_node_1", subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()
subgraph


class State(TypedDict):
	player: str

    
def call_subgraph(state: State):
	subgraph_output = subgraph.invoke({"greet": state["player"]})
	return {"player": subgraph_output["greet"]}


builder = StateGraph(State)
builder.add_node("node_1", call_subgraph)
builder.add_edge(START, "node_1")
graph = builder.compile()
graph


input_state = {"player": "Sachin"}
output_state = graph.invoke(input_state)
print("Input:", input_state)
print("Output:", output_state)



