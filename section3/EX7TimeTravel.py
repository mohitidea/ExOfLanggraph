import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrockConverse

class State(TypedDict):
	topic: NotRequired[str]
	jingle: NotRequired[str]
#Initialize the chat model
model = ChatBedrockConverse(
	model_id="amazon.nova-lite-v1:0",
	region_name="us-east-1",
	temperature=0.4,
	max_tokens=50
	)
def generate_topic(state: State):
	"""LLM call to generate a topic for the jingle"""
	msg = model.invoke("Give me a fun and catchy topic for a jingle")
	return {"topic": msg.content}
def write_jingle(state: State):
	"""LLM call to write a jingle based on the topic"""
	msg = model.invoke(f"Write a short, catchy jingle about {state['topic']}")
	return {"jingle": msg.content}


#Build workflow
workflow = StateGraph(State)
#Add nodes
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_jingle", write_jingle)
#Add edges to connect nodes
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_jingle")
workflow.add_edge("write_jingle", END)
#Compile the workflow
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
graph


#Configuration for the execution
config = { "configurable": { "thread_id": uuid.uuid4(),}}
#Start the graph with an empty initial state
state = graph.invoke({}, config)

#The states are returned in reverse chronological order, so we print the history
states = list(graph.get_state_history(config))
#Print the history of states (in chronological order)
for state in states:
	print(state.next)
	#print(state.config["configurable"]["checkpoint_id"])
	print() # This is the state before last (states are listed in chronological order)


before_jingle = next(s for s in states if "write_jingle" in s.next)
print(f"Replaying from topic: {before_jingle.values.get('topic')}")
#Re-execute from that point
#Passing None tells the graph: "Don't add new input, just resume from this config"
replay_result = graph.invoke(None, before_jingle.config)
#Validation
print("New Jingle Generated:", replay_result.get("jingle"))


#The states are returned in reverse chronological order, so we print the history
states = list(graph.get_state_history(config))
#Print the history of states (in chronological order)
for state in states:
	print(state.next)
	print()


selected_state = states[1]
print("Selected State Topic:", selected_state[0])
#print("Selected State Values:", selected_state.values)
#Update state with a new topic
new_config = graph.update_state(selected_state.config, values={"topic": "first day at Infosys"})
print("New Config with Updated Topic:", new_config)
#Re-run the graph with the updated state
graph.invoke(None, new_config)

#The states are returned in reverse chronological order, so we print the history
states = list(graph.get_state_history(config))
#Print the history of states (in chronological order)
for state in states:
	print(state.next)
	print()
