from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re

# 회원가입 스키마
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    phone: Optional[str] = None

    @field_validator('password')
    def password_validation(cls, v):
        # 비밀번호 정책: 최소 8자, 하나 이상의 문자와 숫자, 특수문자 포함
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', v):
            raise ValueError('비밀번호는 최소 8자 이상이며, 문자, 숫자, 특수문자를 각각 하나 이상 포함해야 합니다.')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "Strong@Pwd123",
                "nickname": "홍길동",
                "phone": "01012345678"
            }
        }

# 로그인 스키마
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "Strong@Pwd123"
            }
        }

# 토큰 응답 스키마
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }

# 토큰 갱신 스키마
class RefreshToken(BaseModel):
    refresh_token: str
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

# OAuth 회원가입 스키마
class OAuthRegister(BaseModel):
    email: EmailStr
    social_code: str  # kakao, google, naver 등
    access_token: str
    nickname: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "social_code": "google",
                "access_token": "your_oauth_token",
                "nickname": "홍길동"
            }
        }

# 이메일 인증 요청 스키마
class EmailVerificationRequest(BaseModel):
    email: EmailStr

# 이메일 인증 확인 스키마
class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: str

# 회원가입 응답 스키마
class UserRegisterResponse(BaseModel):
    uuid: str
    email: str
    message: str
    status: str

# 사용자 정보 스키마
class UserInfoResponse(BaseModel):
    uuid: str
    email: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
