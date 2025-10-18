"""
Chat Application with Web Search Tool Calling
Demonstrates function calling with web search capabilities
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from utils.llm_client import LLMClient, get_available_models
from utils.search_tools import WebSearchTool, format_search_results

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = None
    if "search_tool" not in st.session_state:
        st.session_state.search_tool = WebSearchTool()


def get_search_function_schema():
    """Define the search function schema for tool calling"""
    return {
        "name": "web_search",
        "description": "Search the web for current information about a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up information"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }


def execute_search(query: str, num_results: int = 5):
    """Execute web search and return formatted results"""
    results = st.session_state.search_tool.search(query, num_results)
    return format_search_results(results)


# FIND THIS SECTION IN YOUR CODE (around line 65-95):
# Delete everything from "def handle_tool_calls(message_content: str):" 
# down to "return message_content, False"
# 
# REPLACE IT WITH THIS:


def handle_tool_calls(message_content: str):
    """Robust tool-calling detection for search and currency."""
    import re
    message_lower = message_content.lower()
    st.write("🧩 handle_tool_calls() called with:", message_content)

    # --- Currency conversion ---
    if any(word in message_lower for word in ["convert", "exchange", "usd", "eur", "thb", "currency", "bitcoin", "btc"]):
        from utils.conversion_tools import convert_fx
        match = re.search(r'(\d+\.?\d*)\s*([A-Z]{3})\s*(?:to|in)\s*([A-Z]{3})', message_content, re.IGNORECASE)
        if match:
            amount, from_curr, to_curr = match.groups()
            result = convert_fx(float(amount), from_curr, to_curr)
            return f"""User Query: {message_content}

💱 {float(amount):,.2f} {from_curr.upper()} = {result['converted_amount']:,.2f} {to_curr.upper()}
Rate: {result['rate']:.4f} | Provider: {result['provider']}

Please respond naturally about this conversion.""", True

    # --- Web search detection ---
    search_keywords = [
        "current", "latest", "today", "now", "recent", "news", "update",
        "trending", "viral", "popular", "search", "weather", "stock", "price",
        "twitter", "facebook", "instagram", "reddit", "tiktok",
        "happening", "going on", "look up", "find", "show me"
    ]

    # Normalize punctuation for matching
    normalized = re.sub(r"[^\w\s]", " ", message_lower)

    matched = [kw for kw in search_keywords if kw in normalized]
    st.write(f"🔍 Matched keywords: {matched}")

    if matched:
        query = message_content.strip("?!. ")
        st.write(f"🚀 Triggering search for query: {query}")
        search_results = execute_search(query, 5)
        return f"""User Query: {message_content}

{search_results}

Please answer based on this information.""", True

    # Nothing triggered
    st.write("⚙️ No trigger detected for:", message_content)
    return message_content, False


def display_chat_messages():
    """Display chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("search_used", False):
                st.markdown("🔍 *Used web search*")
            st.markdown(message["content"])

def main():
    st.set_page_config(
        page_title="Chat with Web Search",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 Chat with Web Search")
    st.markdown(
        "AI chat with **automatic** web search capabilities - Advanced starter code!")

    st.info("🤖 **Smart Tool Calling**: I automatically detect when you need current information and search the web! Try asking about weather, news, stock prices, or recent events.")

    # Initialize session state
    init_session_state()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Model selection
        available_models = get_available_models()
        selected_model = st.selectbox(
            "Select Model",
            available_models,
            index=0,
            help="Choose the language model to use"
        )

        # Temperature slider
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Controls randomness in responses"
        )

        # Max tokens
        max_tokens = st.slider(
            "Max Tokens",
            min_value=50,
            max_value=4000,
            value=2000,
            step=50,
            help="Maximum length of response"
        )

        # Search settings
        st.subheader("🔍 Search Settings")
        auto_search = st.checkbox(
            "Auto Search",
            value=True,
            help="Automatically search when needed"
        )

        search_api = st.selectbox(
            "Search API",
            ["serper", "tavily"],
            help="Choose search API to use"
        )

        # Initialize LLM client
        if st.button("Initialize Model") or st.session_state.llm_client is None:
            with st.spinner("Initializing model..."):
                st.session_state.llm_client = LLMClient(
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            st.success(f"Model {selected_model} initialized!")

        st.divider()

        # Clear chat button
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()

        # API status
        st.subheader("🔧 API Status")
        serper_key = os.getenv("SERPER_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")

        st.write(
            f"**Serper API:** {'✅ Configured' if serper_key else '❌ Not configured'}")
        st.write(
            f"**Tavily API:** {'✅ Configured' if tavily_key else '❌ Not configured'}")

        if not serper_key and not tavily_key:
            st.warning(
                "⚠️ No search APIs configured. Add API keys to .env file.")

        st.divider()
        st.markdown("### 📚 About")
        st.markdown("""
        This advanced chat app demonstrates:
        - Web search integration
        - Tool calling concepts
        - Real-time information retrieval
        - Enhanced context for LLMs
        
        **Smart Search Triggers:**
        - Automatic detection for current events, weather, stock prices
        - Time-sensitive questions (today, latest, recent, 2024, etc.)
        - Explicit search requests ("search:", "look up", etc.)
        - Questions about news, updates, and recent developments
        
        **For Students:**
        - Implement proper function calling
        - Add more tools (calculator, weather, etc.)
        - Improve search query extraction
        - Add search result caching
        """)

    # Main chat interface
    if not st.session_state.llm_client:
        st.warning("⚠️ Please initialize a model in the sidebar first!")
        return

    # Display existing chat messages
    display_chat_messages()

    # Example queries
    st.markdown("### 💡 Try these example queries:")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌤️ Current weather in Tokyo"):
            example_query = "What's the current weather in Tokyo today?"
            st.session_state.example_query = example_query

    with col2:
        if st.button("📈 Latest AI developments"):
            example_query = "What are the latest developments in artificial intelligence in 2024?"
            st.session_state.example_query = example_query

    with col3:
        if st.button("💼 Stock market today"):
            example_query = "How is the stock market performing today?"
            st.session_state.example_query = example_query

    # Chat input
    prompt = st.chat_input(
        "Ask anything... I'll automatically search when you need current info! 🔍")

    # Handle example query
    if hasattr(st.session_state, 'example_query'):
        prompt = st.session_state.example_query
        delattr(st.session_state, 'example_query')

    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Handle search and generate response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                # Check if search is needed
                enhanced_prompt, search_used = handle_tool_calls(prompt)

                if search_used:
                    st.markdown(
                        "🔍 *Searching the web for current information...*")

                # Prepare messages for LLM
                messages = []
                # All except the last message
                for msg in st.session_state.messages[:-1]:
                    messages.append(
                        {"role": msg["role"], "content": msg["content"]})

                # Add the enhanced prompt
                messages.append({"role": "user", "content": enhanced_prompt})
                # if enhanced_prompt != prompt and search_used:
                #    st.markdown(" 🎉 * Necessary information retrieved successfully!*")

                # Get response from LLM
                response = st.session_state.llm_client.chat(messages)

                # Display response
                st.markdown(response)

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "search_used": search_used
                })


if __name__ == "__main__":
    main()
