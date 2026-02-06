from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import httpx
import secrets

from app.core.config import settings
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_password, 
    get_password_hash,
    verify_token,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db.session import get_db
from app.db.models import User, UserProfile, Session as UserSession

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ============ Schemas ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    github_username: Optional[str] = None
    github_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str


# ============ Endpoints ============

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Email/password signup.
    Creates a new user in Supabase auth.users and a corresponding profile.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user (in production, use Supabase Admin API)
    # For now, we create directly in the database
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        encrypted_password=hashed_password
    )
    db.add(new_user)
    db.flush()
    
    # Create profile
    profile = UserProfile(
        user_id=new_user.id,
        display_name=user_data.display_name
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token(str(new_user.id))
    refresh_token = create_refresh_token(str(new_user.id))
    
    return AuthResponse(
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            display_name=profile.display_name
        ),
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Email/password login.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.encrypted_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=profile.display_name if profile else None,
            github_username=profile.github_username if profile else None,
            github_avatar_url=profile.github_avatar_url if profile else None
        ),
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/github")
async def github_auth():
    """
    Initiate GitHub OAuth flow.
    Redirects to GitHub's authorization page.
    """
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email,read:user"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """
    GitHub OAuth callback.
    Exchanges code for access token and creates/updates user.
    """
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_response.json()
    
    if "error" in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=token_data.get("error_description", "Failed to authenticate with GitHub")
        )
    
    github_access_token = token_data["access_token"]
    
    # Get user info from GitHub
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json"
            }
        )
        github_user = user_response.json()
        
        # Get primary email
        emails_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json"
            }
        )
        emails = emails_response.json()
        primary_email = next(
            (e["email"] for e in emails if e.get("primary")),
            github_user.get("email")
        )
    
    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email found in GitHub account"
        )
    
    # Check if user exists by GitHub ID or email
    profile = db.query(UserProfile).filter(UserProfile.github_id == str(github_user["id"])).first()
    
    if profile:
        # Update existing user's GitHub info
        profile.github_username = github_user["login"]
        profile.github_avatar_url = github_user["avatar_url"]
        profile.github_access_token = github_access_token
        user = db.query(User).filter(User.id == profile.user_id).first()
    else:
        # Check if email exists
        user = db.query(User).filter(User.email == primary_email).first()
        if user:
            # Link GitHub to existing user
            profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if profile:
                profile.github_id = str(github_user["id"])
                profile.github_username = github_user["login"]
                profile.github_avatar_url = github_user["avatar_url"]
                profile.github_access_token = github_access_token
            else:
                profile = UserProfile(
                    user_id=user.id,
                    github_id=str(github_user["id"]),
                    github_username=github_user["login"],
                    github_avatar_url=github_user["avatar_url"],
                    github_access_token=github_access_token,
                    display_name=github_user.get("name", github_user["login"])
                )
                db.add(profile)
        else:
            # Create new user
            user = User(email=primary_email)
            db.add(user)
            db.flush()
            
            profile = UserProfile(
                user_id=user.id,
                github_id=str(github_user["id"]),
                github_username=github_user["login"],
                github_avatar_url=github_user["avatar_url"],
                github_access_token=github_access_token,
                display_name=github_user.get("name", github_user["login"])
            )
            db.add(profile)
    
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # Redirect to frontend with tokens
    frontend_callback = f"http://localhost:3000/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=frontend_callback)


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """
    Logout user by invalidating their session.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Mark all user sessions as inactive
    db.query(UserSession).filter(
        UserSession.user_id == payload.sub,
        UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Get current authenticated user.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == payload.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=profile.display_name if profile else None,
        github_username=profile.github_username if profile else None,
        github_avatar_url=profile.github_avatar_url if profile else None
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh JWT token.
    """
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user = db.query(User).filter(User.id == payload.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token
    )
