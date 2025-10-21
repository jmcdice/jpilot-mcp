"""Jira client wrapper with connection handling."""

from typing import Optional
from jira import JIRA
from jira.exceptions import JIRAError

from ..config import JiraConfig


class JiraClient:
    """Wrapper around the Jira Python library with enhanced error handling."""

    def __init__(self, config: JiraConfig):
        """Initialize Jira client with configuration.

        Args:
            config: Jira configuration with server, email, and API token

        Raises:
            JiraConnectionError: If connection to Jira fails
        """
        self.config = config
        self._client: Optional[JIRA] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Jira server.

        Raises:
            JiraConnectionError: If connection fails
        """
        try:
            self._client = JIRA(
                server=self.config.server,
                basic_auth=(self.config.email, self.config.api_token),
                options={"rest_api_version": "3"},
            )
            # Test the connection by fetching server info
            _ = self._client.server_info()
        except JIRAError as e:
            raise JiraConnectionError(
                f"Failed to connect to Jira at {self.config.server}: {e.text}"
            ) from e
        except Exception as e:
            raise JiraConnectionError(
                f"Unexpected error connecting to Jira: {str(e)}"
            ) from e

    @property
    def client(self) -> JIRA:
        """Get the underlying JIRA client.

        Returns:
            JIRA client instance

        Raises:
            JiraConnectionError: If client is not connected
        """
        if self._client is None:
            raise JiraConnectionError("Jira client is not connected")
        return self._client

    def test_connection(self) -> bool:
        """Test if the connection to Jira is working.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            _ = self.client.server_info()
            return True
        except Exception:
            return False

    def get_current_user(self) -> dict:
        """Get information about the current authenticated user.

        Returns:
            Dictionary with user information (accountId, displayName, email, etc.)

        Raises:
            JiraError: If unable to fetch user information
        """
        try:
            return self.client.myself()
        except JIRAError as e:
            raise JiraError(f"Failed to get current user: {e.text}") from e


class JiraConnectionError(Exception):
    """Raised when connection to Jira fails."""

    pass


class JiraError(Exception):
    """Base exception for Jira operations."""

    pass


def create_jira_client(config: Optional[JiraConfig] = None) -> JiraClient:
    """Create a Jira client instance.

    Args:
        config: Optional Jira configuration. If not provided, loads from environment.

    Returns:
        Configured JiraClient instance

    Raises:
        JiraConnectionError: If connection fails
    """
    if config is None:
        from ..config import get_jira_config

        config = get_jira_config()

    return JiraClient(config)

