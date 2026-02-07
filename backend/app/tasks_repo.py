"""
Background tasks for repository management.
"""
from datetime import datetime, timedelta
from typing import List
import asyncio
import logging

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import UserProfile
from app.db.models_repo import Repository, RepositorySettings
from app.services.github import GitHubService, parse_github_datetime

logger = logging.getLogger(__name__)


async def sync_repository(repo_id: str, github_token: str):
    """
    Sync a single repository from GitHub.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            logger.warning(f"Repository {repo_id} not found for sync")
            return
        
        github = GitHubService(github_token)
        parts = repo.full_name.split("/")
        
        try:
            github_repo = await github.get_repository(parts[0], parts[1])
            
            # Update repository data
            repo.description = github_repo.get("description")
            repo.visibility = github_repo.get("visibility", "public")
            repo.default_branch = github_repo.get("default_branch", "main")
            repo.language = github_repo.get("language")
            repo.stars_count = github_repo.get("stargazers_count", 0)
            repo.forks_count = github_repo.get("forks_count", 0)
            repo.open_issues_count = github_repo.get("open_issues_count", 0)
            repo.watchers_count = github_repo.get("watchers_count", 0)
            repo.github_updated_at = parse_github_datetime(github_repo.get("updated_at"))
            repo.last_synced_at = datetime.utcnow()
            repo.sync_error = None
            
            db.commit()
            logger.info(f"Synced repository: {repo.full_name}")
            
        except Exception as e:
            repo.sync_error = str(e)
            db.commit()
            logger.error(f"Failed to sync {repo.full_name}: {e}")
            
    finally:
        db.close()


async def sync_all_repositories():
    """
    Sync all active repositories that are due for sync.
    """
    db = SessionLocal()
    try:
        # Get repositories that need syncing
        now = datetime.utcnow()
        
        repos_to_sync = db.query(Repository, RepositorySettings, UserProfile).join(
            RepositorySettings, Repository.id == RepositorySettings.repository_id
        ).join(
            UserProfile, Repository.owner_id == UserProfile.user_id
        ).filter(
            Repository.is_active == True,
            RepositorySettings.auto_sync == True
        ).all()
        
        for repo, settings, profile in repos_to_sync:
            # Check if due for sync
            if repo.last_synced_at:
                next_sync = repo.last_synced_at + timedelta(minutes=settings.sync_interval_minutes)
                if now < next_sync:
                    continue
            
            if profile.github_access_token:
                await sync_repository(str(repo.id), profile.github_access_token)
            else:
                logger.warning(f"No GitHub token for user {profile.user_id}")
        
        logger.info(f"Repository sync cycle complete")
        
    except Exception as e:
        logger.error(f"Error in sync_all_repositories: {e}")
    finally:
        db.close()


async def analyze_repository_codebase(repo_id: str, github_token: str):
    """
    Analyze repository codebase structure.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return
        
        github = GitHubService(github_token)
        parts = repo.full_name.split("/")
        
        # Get languages
        languages = await github.get_repository_languages(parts[0], parts[1])
        if languages:
            # Set primary language (highest byte count)
            primary_lang = max(languages, key=languages.get) if languages else None
            if primary_lang:
                repo.language = primary_lang
                db.commit()
        
        logger.info(f"Analyzed codebase for {repo.full_name}")
        
    except Exception as e:
        logger.error(f"Error analyzing codebase: {e}")
    finally:
        db.close()


async def discover_branches(repo_id: str, github_token: str):
    """
    Discover and cache branches for a repository.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return
        
        github = GitHubService(github_token)
        parts = repo.full_name.split("/")
        
        branches = await github.list_branches(parts[0], parts[1])
        # TODO: Store branches in database if needed
        
        logger.info(f"Discovered {len(branches)} branches for {repo.full_name}")
        
    except Exception as e:
        logger.error(f"Error discovering branches: {e}")
    finally:
        db.close()


async def analyze_contributors(repo_id: str, github_token: str):
    """
    Analyze contributors for a repository.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return
        
        github = GitHubService(github_token)
        parts = repo.full_name.split("/")
        
        contributors = await github.list_contributors(parts[0], parts[1])
        # TODO: Store contributors in database if needed
        
        logger.info(f"Analyzed {len(contributors)} contributors for {repo.full_name}")
        
    except Exception as e:
        logger.error(f"Error analyzing contributors: {e}")
    finally:
        db.close()


class RepositorySyncRunner:
    """
    Background task runner for repository sync.
    """
    
    def __init__(self):
        self.running = False
        self._task = None
    
    async def start(self):
        """Start the sync runner."""
        self.running = True
        self._task = asyncio.create_task(self._run_periodic_sync())
        logger.info("Repository sync runner started")
    
    async def stop(self):
        """Stop the sync runner."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Repository sync runner stopped")
    
    async def _run_periodic_sync(self):
        """Run periodic sync in a loop."""
        while self.running:
            try:
                await sync_all_repositories()
                # Run every 15 minutes
                await asyncio.sleep(900)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(60)


# Global sync runner instance
repo_sync_runner = RepositorySyncRunner()
