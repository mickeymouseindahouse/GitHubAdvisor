import os
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime

class GitHubAPI:
    """GitHub REST API client with async support."""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def search_repositories(
        self, 
        query: str, 
        sort: str = "stars", 
        order: str = "desc", 
        per_page: int = 30
    ) -> Dict[str, Any]:
        """Search for repositories."""
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed repository information."""
        url = f"{self.base_url}/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_contributors(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
        params = {"per_page": per_page}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code == 204:  # Empty repository
                return []
            response.raise_for_status()
            return response.json()

    async def get_pull_requests(
        self, 
        owner: str, 
        repo: str, 
        state: str = "all", 
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository pull requests."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {
            "state": state,
            "per_page": per_page,
            "sort": "updated",
            "direction": "desc"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_issues(
        self, 
        owner: str, 
        repo: str, 
        state: str = "open", 
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository issues."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {
            "state": state,
            "per_page": per_page
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_releases(self, owner: str, repo: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get repository releases."""
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        params = {"per_page": per_page}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()

    async def get_commit_activity(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository commit activity for the last year."""
        url = f"{self.base_url}/repos/{owner}/{repo}/stats/commit_activity"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 202:  # Computing stats
                await asyncio.sleep(2)
                response = await client.get(url, headers=self.headers)

            if response.status_code == 204:  # Empty repository
                return []

            response.raise_for_status()
            return response.json()
