"""Configuration management for jpilot-mcp."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class JiraConfig(BaseModel):
    """Jira connection configuration."""

    server: str = Field(..., description="Jira server URL (e.g., https://your-domain.atlassian.net)")
    email: str = Field(..., description="Jira user email")
    api_token: str = Field(..., description="Jira API token")

    @classmethod
    def from_env(cls) -> "JiraConfig":
        """Load configuration from environment variables."""
        # Try to load from .env file if it exists
        load_dotenv()

        server = os.getenv("JIRA_SERVER")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")

        if not all([server, email, api_token]):
            missing = []
            if not server:
                missing.append("JIRA_SERVER")
            if not email:
                missing.append("JIRA_EMAIL")
            if not api_token:
                missing.append("JIRA_API_TOKEN")

            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please set them in your environment or .env file."
            )

        return cls(server=server, email=email, api_token=api_token)


def get_jira_config() -> JiraConfig:
    """Get Jira configuration from environment."""
    return JiraConfig.from_env()

