"""Authentication and Authorization API routes."""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.telemetry import LoginRequest, TokenResponse, AuthUser
from app.telemetry.auth import AuthService, get_current_user, DEMO_USERS, ROLE_PERMISSIONS
from app.telemetry.audit import audit_service

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticate user with username and password, returning a signed JWT bearer token."""
    user = AuthService.authenticate_user(req.username, req.password)
    if not user:
        audit_service.log_event(
            actor=req.username,
            role="ANONYMOUS",
            action="LOGIN_ATTEMPT",
            entity_type="AUTH",
            reason="Invalid credentials",
            result="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthService.create_access_token(user)
    audit_service.log_event(
        actor=user.username,
        role=user.role,
        action="LOGIN_SUCCESS",
        entity_type="AUTH",
        reason="JWT issued",
        result="SUCCESS",
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=3600 * 2,
        user=user,
    )


@router.get("/me", response_model=AuthUser)
def get_me(current_user: AuthUser = Depends(get_current_user)):
    """Return profile and permissions of the currently authenticated user."""
    return current_user


@router.get("/demo-users", response_model=List[AuthUser])
def list_demo_users():
    """Return available safe demo accounts for local simulation testing."""
    users = []
    for username, u in DEMO_USERS.items():
        role = u["role"]
        users.append(AuthUser(
            username=username,
            email=u["email"],
            role=role,
            assigned_vehicle_id=u.get("assigned_vehicle_id"),
            permissions=ROLE_PERMISSIONS.get(role, []),
        ))
    return users
