from typing_extensions import TypedDict
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END

class OverallState(TypedDict):
	task_progress: int # Overall progress (in percentage)
	
class IntermediateState(TypedDict):
	temp_progress: int # Temporary progress used during calculations


def node_1(state: OverallState) -> IntermediateState:
	print("---Node 1: Calculating intermediate progress---")
	# Add 10% progress based on the current overall progress
	return {"temp_progress": state['task_progress'] + 10}


def node_2(state: IntermediateState) -> OverallState:
	print("---Node 2: Updating overall progress---")
	# Use intermediate data to update overall progress
	return {"task_progress": state['temp_progress']}

builder = StateGraph(OverallState) # Define the overall state for the graph
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)

builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", END)

graph = builder.compile()
display(Image(graph.get_graph().draw_mermaid_png()))

result = graph.invoke({"task_progress": 40}) # Starting progress is 40%
print(f"Final Task Progress: {result['task_progress']}%")

