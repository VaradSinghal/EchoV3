"""
Background tasks for the Echo application.
"""
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging
import httpx

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import UserProfile, UserSession

logger = logging.getLogger(__name__)


async def sync_github_user_data(user_id: str, github_access_token: str):
    """
    Sync user data from GitHub on login.
    Updates profile with latest GitHub information.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {github_access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch GitHub user data: {response.status_code}")
                return
            
            github_user = response.json()
            
            # Update profile in database
            db = SessionLocal()
            try:
                profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                if profile:
                    profile.github_username = github_user.get("login")
                    profile.github_avatar_url = github_user.get("avatar_url")
                    profile.display_name = github_user.get("name") or profile.display_name
                    db.commit()
                    logger.info(f"Synced GitHub data for user {user_id}")
            finally:
                db.close()
                
    except Exception as e:
        logger.error(f"Error syncing GitHub data: {e}")


async def cleanup_expired_sessions():
    """
    Cleanup expired sessions from the database.
    Should be run periodically (e.g., every hour).
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Delete sessions that have expired
        expired_count = db.query(UserSession).filter(
            UserSession.expires_at < now
        ).delete()
        
        # Deactivate sessions inactive for more than 7 days
        inactive_threshold = now - timedelta(days=7)
        inactive_count = db.query(UserSession).filter(
            UserSession.last_active_at < inactive_threshold,
            UserSession.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        logger.info(f"Cleaned up {expired_count} expired sessions, deactivated {inactive_count} inactive sessions")
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        db.rollback()
    finally:
        db.close()


async def send_welcome_email(user_email: str, display_name: Optional[str] = None):
    """
    Send welcome email to new users.
    In production, integrate with an email service (SendGrid, SES, etc.)
    """
    try:
        name = display_name or "there"
        
        # TODO: Replace with actual email sending logic
        # For now, just log the email
        logger.info(f"Sending welcome email to {user_email}")
        
        email_content = f"""
        Hi {name}!
        
        Welcome to Echo! We're excited to have you on board.
        
        Here's what you can do:
        - Monitor your social media presence
        - Get AI-powered insights from community feedback
        - Automate GitHub issue creation from user suggestions
        
        Get started by connecting your GitHub repositories.
        
        Best,
        The Echo Team
        """
        
        # In production:
        # await send_email(to=user_email, subject="Welcome to Echo!", body=email_content)
        
        logger.info(f"Welcome email sent to {user_email}")
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")


class BackgroundTaskRunner:
    """
    Manages periodic background tasks.
    """
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background task runner."""
        self.running = True
        self._task = asyncio.create_task(self._run_periodic_tasks())
        logger.info("Background task runner started")
    
    async def stop(self):
        """Stop the background task runner."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background task runner stopped")
    
    async def _run_periodic_tasks(self):
        """Run periodic tasks in a loop."""
        while self.running:
            try:
                # Cleanup sessions every hour
                await cleanup_expired_sessions()
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic tasks: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying


# Global task runner instance
task_runner = BackgroundTaskRunner()
