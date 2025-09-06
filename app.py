"""
Streamlit Web UI for What To Do Tomorrow Agent
"""
import streamlit as st
import asyncio
import os
from agent import WhatToDoAgent

# Set page config
st.set_page_config(
    page_title="What To Do Tomorrow?",
    page_icon="🤖",
    layout="centered"
)

# Title and description
st.title("🤖 What To Do Tomorrow?")
st.markdown("Ask me what activities you can do in any city, and I'll check the weather and recommend the perfect activities!")

# Examples
with st.expander("💡 Try these example questions"):
    st.markdown("""
    - "What can I do tomorrow in Sydney?"
    - "What activities are available this weekend in Melbourne?"
    - "What can I do next Monday in Brisbane?"
    - "What indoor activities are there in Perth?"
    """)

# Initialize agent in session state
if "agent" not in st.session_state:
    with st.spinner("Initializing agent..."):
        st.session_state.agent = WhatToDoAgent()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me what to do somewhere..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking and checking weather..."):
            try:
                # Call the agent
                response = asyncio.run(st.session_state.agent.chat_ui(prompt))
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar with info
with st.sidebar:
    st.markdown("### 🔧 How it works")
    st.markdown("""
    1. **Query Analysis**: I understand your location and time preferences
    2. **Weather Check**: I get real weather data from WeatherAPI.com
    3. **Activity Search**: I find activities using Foursquare Places API
    4. **Smart Recommendations**: I suggest indoor/outdoor activities based on weather
    """)
    
    st.markdown("### 📊 Features")
    st.markdown("""
    - ✅ Real weather data
    - ✅ Real activity recommendations
    - ✅ Weather-based suggestions
    - ✅ Flexible date parsing
    - ✅ Any location worldwide
    """)
    
    st.markdown("### 🗂️ Debug")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
        
    if st.button("View Logs"):
        if os.path.exists("logs"):
            import glob
            log_files = glob.glob("logs/*.log")
            if log_files:
                st.write(f"Found {len(log_files)} log files:")
                for log_file in log_files:
                    st.write(f"- {log_file}")
            else:
                st.write("No log files found")
        else:
            st.write("Logs directory doesn't exist yet")