from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class User(Base):
    """
    Extends Supabase auth.users table.
    This model maps to the auth.users table for additional querying.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    encrypted_password = Column(String, nullable=True)
    email_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    api_keys = relationship("APIKey", back_populates="user")
    sessions = relationship("Session", back_populates="user")


class UserProfile(Base):
    """
    Additional user data beyond what Supabase stores.
    Stores GitHub profile info and custom metadata.
    """
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # GitHub OAuth data
    github_id = Column(String, unique=True, nullable=True, index=True)
    github_username = Column(String, nullable=True)
    github_avatar_url = Column(String, nullable=True)
    github_access_token = Column(String, nullable=True)  # Encrypted in production
    
    # Profile info
    display_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Settings
    email_notifications = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class APIKey(Base):
    """
    API keys for programmatic access.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # Hashed API key
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for identification
    
    # Permissions
    scopes = Column(Text, nullable=True)  # JSON array of allowed scopes
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class Session(Base):
    """
    Session management for tracking user sessions.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    
    # Session info
    refresh_token_hash = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
