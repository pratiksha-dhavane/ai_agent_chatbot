import streamlit as st
from ai_agent.agents import run_agent

import os
import sys
sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="AI agent", layout="centered")
st.title("Ask anything")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# chat input
user_input = st.chat_input("Ask a question:")

if user_input:
    st.session_state.messages.append(
        {
            "role" : "user", "content" : user_input
        }
    )
    with st.chat_message("user"):
        st.write(user_input)

    # agent response 
    with st.chat_message("assistant"):
        with st.spinner("Thinking...."):
            try:
                answer = run_agent(user_input)
                st.write(answer)

                st.session_state.messages.append(
                    {
                        "role" : "assistant", "content" : answer
                    }
                )
            except Exception as e:
                error_msg = f"Agent failed: {e}"
                st.error(error_msg)

                st.session_state.messages.append(
                    {
                        "role" : "assistant", "content" : error_msg
                    }
                )
