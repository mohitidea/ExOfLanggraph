import time
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.store.base import BaseStore
from langgraph.graph import START, MessagesState, StateGraph, END
from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import InMemorySaver


#  Bedrock LLM Setup 
model = ChatBedrockConverse(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0", 
    region_name="us-east-1",  
    temperature=0.4,
    max_tokens=100
)


# Define the Chatbot Interaction 
def chat(state: MessagesState) -> dict:
    """
    Handles the user message, processes it, and invokes the Bedrock LLM to generate a response.
    """
    # system prompt -
    system_prompt = (
        "You are a helpful, ethical, and conservative **Financial Advisor AI**. "
        "Use the user's message to provide professional, financial advice. "
        "Keep your answers focused on financial well-being."
        "You can refer previous conversations to answer user queries if required."
    )
    response = model.invoke(
        [
            {"role": "system", "content": system_prompt},
            *state["messages"],  # Include the user message in the context
        ]
    )
    return {"messages": [response]}

#  Build the Graph ---
builder = StateGraph(MessagesState)
builder.add_node("chat_node", chat)  # Add chat logic to the graph
builder.add_edge(START, "chat_node")  # Connect start to the chat node
builder.add_edge("chat_node", END)    # Connect chat node to the end
# Compile the Graph with InMemorySaver ---
graph = builder.compile(checkpointer=InMemorySaver())  # Use InMemorySaver for state checkpointing
builder.compile(checkpointer=InMemorySaver())


from rich import print
while True:
    # Get user input and thread_id
    user_input = input("User: ")
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Chatbot has ended.")
        break
    thread_id = input("Thread ID: ")
    # Create the message and config for graph.stream
    messages = [{"role": "user", "content": user_input}]  # Ensure the first message is from the user
    config = {"configurable": {"thread_id": thread_id}}  # Config for thread_id
    # Using graph.stream with the correct structure
    for step in graph.stream({"messages": messages}, config=config):
        # Print AI's response (assuming step contains the response)
        print(step)  # Get the AI's response content
