import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

st.set_page_config(page_title="Hello LLM", layout="centered")
st.title("Hello World-Streamlit + LLM ")

# --- Simple configuration (keep it minimal for a course hello-world) ---

SYSTEM_PROMPT = "You are a helpful assistant. Keep answers brief."

from langchain_aws import ChatBedrockConverse

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0" 
llm = ChatBedrockConverse(
    model=MODEL_ID,
    temperature=0.2,
    region_name="us-east-1"
)


# --- Session state for chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me anything 🙂"}
    ]

# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat input
user_text = st.chat_input("Type your message...")
if user_text:
    # show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Build LangChain message list from session history (simple conversion)
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in st.session_state.messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))

    # Call the model
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_msg = llm.invoke(lc_messages)   # returns an AIMessage
            reply = ai_msg.content

        st.markdown(reply)

    # save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})