from typing import Literal
from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from langchain_aws import ChatBedrockConverse, BedrockEmbeddings #"cohere.command-r-plus-v1:0",
#llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=50)
llm = ChatBedrockConverse(model_id="amazon.nova-lite-v1:0", region_name="us-east-1", temperature=0.5, max_tokens=200)


@tool
def get_leave_policy(query: str) -> str:
	"""Returns company leave policy details."""
	query = query.lower()
	if "sick" in query:
		return "Employees get 5 sick leave days per year."
	elif "casual" in query:
		return "Employees get 20 casual leave days annually."
	elif "maternity" in query:
		return "Maternity leave is 26 weeks."
	elif "paternity" in query:
		return "Paternity leave is 5 days."
	return "Please check HR portal for more details."


tools = [get_leave_policy]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = llm.bind_tools(tools)


def call_llm(state: MessagesState):
	"""This node gets the state messages and invokes the llm for response"""
	print("STATE MESSAGES:", state["messages"])
	response = model_with_tools.invoke(state["messages"])
	return {"messages": [response]}


def call_tool(state: MessagesState):
	""" This node detects the tool call message from the LLM's response and calls the intended tool and returns the response"""
	last_message = state["messages"][-1]
	tool_call = last_message.tool_calls[0]   
	tool = tools_by_name[tool_call["name"]]
	tool_response = tool.invoke(tool_call["args"])
	return {
    	"messages": [
       		ToolMessage(
            	content=tool_response,
            	tool_call_id=tool_call["id"]
        	)
    	]
	}


def should_continue(state: MessagesState) -> Literal["tool", END]:
	""" This is a conditional logic node,it decides whether LLM node needs a tool_call or to generate the final response """
	last_message = state["messages"][-1]
	if last_message.tool_calls:
		return "tool"
	return END


builder = StateGraph(MessagesState)
builder.add_node("llm", call_llm)
builder.add_node("tool", call_tool)
builder.set_entry_point("llm")
builder.add_conditional_edges( "llm",
	should_continue,
	{
		"tool": "tool",
		END: END
	}
	)
builder.add_edge("tool", "llm")
graph = builder.compile()
builder.compile()


from rich import print
result = graph.invoke({ "messages": [ HumanMessage(content="How many sick and maternity leave weeks do employees get?") ] })
print("\nFINAL ANSWER:")
print(result["messages"][-1].content)

