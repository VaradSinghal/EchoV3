"""
Repository API Endpoints
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.session import get_db
from app.db.models import UserProfile
from app.db.models_repo import Repository, RepositoryMember, RepositorySettings, Webhook
from app.services.github import GitHubService, generate_webhook_secret, parse_github_datetime

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


# ============ Schemas ============

class RepositoryCreate(BaseModel):
    full_name: str  # owner/repo format

class RepositoryResponse(BaseModel):
    id: str
    github_id: int
    name: str
    full_name: str
    description: Optional[str]
    html_url: str
    visibility: str
    default_branch: str
    language: Optional[str]
    stars_count: int
    forks_count: int
    open_issues_count: int
    is_active: bool
    last_synced_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class RepositorySettingsUpdate(BaseModel):
    auto_sync: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    notify_on_push: Optional[bool] = None
    notify_on_pr: Optional[bool] = None
    notify_on_issues: Optional[bool] = None
    agent_enabled: Optional[bool] = None
    auto_create_issues: Optional[bool] = None

class BranchResponse(BaseModel):
    name: str
    protected: bool

class WebhookResponse(BaseModel):
    id: str
    github_hook_id: Optional[int]
    events: List[str]
    is_active: bool
    last_delivery_at: Optional[datetime]
    last_delivery_status: Optional[str]


# ============ Helper Functions ============

async def get_current_user_id(request: Request) -> str:
    """Extract user ID from JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    return payload.sub


async def get_github_service(user_id: str, db: Session) -> GitHubService:
    """Get GitHub service with user's access token."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile or not profile.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected"
        )
    return GitHubService(profile.github_access_token)


# ============ Endpoints ============

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    request: Request,
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """List all repositories for the current user."""
    user_id = await get_current_user_id(request)
    
    query = db.query(Repository).filter(Repository.owner_id == user_id)
    if not include_inactive:
        query = query.filter(Repository.is_active == True)
    
    repos = query.order_by(Repository.updated_at.desc()).all()
    return [RepositoryResponse(
        id=str(r.id),
        github_id=r.github_id,
        name=r.name,
        full_name=r.full_name,
        description=r.description,
        html_url=r.html_url,
        visibility=r.visibility,
        default_branch=r.default_branch,
        language=r.language,
        stars_count=r.stars_count,
        forks_count=r.forks_count,
        open_issues_count=r.open_issues_count,
        is_active=r.is_active,
        last_synced_at=r.last_synced_at
    ) for r in repos]


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def add_repository(
    repo_data: RepositoryCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Add a new repository to track."""
    user_id = await get_current_user_id(request)
    github = await get_github_service(user_id, db)
    
    # Parse owner/repo
    parts = repo_data.full_name.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository format. Use owner/repo"
        )
    owner, repo_name = parts
    
    # Check if already exists
    existing = db.query(Repository).filter(
        Repository.full_name == repo_data.full_name,
        Repository.owner_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already added"
        )
    
    # Fetch from GitHub
    try:
        github_repo = await github.get_repository(owner, repo_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found or no access: {str(e)}"
        )
    
    # Create repository record
    new_repo = Repository(
        github_id=github_repo["id"],
        name=github_repo["name"],
        full_name=github_repo["full_name"],
        description=github_repo.get("description"),
        url=github_repo["url"],
        html_url=github_repo["html_url"],
        clone_url=github_repo.get("clone_url"),
        owner_id=user_id,
        owner_github_login=github_repo["owner"]["login"],
        visibility=github_repo.get("visibility", "public"),
        default_branch=github_repo.get("default_branch", "main"),
        language=github_repo.get("language"),
        stars_count=github_repo.get("stargazers_count", 0),
        forks_count=github_repo.get("forks_count", 0),
        open_issues_count=github_repo.get("open_issues_count", 0),
        watchers_count=github_repo.get("watchers_count", 0),
        github_created_at=parse_github_datetime(github_repo.get("created_at")),
        github_updated_at=parse_github_datetime(github_repo.get("updated_at")),
        last_synced_at=datetime.utcnow()
    )
    db.add(new_repo)
    db.flush()
    
    # Create default settings
    settings = RepositorySettings(repository_id=new_repo.id)
    db.add(settings)
    
    db.commit()
    db.refresh(new_repo)
    
    return RepositoryResponse(
        id=str(new_repo.id),
        github_id=new_repo.github_id,
        name=new_repo.name,
        full_name=new_repo.full_name,
        description=new_repo.description,
        html_url=new_repo.html_url,
        visibility=new_repo.visibility,
        default_branch=new_repo.default_branch,
        language=new_repo.language,
        stars_count=new_repo.stars_count,
        forks_count=new_repo.forks_count,
        open_issues_count=new_repo.open_issues_count,
        is_active=new_repo.is_active,
        last_synced_at=new_repo.last_synced_at
    )


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get repository details."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    return RepositoryResponse(
        id=str(repo.id),
        github_id=repo.github_id,
        name=repo.name,
        full_name=repo.full_name,
        description=repo.description,
        html_url=repo.html_url,
        visibility=repo.visibility,
        default_branch=repo.default_branch,
        language=repo.language,
        stars_count=repo.stars_count,
        forks_count=repo.forks_count,
        open_issues_count=repo.open_issues_count,
        is_active=repo.is_active,
        last_synced_at=repo.last_synced_at
    )


@router.put("/{repo_id}")
async def update_repository_settings(
    repo_id: UUID,
    settings_update: RepositorySettingsUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update repository settings."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    settings = db.query(RepositorySettings).filter(
        RepositorySettings.repository_id == repo_id
    ).first()
    
    if not settings:
        settings = RepositorySettings(repository_id=repo_id)
        db.add(settings)
    
    # Update settings
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    db.commit()
    
    return {"message": "Settings updated successfully"}


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """Remove repository from tracking."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    db.delete(repo)
    db.commit()
    
    return {"message": "Repository removed successfully"}


@router.post("/{repo_id}/sync")
async def sync_repository(
    repo_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """Manually sync repository data from GitHub."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    github = await get_github_service(user_id, db)
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
        
        return {"message": "Repository synced successfully", "last_synced_at": repo.last_synced_at}
        
    except Exception as e:
        repo.sync_error = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/{repo_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    repo_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """List branches for a repository."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    github = await get_github_service(user_id, db)
    parts = repo.full_name.split("/")
    
    try:
        branches = await github.list_branches(parts[0], parts[1])
        return [BranchResponse(name=b["name"], protected=b.get("protected", False)) for b in branches]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch branches: {str(e)}"
        )


@router.get("/{repo_id}/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    repo_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """List webhooks for a repository."""
    user_id = await get_current_user_id(request)
    
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    
    webhooks = db.query(Webhook).filter(Webhook.repository_id == repo_id).all()
    
    return [WebhookResponse(
        id=str(w.id),
        github_hook_id=w.github_hook_id,
        events=w.events,
        is_active=w.is_active,
        last_delivery_at=w.last_delivery_at,
        last_delivery_status=w.last_delivery_status
    ) for w in webhooks]
