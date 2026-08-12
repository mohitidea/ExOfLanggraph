from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# Add Messages Reducer 
class WorkflowState(TypedDict):
    # 'add_messages' ensures new messages are appended to the list
    # or updated if the message IDs match.
    messages: Annotated[list[BaseMessage], add_messages]


#Messages State Reducer
from langgraph.graph import MessagesState
class AgentState(MessagesState):
	doc:str
