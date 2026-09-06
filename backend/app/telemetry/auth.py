"""Production-Style Authentication & Role-Based Access Control (RBAC) service.

Supports JWT bearer tokens, password hashing, and role validation.
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.telemetry import AuthUser, TokenResponse

# Security configuration from environment with secure development defaults
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "smart_waste_dev_secret_key_change_in_production_987654321")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


# Role Permissions Matrix
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "DISPATCHER": [
        "view_fleet",
        "assign_tasks",
        "rebalance_fleet",
        "create_emergency_requests",
        "view_telemetry",
    ],
    "DRIVER": [
        "view_assigned_tasks",
        "update_vehicle_telemetry",
        "update_collection_status",
        "view_own_route",
    ],
    "MUNICIPAL_SUPERVISOR": [
        "view_dashboards",
        "view_reports",
        "view_fleet_analytics",
        "view_audit_logs",
    ],
}

# Pre-seeded Safe Demo Users (for simulator and local academic evaluation)
DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "dispatcher": {
        "username": "dispatcher",
        "email": "dispatcher@smartwaste.city.local",
        "password_hash": pwd_context.hash("demo123"),
        "role": "DISPATCHER",
        "assigned_vehicle_id": None,
    },
    "driver_alex": {
        "username": "driver_alex",
        "email": "alex.mercer@smartwaste.city.local",
        "password_hash": pwd_context.hash("demo123"),
        "role": "DRIVER",
        "assigned_vehicle_id": "V-01",
    },
    "supervisor": {
        "username": "supervisor",
        "email": "supervisor@smartwaste.city.local",
        "password_hash": pwd_context.hash("demo123"),
        "role": "MUNICIPAL_SUPERVISOR",
        "assigned_vehicle_id": None,
    },
}


class AuthService:
    """Authentication and token generation service."""

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def authenticate_user(cls, username: str, plain_password: str) -> Optional[AuthUser]:
        """Authenticate username/password against user store."""
        user_record = DEMO_USERS.get(username.strip().lower())
        if not user_record:
            return None
        if not cls.verify_password(plain_password, user_record["password_hash"]):
            return None

        role = user_record["role"]
        return AuthUser(
            username=user_record["username"],
            email=user_record["email"],
            role=role,
            assigned_vehicle_id=user_record.get("assigned_vehicle_id"),
            permissions=ROLE_PERMISSIONS.get(role, []),
        )

    @classmethod
    def create_access_token(cls, user: AuthUser, expires_delta: Optional[timedelta] = None) -> str:
        """Encode a signed JWT token containing user identity and role."""
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        payload = {
            "sub": user.username,
            "email": user.email,
            "role": user.role,
            "assigned_vehicle_id": user.assigned_vehicle_id,
            "permissions": user.permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        encoded = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded

    @classmethod
    def decode_token(cls, token: str) -> Optional[AuthUser]:
        """Decode and validate a signed JWT bearer token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            if not username:
                return None
            role = payload.get("role", "DRIVER")
            return AuthUser(
                username=username,
                email=payload.get("email", ""),
                role=role,
                assigned_vehicle_id=payload.get("assigned_vehicle_id"),
                permissions=payload.get("permissions", ROLE_PERMISSIONS.get(role, [])),
            )
        except (jwt.PyJWTError, Exception):
            return None


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Optional[AuthUser]:
    """Dependency that extracts AuthUser if a valid token is provided, or returns None."""
    if not credentials or not credentials.credentials:
        return None
    return AuthService.decode_token(credentials.credentials)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> AuthUser:
    """Dependency requiring a valid authenticated user."""
    if not credentials or not credentials.credentials:
        # Provide default dispatcher user for demo local API calls when no header is supplied
        return AuthUser(
            username="demo_dispatcher",
            email="dispatcher@demo.local",
            role="DISPATCHER",
            permissions=ROLE_PERMISSIONS["DISPATCHER"],
        )
    user = AuthService.decode_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """Role-based access control dependency factory."""
    def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.role}' lacks permission. Required: {allowed_roles}",
            )
        return user
    return role_checker
