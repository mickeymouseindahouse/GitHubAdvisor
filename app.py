import streamlit as st
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.github_agent import GitHubRepositoryAgent

load_dotenv()

st.set_page_config(
    page_title="GitHub Repository Finder",
    page_icon="🔍",
    layout="wide"
)

def main():
    st.title("🔍 GitHub Repository Finder")
    st.markdown("Find the best GitHub repositories for your needs using AI-powered search and analysis!")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = "user_session"
    if "stored_repositories" not in st.session_state:
        st.session_state.stored_repositories = []
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = GitHubRepositoryAgent()
        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            st.info("Please check your API keys in the .env file")
            return

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Redisplay diagram if it exists in this message
            if "diagram_path" in message and message["diagram_path"]:
                st.subheader("🏗️ Class Diagram")
                try:
                    st.image(message["diagram_path"], caption="Generated Class Diagram", use_column_width=True)
                except Exception as e:
                    st.warning(f"Could not display diagram: {str(e)}")

    # Chat input
    if prompt := st.chat_input("What kind of repository are you looking for?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Processing your request..."):
                try:
                    response = asyncio.run(st.session_state.agent.find_repositories(
                        prompt, 
                        st.session_state.thread_id,
                        st.session_state.stored_repositories
                    ))
                    st.markdown(response["message"])

                    # Store repositories in session state for diagram requests
                    if "repositories" in response and response["repositories"]:
                        st.session_state.stored_repositories = response["repositories"]

                    # Display class diagram if generated
                    if "diagram_path" in response and response["diagram_path"]:
                        st.subheader("🏗️ Class Diagram")
                        try:
                            st.image(response["diagram_path"], caption="Generated Class Diagram", use_column_width=True)
                        except Exception as e:
                            st.warning(f"Could not display diagram: {str(e)}")

                    if "repositories" in response and response["repositories"]:
                        st.subheader("📊 Repository Analysis")
                        for i, repo in enumerate(response["repositories"][:3]):  # Show top 3
                            with st.expander(f"#{i+1}: {repo['name']}", expanded=(i==0)):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.metric("⭐ Stars", repo["stars"])
                                    st.metric("👥 Contributors", repo["contributors"])
                                    st.metric("📝 Language", repo["language"] or "Mixed")

                                with col2:
                                    st.metric("📅 Last Updated", repo["last_updated"])
                                    st.metric("🔀 Open PRs", repo["open_prs"])
                                    if repo["avg_pr_merge_time"]:
                                        st.metric("⏱️ Avg PR Merge Time", f"{repo['avg_pr_merge_time']:.1f} days")

                                st.write("**Description:**", repo["description"] or "No description available")
                                st.write("**URL:**", f"[{repo['url']}]({repo['url']})")

                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["message"],
                        "diagram_path": response.get("diagram_path")
                    })

                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg,
                        "diagram_path": None
                    })

    # Sidebar with instructions
    with st.sidebar:
        st.header("🚀 How it works")
        st.markdown("""
        1. **Enter your query** describing what kind of repository you need
        2. **AI analyzes** your requirements using OpenAI
        3. **GitHub API search** finds relevant repositories
        4. **Smart ranking** based on stars, contributors, and activity
        5. **Detailed metrics** show PR merge times and other insights
        6. **Class diagrams** generated on request using AI analysis
        """)

        st.header("💡 Example queries")
        st.markdown("""
        - "Find a Python web framework for REST APIs"
        - "Show me a class diagram for a React state management library"
        - "I need a machine learning framework with good documentation"
        """)

        st.header("🔑 Setup")
        st.markdown("""
        Make sure to set up your `.env` file with:
        - `OPENAI_API_KEY`
        - `GITHUB_TOKEN` (optional, for higher rate limits)
        """)

if __name__ == "__main__":
    main()
