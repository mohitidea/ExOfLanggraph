from langgraph.store.memory import InMemoryStore
# 
def embed(texts: list[str]) -> list[list[float]]:
    return [[1.0, 2.0] * len(texts)]
# Create the store with semantic search enabled
store = InMemoryStore(index={"embed": embed, "dims": 2})

# Define namespace and key
namespace = ("user_123", "preferences") #best practice to seperate different classes of storage you want to have
memory_key = "user_profile"
# Store long-term memory
store.put(
    namespace,
    memory_key,
    {
        "name": "USER-1",
        "preferences": ["short responses", "English", "Python"]
    }
)

# Retrieve memory
retrieved = store.get(namespace, memory_key)
print("Retrieved Memory:", retrieved)
# Semantic search example
results = store.search(namespace, query="language preference", limit=1)
print("Semantic Search Result:", results)

