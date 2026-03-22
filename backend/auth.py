"""
Authentication module for AI Sales Forecasting API.
Provides JWT-based authentication with password hashing.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "sales-forecast-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ─── Models ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"  # viewer, editor, admin


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    username: str
    role: str


# ─── In-memory user store (replace with DB in production) ─────────────────────

users_db: dict = {}


def init_default_users():
    """Create default admin user if no users exist"""
    if not users_db:
        users_db["admin"] = {
            "username": "admin",
            "hashed_password": pwd_context.hash("admin123"),
            "role": "admin"
        }
        logger.info("✅ Default admin user created (admin/admin123)")


# Initialize on module load
init_default_users()


# ─── Helper Functions ──────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            return None
        return TokenData(username=username, role=role)
    except JWTError:
        return None


# ─── Dependencies ──────────────────────────────────────────────────────────────

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """
    Get current authenticated user from JWT token.
    Returns None if no token provided (allows public access when AUTH_REQUIRED=false).
    Raises 401 if token is invalid.
    """
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

    if token is None:
        if auth_required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = users_db.get(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ─── Auth Service Functions ────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password"""
    user = users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def register_user(username: str, password: str, role: str = "viewer") -> dict:
    """Register a new user"""
    if username in users_db:
        raise ValueError(f"Username '{username}' already exists")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    if role not in ("viewer", "editor", "admin"):
        raise ValueError("Role must be one of: viewer, editor, admin")

    users_db[username] = {
        "username": username,
        "hashed_password": hash_password(password),
        "role": role
    }
    logger.info(f"✅ User registered: {username} (role: {role})")
    return {"username": username, "role": role}


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


def change_user_password(username: str, current_password: str, new_password: str) -> dict:
    """Change password for existing user"""
    user = users_db.get(username)
    if not user:
        raise ValueError("User not found")
    if not verify_password(current_password, user["hashed_password"]):
        raise ValueError("Current password is incorrect")
    if len(new_password) < 6:
        raise ValueError("New password must be at least 6 characters")

    users_db[username]["hashed_password"] = hash_password(new_password)
    logger.info(f"✅ Password changed for user: {username}")
    return {"username": username, "message": "Password changed successfully"}


def delete_user_from_db(username: str) -> dict:
    """Delete a user from the database"""
    if username not in users_db:
        raise ValueError(f"User '{username}' not found")
    if username == "admin":
        raise ValueError("Cannot delete default admin user")

    del users_db[username]
    logger.info(f"✅ User deleted: {username}")
    return {"username": username, "message": "User deleted successfully"}

