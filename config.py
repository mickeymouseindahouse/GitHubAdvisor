"""Configuration settings for the GitHub Repository Finder."""

import os
from typing import Dict, Any

# Default search parameters
DEFAULT_SEARCH_PARAMS = {
    "per_page": 30,
    "sort": "stars",
    "order": "desc"
}

# Scoring weights for repository ranking
SCORING_WEIGHTS = {
    "stars_weight": 1.0,
    "contributors_weight": 5.0,
    "activity_weight": 1.0,
    "pr_merge_weight": 1.0,
    "issues_weight": 1.0
}

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    "requests_per_minute": 30,
    "batch_size": 5,
    "delay_between_batches": 0.5
}

# OpenAI model settings
OPENAI_SETTINGS = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.1,
    "max_tokens": 2000
}

# Streamlit page config
STREAMLIT_CONFIG = {
    "page_title": "GitHub Repository Finder",
    "page_icon": "🔍",
    "layout": "wide"
}

def get_env_vars() -> Dict[str, Any]:
    """Get environment variables with defaults."""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
    }
