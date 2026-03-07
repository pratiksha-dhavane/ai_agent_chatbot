import streamlit as st
from ai_agent.agents import run_agent, update_summary

import os
import sys
sys.path.append(os.path.dirname(__file__))
max_turns = 4

st.set_page_config(page_title="AI agent", layout="centered")
st.title("Ask anything")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Adding short term memory
if "memory" not in st.session_state:
    st.session_state.memory = {
        "summary": "",
        "recent_turns": []
    }

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

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
                answer = run_agent(user_input=user_input,
                                   memory=st.session_state.memory)
                st.write(answer)

                st.session_state.messages.append(
                    {
                        "role" : "assistant", "content" : answer
                    }
                )

                st.session_state.turn_count += 1

                st.session_state.memory["recent_turns"].insert(0,{
                    "user_input" : user_input,
                    "assistant" : answer
                })

                if len(st.session_state.memory["recent_turns"]) > max_turns:
                    st.session_state.memory["recent_turns"] = st.session_state.memory["recent_turns"][:max_turns] 

                if st.session_state.turn_count % max_turns == 0:
                    new_summary = update_summary(
                        existing_summary = st.session_state.memory["summary"],
                        recent_turns = st.session_state.memory["recent_turns"]
                    )

                    st.session_state.memory["summary"] = new_summary

            except Exception as e:
                error_msg = f"Agent failed: {e}"
                st.error(error_msg)

                st.session_state.messages.append(
                    {
                        "role" : "assistant", "content" : error_msg
                    }
                )
