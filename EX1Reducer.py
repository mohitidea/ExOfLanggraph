from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class WithReducerState(TypedDict):
	"""The 'log' field is annotated with operator.add to APPEND lists."""
	log: Annotated[List[str], operator.add]

def node_1_with_reducer(state: WithReducerState) -> WithReducerState:
	log_entry = "Node 1 contribution."
	print(f"-> Node 1 runs. State returned: {log_entry}")
	# Returns a list containing its single contribution
	return {"log": [log_entry]}
	
def node_2_with_reducer(state: WithReducerState) -> WithReducerState:
	# State['log'] here is ['Node 1 contribution.']
	log_entry = "Node 2 contribution."
	print(f"-> Node 2 runs. State returned: {log_entry}")
	# Returns a new list containing its single contribution
	return {"log": [log_entry]}

workflow_with_reducer = StateGraph(WithReducerState)
workflow_with_reducer.add_node("node_1", node_1_with_reducer)
workflow_with_reducer.add_node("node_2", node_2_with_reducer)
workflow_with_reducer.set_entry_point("node_1")
workflow_with_reducer.add_edge("node_1", "node_2")
workflow_with_reducer.add_edge("node_2", END)
app_with_reducer = workflow_with_reducer.compile()
app_with_reducer

result_with_reducer = app_with_reducer.invoke({})
print("\n--- Final State (WITH Reducer) ---")
print(f"Log: {result_with_reducer['log']}")
