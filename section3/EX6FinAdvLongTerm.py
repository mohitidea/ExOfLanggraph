# It stores user‑specific financial details and chat messages in 
# long‑term memory, retrieves the most relevant memories using semantic 
# search, and uses them to generate personalized financial advice with 
# an LLM. The entire flow is orchestrated using a LangGraph state graph.
import time  # Used to generate unique IDs for memory entries
# Message types used by LangGraph
from langchain_core.messages import HumanMessage, AIMessage
# Base interfaces for memory storage
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
# Core LangGraph components
from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
#  Configure the LLM and Embedding Model
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings


# Configure the chat model (LLM) using Amazon Bedrock
model = ChatBedrockConverse(
    model_id="amazon.nova-lite-v1:0",
    region_name="us-east-1",
    temperature=0.4,   # Lower temperature for safer, conservative responses
    max_tokens=50      # Keep responses concise
)
# Configure embeddings for semantic memory search
embeddings = BedrockEmbeddings(model_id="cohere.embed-english-v3")

# Create an in-memory store with vector indexing enabled
store = InMemoryStore(
    index={
        "embed": embeddings,  # Embedding function
        "dims": 1536          # Embedding vector dimensions
    }
)
# Static user ID for this demo
USER_ID = "user_123"
# Store some pre-existing financial memories for the user
store.put((USER_ID, "memories"), "1", {
    "text": "I am generally risk-averse and prefer stability."
})
store.put((USER_ID, "memories"), "2", {
    "text": "I am an engineer and I earn $10000 per year."
})
store.put((USER_ID, "memories"), "3", {
    "text": "My goal is to retire in 10 years."
})





def chat(state: MessagesState, *, store: BaseStore) -> dict:
    """
    Stores the latest user message, retrieves relevant memories,
    and invokes the LLM with personalized context.
    """
    # Store the latest user message as new memory
 
    latest_user_message = state["messages"][-1]
    # Generate a unique ID using timestamp
    new_id = str(int(time.time() * 1000))
    # Save the user's latest message to memory
    store.put(
        (USER_ID, "memories"),       # Namespace: user + memory type
        new_id,                      # Unique memory ID
        {"text": latest_user_message.content}
    )
    # Retrieve relevant past memories
    # Perform semantic search using the latest message as query
    items = store.search(
        (USER_ID, "memories"),
        query=latest_user_message.content,
        limit=3
    )
    # Convert retrieved memories into prompt text
    memories = "\n".join(item.value["text"] for item in items)
    memories_prompt = (
        f"\n## User Context / Memories\n{memories}"
        if memories else ""
    )
    # Invoke the LLM with personalized system prompt
   
    system_prompt = (
        "You are a helpful, ethical, and conservative Financial Advisor AI. "
        "Use the user's past memories to personalize your advice. "
        "Focus on long-term financial well-being and stability."
        f"{memories_prompt}"
    )
    # Call the model with system prompt + conversation history
    response = model.invoke(
        [
            {"role": "system", "content": system_prompt},
            *state["messages"],
        ]
    )
    return {"messages": [response]}


# Create a graph with message-based state
builder = StateGraph(MessagesState)
# Add the chat node
builder.add_node("chat_node", chat)
# Define graph flow
builder.add_edge(START, "chat_node")
builder.add_edge("chat_node", END)  # Single-step flow
# Compile the graph with memory checkpointing and store
graph = builder.compile(
    checkpointer=InMemorySaver(),
    store=store
)
print(graph)


print("--- STARTING FINANCIAL CHATBOT Conversation With Thread 1---")
while True:
# --- First Interaction ---
   user_input = input("Your Query:")
   print(f"\nUser : {user_input}")
   if(user_input=='exit'):
        break
# This message will be processed AND stored.
   for message in graph.stream( input={"messages": [HumanMessage(content=user_input)]},
                                config={'configurable':{'thread_id':1}},stream_mode="values",):
        if isinstance(message["messages"][-1], AIMessage):
           print("AI Advisor :", message["messages"][-1].content)
print("\n--- END OF CHATBOT ---")


print("--- STARTING FINANCIAL CHATBOT Conversation With Thread 2 ---")
while True:
# --- First Interaction With Thread-2 ---
    user_input = input("Your Query:")
    print(f"\nUser : {user_input}")
    if(user_input=='exit'):
        break
#This message will be processed AND stored.
    for message in graph.stream( input={"messages": [HumanMessage(content=user_input)]},
                                config={'configurable':{'thread_id':2}},stream_mode="values",):
        
        if isinstance(message["messages"][-1], AIMessage):
            
            print("AI Advisor :", message["messages"][-1].content)
    print("\n--- END OF CHATBOT ---")


from rich import print
def print_user_memories(store, user_id):
# Retrieve all memories for the given user_id
	items = store.search((user_id, "memories"), query="What is my goal in next few years?", limit=2)
	print(items)# Set limit to an appropriate number if needed
	
#Call the function to print all stored memories for USER_ID
print_user_memories(store, USER_ID)



