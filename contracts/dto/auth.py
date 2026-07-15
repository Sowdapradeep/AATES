from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    """Data Transfer Object containing user registration credentials."""
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """Data Transfer Object containing user credentials during a login request."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Access token serialization metadata wrapper."""
    access_token: str
    token_type: str = "bearer"
