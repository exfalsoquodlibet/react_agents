import streamlit as st
from openai_react_agents_from_scratch.react_openai_native import react_agent

st.set_page_config(layout="wide")

st.title("ReAct Agent Chatbot")

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'steps' not in st.session_state:
    st.session_state.steps = []
if 'waiting_for_user_input' not in st.session_state:
    st.session_state.waiting_for_user_input = False
if 'user_input_question' not in st.session_state:
    st.session_state.user_input_question = None
if 'user_response' not in st.session_state:
    st.session_state.user_response = None
if 'pending_response' not in st.session_state:
    st.session_state.pending_response = False

# Function to handle user input from the Ask User step
def get_user_input(question):
    # Set state indicating the system is waiting for user input
    st.session_state.waiting_for_user_input = True
    st.session_state.user_input_question = question
    
    # Add the agent's question to the chat messages so it appears as an answer from the assistant
    st.session_state.messages.append({"role": "assistant", "content": question})
    st.experimental_rerun()  # Trigger a rerun to update the chat interface

# Function to process the ReAct agent's main question and interactions
def process_agent(prompt):
    # Create a combined history of the conversation up to this point
    combined_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
    
    # Append the new user prompt to maintain the complete history
    combined_prompt += f"\nuser: {prompt}"
    
    # Call the react_agent with the complete conversation context
    final_answer, steps = react_agent(combined_prompt, user_input_func=get_user_input)
    
    # Update session state steps
    st.session_state.steps = steps

    # Append all steps including final answer to the chat messages
    # for step_type, step_content in steps:
    #     if step_type == "Final Answer":
    #         # Ensure the Final Answer is added to chat messages (for Column 1)
    #         st.session_state.messages.append({"role": "assistant", "content": step_content})

    if final_answer:
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
        with st.chat_message("assistant"):
            st.markdown(final_answer)
        st.experimental_rerun()  # Trigger a rerun to update the chat interface

    # Reset states after processing
    st.session_state.pending_response = False  # Ensure no pending response
    st.session_state.waiting_for_user_input = False  # Reset input wait flag

# Create two columns
col1, col2 = st.columns(2)

# Left column for chat interface
with col1:
    st.header("Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])

    # Handling primary user input
    if not st.session_state.waiting_for_user_input and not st.session_state.pending_response:
        user_prompt = st.chat_input("What would you like to know?")
        if user_prompt:
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            st.session_state.pending_response = True  # Indicate a response is being processed
            process_agent(user_prompt)
    
    # Handling Ask User step
    elif st.session_state.waiting_for_user_input:
        # Display the agent's question to the user
        # st.write(f"Agent asks: {st.session_state.user_input_question}")
        
        # Allow the user to provide their response using Enter key
        user_response = st.text_input("Your response:", key="user_response_input", on_change=lambda: st.session_state.update({"user_response": st.session_state.user_response_input}))
        
        # Automatically process the agent's question when the Enter key is pressed
        if user_response:
            st.session_state.messages.append({"role": "user", "content": user_response})
            st.session_state.user_response = user_response
            st.session_state.waiting_for_user_input = False  # Mark that the user has responded
            st.session_state.pending_response = True  # Re-enable processing for the agent
            process_agent(user_response)

# Right column for showing the thought process
with col2:
    st.header("Agent's reasoning process")

    # for step_type, step_content in st.session_state.steps:
    #     st.markdown(f"**{step_type}:**")
    #     st.markdown(step_content)
    
    for step_type, step_content in st.session_state.steps:
        with st.expander(f"{step_type}", expanded=True):
            st.text(step_content)
