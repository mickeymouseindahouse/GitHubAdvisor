import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
from langgraph.graph import Graph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from .github_api import GitHubAPI
from .repository_analyzer import RepositoryAnalyzer
from .class_diagram_generator import ClassDiagramGenerator

class GitHubRepositoryAgent:
    """Main agent that orchestrates the repository finding workflow using LangGraph."""

    def __init__(self):
        self.openai_client = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.github_api = GitHubAPI()
        self.analyzer = RepositoryAnalyzer(self.github_api)
        self.diagram_generator = ClassDiagramGenerator()
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> Graph:
        """Build the LangGraph workflow for repository finding."""
        workflow = Graph()

        # Add nodes
        workflow.add_node("parse_query", self._parse_query)
        workflow.add_node("search_repositories", self._search_repositories)
        workflow.add_node("analyze_repositories", self._analyze_repositories)
        workflow.add_node("rank_repositories", self._rank_repositories)
        workflow.add_node("generate_diagram", self._generate_diagram)
        workflow.add_node("generate_response", self._generate_response)

        # Add conditional routing from parse_query
        workflow.add_conditional_edges(
            "parse_query",
            self._route_request,
            {
                "search": "search_repositories",
                "diagram": "generate_diagram"
            }
        )

        # Search flow
        workflow.add_edge("search_repositories", "analyze_repositories")
        workflow.add_edge("analyze_repositories", "rank_repositories")
        workflow.add_edge("rank_repositories", "generate_response")
        
        # Diagram flow
        workflow.add_edge("generate_diagram", "generate_response")
        workflow.add_edge("generate_response", END)

        # Set entry point
        workflow.set_entry_point("parse_query")

        return workflow.compile(checkpointer=self.memory)

    def _route_request(self, state: Dict[str, Any]) -> str:
        """Route request based on query type."""
        query = state["user_query"].lower()
        diagram_keywords = ["diagram", "draw", "show", "visualize"]
        
        if any(keyword in query for keyword in diagram_keywords):
            return "diagram"
        return "search"

    async def _generate_diagram(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate class diagram for specified repository."""
        # Parse repo index from query
        query = state["user_query"].lower()
        repo_index = 0  # default to first repo
        
        if "second" in query or "2nd" in query or "2" in query:
            repo_index = 1
        elif "third" in query or "3rd" in query or "3" in query:
            repo_index = 2
            
        # Get repositories from state
        repositories = state.get("ranked_repositories", [])
        
        if not repositories or repo_index >= len(repositories):
            state["response"] = "No repositories available for diagram generation. Please search for repositories first."
            return state
            
        # Generate diagram for selected repository
        selected_repo = repositories[repo_index]
        diagram_path = await self.diagram_generator.generate_diagram(selected_repo)
        
        if diagram_path:
            state["diagram_path"] = diagram_path
            state["response"] = f"Generated class diagram for {selected_repo['name']}"
        else:
            state["response"] = f"Failed to generate diagram for {selected_repo['name']}"
            
        return state

    async def find_repositories(self, user_query: str, thread_id: str = "default", stored_repositories: List[Dict] = None) -> Dict[str, Any]:
        """Main entry point for finding repositories."""
        initial_state = {
            "user_query": user_query,
            "thread_id": thread_id,
            "search_terms": [],
            "repositories": [],
            "analyzed_repositories": [],
            "ranked_repositories": stored_repositories or [],
            "response": ""
        }

        config = {"configurable": {"thread_id": thread_id}}
        result = await self.workflow.ainvoke(initial_state, config=config)
        
        return {
            "message": result["response"],
            "repositories": result.get("ranked_repositories", []),
            "diagram_path": result.get("diagram_path")
        }

    async def _parse_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user query to extract search terms and requirements."""
        system_message = SystemMessage(content="""
        You are an expert at understanding developer needs and converting them into GitHub search terms.

        Given a user query about finding a repository, extract:
        1. Primary technology/framework keywords
        2. Programming language preferences
        3. Specific features or use cases
        4. Project type (library, framework, tool, etc.)

        Return a JSON object with:
        - "search_terms": list of relevant keywords for GitHub search
        - "language": preferred programming language (if mentioned)
        - "requirements": list of specific requirements mentioned

        Example:
        User: "I need a Python web framework for building REST APIs"
        Response: {
            "search_terms": ["web framework", "REST API", "HTTP", "server"],
            "language": "python",
            "requirements": ["REST API support", "web framework"]
        }
        """)

        human_message = HumanMessage(content=f"User query: {state['user_query']}")
        response = await self.openai_client.ainvoke([system_message, human_message])

        try:
            parsed_data = json.loads(response.content)
            state["search_terms"] = parsed_data.get("search_terms", [])
            state["language"] = parsed_data.get("language")
            state["requirements"] = parsed_data.get("requirements", [])
        except json.JSONDecodeError:
            # Fallback: use the query as-is
            state["search_terms"] = [state["user_query"]]
            state["language"] = None
            state["requirements"] = []

        return state

    async def _search_repositories(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search GitHub for repositories based on parsed terms."""
        repositories = []

        for term in state["search_terms"]:
            search_query = term
            if state.get("language"):
                search_query += f" language:{state['language']}"

            results = await self.github_api.search_repositories(
                query=search_query,
                sort="stars",
                order="desc",
                per_page=20
            )

            repositories.extend(results.get("items", []))

        # Remove duplicates based on repository ID
        unique_repos = {}
        for repo in repositories:
            unique_repos[repo["id"]] = repo

        state["repositories"] = list(unique_repos.values())[:30]  # Limit to top 30
        return state

    async def _analyze_repositories(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repositories for detailed metrics."""
        analyzed_repos = []

        # Process repositories in batches to avoid rate limits
        batch_size = 5
        repositories = state["repositories"]

        for i in range(0, len(repositories), batch_size):
            batch = repositories[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                self.analyzer.analyze_repository(repo)
                for repo in batch
            ], return_exceptions=True)

            for result in batch_results:
                if not isinstance(result, Exception) and result:
                    analyzed_repos.append(result)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.5)

        state["analyzed_repositories"] = analyzed_repos
        return state

    async def _rank_repositories(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rank repositories based on multiple criteria."""
        repositories = state["analyzed_repositories"]

        if not repositories:
            state["ranked_repositories"] = []
            return state

        # Calculate composite score for each repository
        for repo in repositories:
            score = self._calculate_repository_score(repo)
            repo["composite_score"] = score

        # Sort by composite score
        ranked_repos = sorted(repositories, key=lambda x: x["composite_score"], reverse=True)
        state["ranked_repositories"] = ranked_repos
        return state

    def _calculate_repository_score(self, repo: Dict[str, Any]) -> float:
        """Calculate a composite score for repository ranking."""
        score = 0

        # Stars (normalized, max 1000 points)
        stars = repo.get("stars", 0)
        score += min(stars / 10, 1000)

        # Contributors (normalized, max 500 points)
        contributors = repo.get("contributors", 0)
        score += min(contributors * 5, 500)

        # Recent activity (max 300 points)
        last_updated = repo.get("last_updated_days", 365)
        if last_updated <= 7:
            score += 300
        elif last_updated <= 30:
            score += 200
        elif last_updated <= 90:
            score += 100

        # PR merge time (max 200 points, favor faster merges)
        avg_merge_time = repo.get("avg_pr_merge_time")
        if avg_merge_time is not None:
            if avg_merge_time <= 1:
                score += 200
            elif avg_merge_time <= 3:
                score += 150
            elif avg_merge_time <= 7:
                score += 100
            elif avg_merge_time <= 14:
                score += 50

        # Issues to stars ratio (max 100 points, lower is better)
        open_issues = repo.get("open_issues", 0)
        if stars > 0:
            issue_ratio = open_issues / stars
            if issue_ratio < 0.1:
                score += 100
            elif issue_ratio < 0.2:
                score += 50

        return score

    async def _generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a natural language response about the found repositories."""
        
        # Check if this is a diagram request - provide minimal response
        query = state["user_query"].lower()
        diagram_keywords = ["diagram", "draw", "show", "visualize"]
        
        if any(keyword in query for keyword in diagram_keywords):
            # Use the response already set by _generate_diagram
            if "response" in state and state["response"]:
                return state
            else:
                state["response"] = "Generated class diagram"
                return state
        
        # Regular search response
        repositories = state["ranked_repositories"][:3]  # Top 3

        if not repositories:
            state["response"] = "I couldn't find any repositories matching your criteria. Try refining your search terms."
            return state

        system_message = SystemMessage(content="""
        You are a helpful assistant that explains GitHub repository recommendations.

        Given a list of repositories with their metrics, provide a conversational explanation of:
        1. Why these repositories are good matches
        2. Key strengths of the top recommendation
        3. Brief comparison of the top options

        Be enthusiastic but informative. Focus on the metrics that matter most to developers.
        """)

        repo_summary = []
        for i, repo in enumerate(repositories):
            summary = f"""
            Repository #{i+1}: {repo['name']}
            - Stars: {repo['stars']}
            - Contributors: {repo['contributors']}
            - Language: {repo.get('language', 'Mixed')}
            - Last updated: {repo.get('last_updated_days', 'Unknown')} days ago
            - Average PR merge time: {repo.get('avg_pr_merge_time', 'Unknown')} days
            - Description: {repo.get('description', 'No description')}
            """
            repo_summary.append(summary)

        human_message = HumanMessage(content=f"""
        User was looking for: {state['user_query']}

        Top repositories found:
        {chr(10).join(repo_summary)}

        Please provide a conversational explanation of these recommendations.
        """)

        response = await self.openai_client.ainvoke([system_message, human_message])
        state["response"] = response.content
        return state
