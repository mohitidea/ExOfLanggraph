from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import HumanMessage

from langchain_aws import ChatBedrockConverse
#"cohere.command-r-plus-v1:0",
#llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)
llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=200)

class AgentState(MessagesState):
	pass

def chat_node(state: AgentState):
	# Send full message history to the LLM
	response = llm.invoke(state["messages"])
	
	#  Return ONLY the new message
	# LangGraph auto-appends it to state["messages"]
	
	return {"messages": [response]}


graph = StateGraph(AgentState)
graph.add_node("chat", chat_node)
graph.set_entry_point("chat")
app = graph.compile()
graph.compile()


result = app.invoke({ "messages": [HumanMessage(content="Explain MessagesState in one sentence.")] })
for msg in result["messages"]:
	print(type(msg).name, ":", msg.content)


from rich import print
print(result)
