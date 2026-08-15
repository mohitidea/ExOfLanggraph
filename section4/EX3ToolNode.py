from langchain_aws import ChatBedrockConverse
from langchain_experimental.tools import PythonREPLTool
from typing import TypedDict, Annotated, List
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.graph import START, END, StateGraph
from rich import print
import operator

#llm
llm = ChatBedrockConverse(model_id='cohere.command-r-plus-v1:0', temperature = 0.5, region_name = 'us-east-1', max_tokens = 250)
llm.invoke('hi')

#Tool 1
python_tool = PythonREPLTool()


#Tool 2
search_engine = DuckDuckGoSearchRun()


#Tool 3
@tool
def math_tool(operator: str, a: float, b:float) -> float:
	"""This tool perform the arithmetic calculation when the tools is called"""
	if operator == 'add':
		return a + b
	elif operator == 'subtraction':
		return a-b
	elif operator == 'multiplication':
		return a * b
	else:
		return a/b if b!=0 else "Error: Division by 0"


tools = [python_tool, search_engine, math_tool]
model_with_tools = llm.bind_tools(tools)

tool_names = {tool.name:tool for tool in tools}
print(tool_names)


res = model_with_tools.invoke("Multiply 10 and 20")
print(res)
print(res.tool_calls)

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
class AgentState(TypedDict):
	messages: Annotated[List[BaseMessage], operator.add]

def llm_node(state:AgentState):
	"""
	Node executes the response either by using the given
	tools at its disposal or from its pre existing knowledge
	"""
	response = model_with_tools.invoke(state['messages'])
	return {'messages': [response]}


def custom_tool_node(state:AgentState): 
    last_message = state['messages'][-1] 
    if not last_message.tool_calls: 
        return {} 
    result = [] 
    for tool_call in last_message.tool_calls: 
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        selected_tool = tool_names.get(tool_name) 
        tool_result = selected_tool.invoke(tool_args)
        result.append(ToolMessage(content = tool_result, tool_call_id = tool_call['id']))
    return {'messages':result}

def should_continue(state:AgentState): 
    last_message = state['messages'][-1] 
    if last_message.tool_calls: 
        return "tool" 
    return END


builder = StateGraph(AgentState) 
builder.add_node("Agent", llm_node) 
builder.add_node("tool", custom_tool_node) 
builder.add_conditional_edges("Agent",should_continue, 
                              { 
                                'tool':'tool', 
                                END:END}) 
builder.add_edge(START, "Agent") 
builder.add_edge("Agent", END) 
builder.add_edge("tool","Agent") 
graph = builder.compile()
graph

from rich import print
print(graph.invoke({'messages':['What is the current news in the world of AI ? provide the answer in 1-2 lines.']}))

print(graph.invoke({'messages':['Write a python program to generate fibonacci series of 10 numbers']}))

from langgraph.prebuilt import ToolNode, tools_condition
tools = [math_tool, search_engine, python_tool]
model_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools,handle_tool_errors=True)
builder1= StateGraph(AgentState)
builder1.add_node("Agent", llm_node)
builder1.add_node("tools", tool_node)
builder1.add_conditional_edges("Agent",tools_condition,)
builder1.add_edge(START, "Agent")
builder1.add_edge("tools","Agent")
builder1.add_edge("Agent", END)
graph1 = builder1.compile()
graph1

res = graph1.invoke({'messages':['When I was 6 years my sister was half my age. Now I am 70 years old, how old is my sister']})
print(res)

