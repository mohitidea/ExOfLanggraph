from typing import TypedDict,List
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
#llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)
llm = ChatBedrockConverse(model_id="cohere.command-r-plus-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)

llm.invoke("Hi").content

class AgentState(TypedDict):
	messages:List[HumanMessage]


def process(state:AgentState)->AgentState:
	"""LLM as an Agent"""
	response =llm.invoke(state['messages'])
	print(f'AI Message:{response.content}')
	state['messages']=response.content
	return state

graph =StateGraph(AgentState)
graph.add_node('process',process)
graph.add_edge(START,'process')
graph.add_edge('process',END)
graph.compile()

app=graph.compile()
user_input =input("Your Message:")
while user_input!='exit':
	response=app.invoke({'messages': [HumanMessage(content=user_input)]})
	print(response)
	user_input=input("Your Message:")
