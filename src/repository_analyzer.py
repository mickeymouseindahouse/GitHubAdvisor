import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .github_api import GitHubAPI

class RepositoryAnalyzer:
    """Analyzes GitHub repositories for various metrics and insights."""

    def __init__(self, github_api: GitHubAPI):
        self.github_api = github_api

    async def analyze_repository(self, repo_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a repository and return detailed metrics."""
        try:
            owner = repo_data["owner"]["login"]
            name = repo_data["name"]

            # Get additional data in parallel
            tasks = [
                self._get_contributor_count(owner, name),
                self._analyze_pull_requests(owner, name),
                self._analyze_issues(owner, name),
                self._get_release_info(owner, name),
                self._analyze_commit_activity(owner, name)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract results (handling exceptions)
            contributor_count = results[0] if not isinstance(results[0], Exception) else 0
            pr_metrics = results[1] if not isinstance(results[1], Exception) else {}
            issue_metrics = results[2] if not isinstance(results[2], Exception) else {}
            release_info = results[3] if not isinstance(results[3], Exception) else {}
            activity_metrics = results[4] if not isinstance(results[4], Exception) else {}

            # Calculate days since last update
            updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
            days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days

            return {
                "id": repo_data["id"],
                "name": repo_data["full_name"],
                "description": repo_data.get("description"),
                "url": repo_data["html_url"],
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "watchers": repo_data["watchers_count"],
                "language": repo_data.get("language"),
                "contributors": contributor_count,
                "open_issues": repo_data["open_issues_count"],
                "last_updated": updated_at.strftime("%Y-%m-%d"),
                "last_updated_days": days_since_update,
                "size": repo_data["size"],
                "default_branch": repo_data["default_branch"],
                "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
                "topics": repo_data.get("topics", []),
                "has_wiki": repo_data.get("has_wiki", False),
                "has_pages": repo_data.get("has_pages", False),
                "archived": repo_data.get("archived", False),
                "disabled": repo_data.get("disabled", False),
                # Metrics from additional analysis
                **pr_metrics,
                **issue_metrics,
                **release_info,
                **activity_metrics
            }

        except Exception as e:
            print(f"Error analyzing repository {repo_data.get('full_name', 'unknown')}: {str(e)}")
            return None

    async def _get_contributor_count(self, owner: str, name: str) -> int:
        """Get the number of contributors to the repository."""
        try:
            contributors = await self.github_api.get_contributors(owner, name)
            return len(contributors)
        except Exception:
            return 0

    async def _analyze_pull_requests(self, owner: str, name: str) -> Dict[str, Any]:
        """Analyze pull request metrics."""
        try:
            prs = await self.github_api.get_pull_requests(owner, name, state="all", per_page=100)

            if not prs:
                return {"open_prs": 0, "avg_pr_merge_time": None, "pr_merge_rate": 0}

            open_prs = len([pr for pr in prs if pr["state"] == "open"])
            merged_prs = [pr for pr in prs if pr.get("merged_at")]

            # Calculate average merge time for merged PRs
            merge_times = []
            for pr in merged_prs[-50:]:  # Last 50 merged PRs
                if pr.get("created_at") and pr.get("merged_at"):
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    merge_times.append((merged - created).total_seconds() / 86400)  # Days

            avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else None
            merge_rate = len(merged_prs) / len(prs) if prs else 0

            return {
                "open_prs": open_prs,
                "avg_pr_merge_time": avg_merge_time,
                "pr_merge_rate": merge_rate,
                "total_prs": len(prs)
            }

        except Exception:
            return {"open_prs": 0, "avg_pr_merge_time": None, "pr_merge_rate": 0}

    async def _analyze_issues(self, owner: str, name: str) -> Dict[str, Any]:
        """Analyze issue metrics."""
        try:
            open_issues = await self.github_api.get_issues(owner, name, state="open")
            closed_issues = await self.github_api.get_issues(owner, name, state="closed", per_page=50)

            # Filter out pull requests (GitHub API includes PRs in issues)
            open_issues = [issue for issue in open_issues if not issue.get("pull_request")]
            closed_issues = [issue for issue in closed_issues if not issue.get("pull_request")]

            # Calculate average time to close issues
            close_times = []
            for issue in closed_issues:
                if issue.get("created_at") and issue.get("closed_at"):
                    created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                    close_times.append((closed - created).total_seconds() / 86400)  # Days

            avg_close_time = sum(close_times) / len(close_times) if close_times else None

            return {
                "open_issues_actual": len(open_issues),
                "avg_issue_close_time": avg_close_time,
                "issue_response_activity": "high" if len(closed_issues) > 20 else "low"
            }

        except Exception:
            return {"open_issues_actual": 0, "avg_issue_close_time": None}

    async def _get_release_info(self, owner: str, name: str) -> Dict[str, Any]:
        """Get release information."""
        try:
            releases = await self.github_api.get_releases(owner, name)

            if not releases:
                return {"has_releases": False, "latest_release": None, "release_frequency": "none"}

            latest_release = releases[0]
            latest_date = datetime.fromisoformat(latest_release["published_at"].replace("Z", "+00:00"))
            days_since_release = (datetime.now(latest_date.tzinfo) - latest_date).days

            # Calculate release frequency
            if len(releases) > 1:
                oldest_release = releases[-1]
                oldest_date = datetime.fromisoformat(oldest_release["published_at"].replace("Z", "+00:00"))
                days_span = (latest_date - oldest_date).days
                avg_days_between_releases = days_span / (len(releases) - 1) if len(releases) > 1 else None
            else:
                avg_days_between_releases = None

            return {
                "has_releases": True,
                "latest_release": latest_release["tag_name"],
                "days_since_latest_release": days_since_release,
                "total_releases": len(releases),
                "avg_days_between_releases": avg_days_between_releases
            }

        except Exception:
            return {"has_releases": False, "latest_release": None}

    async def _analyze_commit_activity(self, owner: str, name: str) -> Dict[str, Any]:
        """Analyze commit activity patterns."""
        try:
            activity = await self.github_api.get_commit_activity(owner, name)

            if not activity:
                return {"commit_activity": "low", "commits_last_month": 0}

            # Calculate commits in the last month (last 4 weeks)
            recent_commits = sum(week["total"] for week in activity[-4:])
            total_commits = sum(week["total"] for week in activity)

            activity_level = "high" if recent_commits > 50 else "medium" if recent_commits > 10 else "low"

            return {
                "commit_activity": activity_level,
                "commits_last_month": recent_commits,
                "commits_last_year": total_commits
            }

        except Exception:
            return {"commit_activity": "unknown", "commits_last_month": 0}
