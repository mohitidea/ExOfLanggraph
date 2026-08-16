import streamlit as st
st.title("Hello World-Streamlit UI")
st.write("This is a minimal Streamlit app.")
name = st.text_input("Enter your name")
if st.button("Say Hello"):
    if name.strip():
        st.success(f"Hello, {name} ðŸ‘‹")
    else:
        st.warning("Please enter your name to continue")
