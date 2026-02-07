"""
Webhook Handler Endpoints
Handles incoming GitHub webhook events.
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Header
import logging
import json

from app.services.github import verify_webhook_signature
from app.db.session import SessionLocal
from app.db.models_repo import Repository, Webhook

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/github")
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(None),
    x_github_delivery: str = Header(None)
):
    """
    Handle incoming GitHub webhook events.
    """
    body = await request.body()
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Get repository info from payload
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name")
    
    if not repo_full_name:
        logger.warning(f"Webhook without repository info: {x_github_event}")
        return {"status": "ignored", "reason": "No repository in payload"}
    
    # Find the repository and webhook in our database
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(
            Repository.full_name == repo_full_name
        ).first()
        
        if not repo:
            logger.info(f"Webhook for untracked repo: {repo_full_name}")
            return {"status": "ignored", "reason": "Repository not tracked"}
        
        # Verify webhook signature
        webhooks = db.query(Webhook).filter(
            Webhook.repository_id == repo.id,
            Webhook.is_active == True
        ).all()
        
        signature_valid = False
        for webhook in webhooks:
            if verify_webhook_signature(body, x_hub_signature_256, webhook.secret):
                signature_valid = True
                break
        
        if not signature_valid and webhooks:
            logger.warning(f"Invalid webhook signature for {repo_full_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Handle the event
        event_handler = WEBHOOK_HANDLERS.get(x_github_event)
        if event_handler:
            result = await event_handler(payload, repo, db)
            return {"status": "processed", "event": x_github_event, "result": result}
        else:
            logger.info(f"Unhandled event type: {x_github_event}")
            return {"status": "ignored", "reason": f"Unhandled event: {x_github_event}"}
            
    finally:
        db.close()


# ============ Event Handlers ============

async def handle_push_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle push events."""
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])
    pusher = payload.get("pusher", {}).get("name")
    
    logger.info(f"Push to {repo.full_name}: {len(commits)} commits by {pusher}")
    
    # Update repository last synced
    from datetime import datetime
    repo.github_updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "branch": ref.replace("refs/heads/", ""),
        "commits_count": len(commits),
        "pusher": pusher
    }


async def handle_pull_request_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle pull request events."""
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    pr_title = pr.get("title")
    pr_user = pr.get("user", {}).get("login")
    
    logger.info(f"PR {action} on {repo.full_name}: #{pr_number} by {pr_user}")
    
    # TODO: Store PR data, trigger analysis, etc.
    
    return {
        "action": action,
        "pr_number": pr_number,
        "title": pr_title,
        "user": pr_user
    }


async def handle_issues_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle issue events."""
    action = payload.get("action")
    issue = payload.get("issue", {})
    issue_number = issue.get("number")
    issue_title = issue.get("title")
    issue_user = issue.get("user", {}).get("login")
    
    logger.info(f"Issue {action} on {repo.full_name}: #{issue_number} by {issue_user}")
    
    # Update open issues count
    if action == "opened":
        repo.open_issues_count = (repo.open_issues_count or 0) + 1
    elif action == "closed":
        repo.open_issues_count = max(0, (repo.open_issues_count or 1) - 1)
    db.commit()
    
    return {
        "action": action,
        "issue_number": issue_number,
        "title": issue_title,
        "user": issue_user
    }


async def handle_issue_comment_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle issue comment events."""
    action = payload.get("action")
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})
    
    logger.info(f"Issue comment {action} on {repo.full_name}: issue #{issue.get('number')}")
    
    return {
        "action": action,
        "issue_number": issue.get("number"),
        "comment_user": comment.get("user", {}).get("login")
    }


async def handle_discussion_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle discussion events."""
    action = payload.get("action")
    discussion = payload.get("discussion", {})
    
    logger.info(f"Discussion {action} on {repo.full_name}: {discussion.get('title')}")
    
    return {
        "action": action,
        "discussion_title": discussion.get("title"),
        "discussion_user": discussion.get("user", {}).get("login")
    }


async def handle_create_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle create events (branch, tag)."""
    ref_type = payload.get("ref_type")
    ref = payload.get("ref")
    
    logger.info(f"Created {ref_type} on {repo.full_name}: {ref}")
    
    return {
        "ref_type": ref_type,
        "ref": ref
    }


async def handle_delete_event(payload: Dict[str, Any], repo: Repository, db) -> Dict[str, Any]:
    """Handle delete events (branch, tag)."""
    ref_type = payload.get("ref_type")
    ref = payload.get("ref")
    
    logger.info(f"Deleted {ref_type} on {repo.full_name}: {ref}")
    
    return {
        "ref_type": ref_type,
        "ref": ref
    }


# Event handler mapping
WEBHOOK_HANDLERS = {
    "push": handle_push_event,
    "pull_request": handle_pull_request_event,
    "issues": handle_issues_event,
    "issue_comment": handle_issue_comment_event,
    "discussion": handle_discussion_event,
    "create": handle_create_event,
    "delete": handle_delete_event,
}
