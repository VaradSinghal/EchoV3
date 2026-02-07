from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.session import Base


class RepositoryVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class WebhookEvent(str, enum.Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    DISCUSSION = "discussion"
    DISCUSSION_COMMENT = "discussion_comment"
    CREATE = "create"
    DELETE = "delete"


class Repository(Base):
    """
    GitHub repository data and configuration.
    """
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # GitHub data
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False, unique=True)  # owner/repo
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=False)
    html_url = Column(String(512), nullable=False)
    clone_url = Column(String(512), nullable=True)
    
    # Owner info
    owner_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    owner_github_login = Column(String(255), nullable=False)
    
    # Repository metadata
    visibility = Column(String(20), default="public")
    default_branch = Column(String(255), default="main")
    language = Column(String(100), nullable=True)
    
    # Stats
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    
    # Sync status
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    github_created_at = Column(DateTime(timezone=True), nullable=True)
    github_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    members = relationship("RepositoryMember", back_populates="repository", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="repository", cascade="all, delete-orphan")
    settings = relationship("RepositorySettings", back_populates="repository", uselist=False, cascade="all, delete-orphan")


class RepositoryMember(Base):
    """
    Team collaboration - users with access to a repository.
    """
    __tablename__ = "repository_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    
    # Role and permissions
    role = Column(String(20), default="member")
    permissions = Column(JSONB, default={})  # {"push": true, "pull": true, "admin": false}
    
    # Invitation status
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="members")


class Webhook(Base):
    """
    GitHub webhook configuration for a repository.
    """
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # GitHub webhook data
    github_hook_id = Column(Integer, nullable=True, index=True)
    url = Column(String(512), nullable=False)
    secret = Column(String(255), nullable=False)  # For signature verification
    
    # Configuration
    events = Column(JSONB, default=["push", "pull_request", "issues"])
    content_type = Column(String(50), default="json")
    
    # Status
    is_active = Column(Boolean, default=True)
    last_delivery_at = Column(DateTime(timezone=True), nullable=True)
    last_delivery_status = Column(String(50), nullable=True)  # "success", "failed"
    delivery_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="webhooks")


class RepositorySettings(Base):
    """
    Per-repository configuration settings.
    """
    __tablename__ = "repository_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Sync settings
    auto_sync = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=60)
    sync_branches = Column(Boolean, default=True)
    sync_contributors = Column(Boolean, default=True)
    
    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    notify_on_push = Column(Boolean, default=False)
    notify_on_pr = Column(Boolean, default=True)
    notify_on_issues = Column(Boolean, default=True)
    notify_on_discussions = Column(Boolean, default=True)
    
    # Agent settings
    agent_enabled = Column(Boolean, default=True)
    auto_create_issues = Column(Boolean, default=False)
    auto_respond_to_discussions = Column(Boolean, default=False)
    
    # Analysis settings
    analyze_codebase = Column(Boolean, default=True)
    analyze_contributors = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="settings")
