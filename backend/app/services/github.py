"""
GitHub API Service
Handles all interactions with GitHub API for repository management.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
import hmac
import hashlib
import secrets
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


class GitHubService:
    """
    Service for interacting with GitHub API.
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def get_user(self) -> Dict[str, Any]:
        """Get authenticated user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def list_repositories(
        self, 
        visibility: Optional[str] = None,
        sort: str = "updated",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        List repositories for the authenticated user.
        """
        params = {
            "sort": sort,
            "per_page": per_page,
            "page": page
        }
        if visibility:
            params["visibility"] = visibility
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/user/repos",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get a specific repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List branches for a repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def list_contributors(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List contributors for a repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/contributors",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get languages used in a repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/languages",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_webhook(
        self, 
        owner: str, 
        repo: str, 
        webhook_url: str,
        secret: str,
        events: List[str] = ["push", "pull_request", "issues"]
    ) -> Dict[str, Any]:
        """
        Create a webhook for a repository.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/hooks",
                headers=self.headers,
                json={
                    "name": "web",
                    "active": True,
                    "events": events,
                    "config": {
                        "url": webhook_url,
                        "content_type": "json",
                        "secret": secret,
                        "insecure_ssl": "0"
                    }
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> bool:
        """Delete a webhook from a repository."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/hooks/{hook_id}",
                headers=self.headers
            )
            return response.status_code == 204
    
    async def list_webhooks(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List webhooks for a repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/hooks",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def check_repository_permissions(self, owner: str, repo: str) -> Dict[str, bool]:
        """Check user permissions for a repository."""
        try:
            repo_data = await self.get_repository(owner, repo)
            permissions = repo_data.get("permissions", {})
            return {
                "admin": permissions.get("admin", False),
                "push": permissions.get("push", False),
                "pull": permissions.get("pull", False)
            }
        except httpx.HTTPStatusError:
            return {"admin": False, "push": False, "pull": False}
    
    async def get_open_issues_count(self, owner: str, repo: str) -> int:
        """Get count of open issues."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                params={"state": "open", "per_page": 1}
            )
            response.raise_for_status()
            # Get total from link header if available
            link_header = response.headers.get("link", "")
            if 'rel="last"' in link_header:
                # Parse last page number
                import re
                match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if match:
                    return int(match.group(1))
            return len(response.json())
    
    async def get_open_prs_count(self, owner: str, repo: str) -> int:
        """Get count of open pull requests."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                params={"state": "open", "per_page": 1}
            )
            response.raise_for_status()
            link_header = response.headers.get("link", "")
            if 'rel="last"' in link_header:
                import re
                match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if match:
                    return int(match.group(1))
            return len(response.json())


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret."""
    return secrets.token_hex(32)


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature.
    """
    if not signature:
        return False
    
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def parse_github_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse GitHub datetime string to datetime object."""
    if not dt_string:
        return None
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    except ValueError:
        return None
