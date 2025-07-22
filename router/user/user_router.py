from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request, Header, Response
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime, timedelta
import uuid
import os
import sys
import bcrypt
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette.status import HTTP_401_UNAUTHORIZED

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB 모듈 임포트
from db.database import SessionLocal
from db.model.user_table import UserInfo, UserAuth, Password, SocialLogin
from db.db_manager import DBManager
from model.schemas.user import UserRegister, UserLogin, Token, RefreshToken, UserRegisterResponse, UserInfoResponse, EmailVerificationRequest, EmailVerificationConfirm, OAuthRegister

# 환경변수 로드
load_dotenv()

# 이메일 설정값
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "food_scheduler_secret_key_for_jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

user_router = APIRouter(prefix="/user", tags=["user"])

# 인메모리 저장소 - 이메일 인증 코드 저장
verification_tokens = {}

# 이메일 인증 코드 전송 함수
def send_verification_email(email: str, code: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = "식품 스케줄러 - 이메일 인증"
        
        body = f"""
        <html>
          <body>
            <h2>이메일 인증 코드</h2>
            <p>안녕하세요! 식품 스케줄러 회원가입을 위한 인증 코드입니다.</p>
            <p>인증 코드: <strong>{code}</strong></p>
            <p>이 코드는 10분간 유효합니다.</p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"이메일 전송 오류: {e}")
        return False

# JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 리프레시 토큰 생성 함수
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 현재 사용자 가져오기
async def get_current_user(token: str = Depends(oauth2_scheme), db_manager: DBManager = Depends(get_db_manager)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uuid: str = payload.get("sub")
        if uuid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db_manager.get_user_by_uuid(uuid)
    if user is None:
        raise credentials_exception
    return user

# 일반 회원가입 라우트
@user_router.post("/register", response_model=UserRegisterResponse)
async def register_user(user_data: UserRegister, db_manager: DBManager = Depends(get_db_manager)):
    try:
        # DBManager를 사용하여 사용자 생성
        user_info = db_manager.create_user(
            email=user_data.email,
            password=user_data.password,
            nickname=user_data.nickname,
            phone=user_data.phone
        )
        
        return {
            "uuid": user_info["uuid"],
            "email": user_data.email,
            "message": "회원가입이 완료되었습니다. 이메일 인증을 진행해주세요.",
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )

# 로그인 라우트
@user_router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    user_data: UserLogin, 
    request: Request,
    db_manager: DBManager = Depends(get_db_manager)
):
    # 사용자 인증
    user = db_manager.verify_user(user_data.email, user_data.password)
    if not user:
        # 실패 로그 기록
        try:
            user_info = db_manager.get_user_by_email(user_data.email)
            if user_info:
                db_manager.record_login(
                    uuid=user_info["uuid"], 
                    status_code=401, 
                    ip=request.client.host
                )
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 성공 로그 기록
    db_manager.record_login(
        uuid=user["uuid"], 
        status_code=200, 
        ip=request.client.host
    )
    
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["uuid"]}, 
        expires_delta=access_token_expires
    )
    
    # 리프레시 토큰 생성
    refresh_token = create_refresh_token(
        data={"sub": user["uuid"]}
    )
    
    # JWT 쿠키 설정
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS에서만 전송
        samesite="lax",  # CSRF 방지
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 초 단위
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위
    }

# 토큰 갱신 라우트
@user_router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    token_data: RefreshToken = None,
    refresh_token: Optional[str] = Header(None),
    cookie_refresh_token: Optional[str] = None,
    db_manager: DBManager = Depends(get_db_manager)
):
    # 리프레시 토큰 우선 순위: Body > Header > Cookie
    if token_data and token_data.refresh_token:
        token = token_data.refresh_token
    elif refresh_token:
        token = refresh_token
    elif cookie_refresh_token:
        token = cookie_refresh_token
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="리프레시 토큰이 필요합니다."
        )
    
    try:
        # 토큰 검증
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uuid = payload.get("sub")
        if uuid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 사용자 확인
        user = db_manager.get_user_by_uuid(uuid)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 새 액세스 토큰 발급
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": uuid},
            expires_delta=access_token_expires
        )
        
        # 새 리프레시 토큰 발급
        new_refresh_token = create_refresh_token(data={"sub": uuid})
        
        # JWT 쿠키 설정
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# OAuth 회원가입 라우트
@user_router.post("/oauth/register", response_model=UserRegisterResponse)
async def register_oauth_user(user_data: OAuthRegister, db_manager: DBManager = Depends(get_db_manager)):
    try:
        # DBManager를 사용하여 OAuth 사용자 생성
        user_info = db_manager.create_oauth_user(
            email=user_data.email,
            social_code=user_data.social_code,
            access_token=user_data.access_token,
            nickname=user_data.nickname
        )
        
        message = "OAuth 회원가입이 완료되었습니다."
        if user_info.get("status") == "existing":
            message = "이미 등록된 사용자입니다. 로그인을 진행합니다."
        
        return {
            "uuid": user_info["uuid"],
            "email": user_data.email,
            "message": message,
            "status": user_info.get("status", "success")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth 회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )

# 이메일 인증 코드 전송 라우트
@user_router.post("/verify/email", status_code=status.HTTP_202_ACCEPTED)
async def request_email_verification(
    request: EmailVerificationRequest, 
    background_tasks: BackgroundTasks,
    db_manager: DBManager = Depends(get_db_manager)
):
    # 해당 이메일이 등록되어 있는지 확인
    user = db_manager.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="등록되지 않은 이메일입니다."
        )
    
    # 인증 코드 생성 (6자리 숫자)
    verification_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    
    # 인증 토큰 저장
    verification_tokens[request.email] = {
        "code": verification_code,
        "expires_at": datetime.now() + timedelta(minutes=10)
    }
    
    # 백그라운드에서 이메일 전송
    background_tasks.add_task(send_verification_email, request.email, verification_code)
    
    return {"message": "인증 코드가 이메일로 전송되었습니다. 10분 내에 인증을 완료해주세요."}

# 이메일 인증 코드 확인 라우트
@user_router.post("/verify/confirm", status_code=status.HTTP_200_OK)
async def confirm_email_verification(verify: EmailVerificationConfirm):
    # 인증 코드 확인
    if verify.email not in verification_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 요청을 먼저 진행해주세요."
        )
    
    token_data = verification_tokens[verify.email]
    
    # 만료 여부 확인
    if datetime.now() > token_data["expires_at"]:
        del verification_tokens[verify.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 만료되었습니다. 다시 인증 요청을 진행해주세요."
        )
    
    # 코드 확인
    if token_data["code"] != verify.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 일치하지 않습니다."
        )
    
    # 인증 성공 후 토큰 삭제
    del verification_tokens[verify.email]
    
    return {"message": "이메일 인증이 완료되었습니다."}

# 사용자 정보 조회 라우트
@user_router.get("/me", response_model=UserInfoResponse)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "uuid": current_user["uuid"],
        "email": current_user["email"],
        "nickname": current_user["nickname"],
        "phone": current_user.get("phone")
    }

# 로그아웃 라우트
@user_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return {"message": "로그아웃 되었습니다."}