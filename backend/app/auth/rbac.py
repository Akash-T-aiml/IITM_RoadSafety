"""
SmartRescue AI — Role-Based Access Control
FastAPI dependencies for extracting current user and enforcing role permissions.
"""

from enum import Enum
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import decode_access_token
from app.utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


class Role(str, Enum):
    """User roles in the SmartRescue ecosystem."""
    TRAVELLER = "traveller"
    AMBULANCE = "ambulance"
    HOSPITAL = "hospital"
    ADMIN = "admin"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency: extract and validate JWT from Authorization header.
    Returns the decoded user payload.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    return {
        "uid": uid,
        "email": payload.get("email"),
        "role": payload.get("role"),
        "name": payload.get("name"),
    }


class RoleChecker:
    """
    FastAPI dependency class for role-based authorization.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker([Role.ADMIN]))])
        async def admin_endpoint():
            ...
        
        Or inject the user:
        @router.get("/data")
        async def get_data(user=Depends(RoleChecker([Role.TRAVELLER, Role.ADMIN]))):
            ...
    """

    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        token = credentials.credentials
        payload = decode_access_token(token)

        user_role = payload.get("role")
        if user_role not in [role.value for role in self.allowed_roles]:
            logger.warning(
                f"Access denied: role '{user_role}' not in {self.allowed_roles}",
                extra={"uid": payload.get("sub")}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}",
            )

        return {
            "uid": payload.get("sub"),
            "email": payload.get("email"),
            "role": user_role,
            "name": payload.get("name"),
        }
