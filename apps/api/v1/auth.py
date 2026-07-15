from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.database.models import User
from core.auth.hashing import verify_password, get_password_hash
from core.auth.jwt import create_access_token, create_refresh_token, decode_token
from contracts.dto.auth import UserRegister, UserLogin
from infrastructure.user_repository import user_repository

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)) -> dict[str, str]:
    """Registers a new user and returns user info."""
    existing_user = user_repository.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    hashed_pwd = get_password_hash(user_in.password)
    user_data = {
        "email": user_in.email,
        "hashed_password": hashed_pwd,
        "is_active": True,
        "is_superuser": False
    }
    new_user = user_repository.create(db, obj_in=user_data)
    return {"id": str(new_user.id), "email": new_user.email}

@router.post("/login")
def login(response: Response, user_in: UserLogin, db: Session = Depends(get_db)) -> dict[str, str]:
    """Authenticates user credentials and sets HttpOnly JWT access/refresh token cookies."""
    user = user_repository.get_by_email(db, email=user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store tokens in Secure, HttpOnly, SameSite cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60  # 30 mins
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {"status": "success", "message": "Successfully logged in"}

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Decodes refresh token cookie and issues new access token in HttpOnly cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing."
        )
        
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )
        
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or profile is deactivated."
        )
        
    new_access_token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60
    )
    return {"status": "success", "message": "Token successfully refreshed"}

@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    """Cleans up active cookies logging out the user session."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"status": "success", "message": "Successfully logged out"}
