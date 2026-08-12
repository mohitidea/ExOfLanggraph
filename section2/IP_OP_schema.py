from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

class InputState(TypedDict):
	query: str
class OutputState(TypedDict):
	answer: str
class OverallState(TypedDict):
	question: str
	setup: str
	punchline: str
	notes: str


def thinking_node(state: InputState) -> dict:
	"""Generate the joke setup and punchline."""
	q = state.get("query", "")
	print(q)
	# Simple logic to pick a joke based on the query
	if "chicken" in q.lower():
		setup = "Why did the chicken cross the road?"
		punchline = "To get to the other side!"
	else:
		setup = "Why don't programmers like nature?"
		punchline = "Too many bugs."
	return {
    	"setup": setup,
    	"punchline": punchline,
    	"notes": "Generated a joke based on the user's query."
    	}

def answer_node(state: OverallState) -> OutputState:
	"""Produce the final formatted response."""
	return { "answer": f"{state['setup']}\n{state['punchline']}" }


graph = StateGraph(OverallState,input_schema=InputState,output_schema=OutputState)
graph.add_node("thinking_node", thinking_node)
graph.add_node("answer_node", answer_node)
graph.add_edge(START, "thinking_node")
graph.add_edge("thinking_node", "answer_node")
graph.add_edge("answer_node", END)
graph = graph.compile()

display(Image(graph.get_graph().draw_mermaid_png()))
res1=graph.invoke({"query": "Tell me a joke on chicken "})
print(res1)
res2=graph.invoke({"query": "Tell me a joke on programmers "})
print(res2)




