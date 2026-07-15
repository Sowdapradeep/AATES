from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.database.models import User
from core.auth.jwt import decode_token

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency resolver pulling the user reference from JWT stored in HttpOnly cookies or Bearer Header."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated."
        )
        
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID context is missing."
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user profile."
        )
    return user

class PermissionChecker:
    """RBAC validation handler ensuring the authenticated user contains the requested permission."""
    
    def __init__(self, permission_name: str) -> None:
        self.permission_name = permission_name

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
            
        for role in current_user.roles:
            for perm in role.permissions:
                if perm.name == self.permission_name:
                    return current_user
                    
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Missing permission '{self.permission_name}'"
        )

def require_permission(permission_name: str) -> Depends:
    """Helper generator returning permission validation dependencies."""
    return Depends(PermissionChecker(permission_name))
