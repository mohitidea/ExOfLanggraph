import streamlit as st
from langchain_aws import ChatBedrockConverse
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
llm = ChatBedrockConverse(model=MODEL_ID, temperature=0.2, region_name="us-east-1")
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! Ask me anything ðŸ™‚"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_text = st.chat_input("Type your message...")

lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
for m in st.session_state.messages:
   if m["role"] == "user":
      lc_messages.append(HumanMessage(content=m["content"]))
   elif m["role"] == "assistant":
       lc_messages.append(AIMessage(content=m["content"]))

ai_msg = llm.invoke(lc_messages)
reply = ai_msg.content

st.markdown(reply)
st.session_state.messages.append({"role": "assistant", "content": reply})




