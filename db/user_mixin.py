from db.tables.user_table import UserInfo, UserAuth, Password, SocialLogin, LoginLog
from datetime import datetime
from typing import Dict, Any, Union
import uuid
import bcrypt


class UserMixin:
    
    def create_user(self, email: str, password: str, nickname: str = None, phone: str = None) -> Dict[str, Any]:
        """
        새로운 사용자를 생성합니다.
        
        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호
            nickname: 사용자 닉네임 (옵션)
            phone: 사용자 전화번호 (옵션)
            
        Returns:
            Dict: 생성된 사용자 정보
            
        Raises:
            ValueError: 이미 등록된 이메일인 경우
        """
        
        # 이메일 중복 확인
        existing_user = self.session.query(UserAuth).filter(UserAuth.email == email).first()
        if existing_user:
            raise ValueError(f"이메일 '{email}'은(는) 이미 등록되어 있습니다.")
            
        # UUID 생성
        user_uuid = str(uuid.uuid4())
        
        # 비밀번호 해싱
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # UserInfo 테이블 생성
        user_info = UserInfo(
            uuid=user_uuid,
            nickname=nickname or f"사용자{user_uuid[:8]}"
        )
        self.session.add(user_info)
        
        # UserAuth 테이블 생성
        user_auth = UserAuth(
            uuid=user_uuid,
            email=email,
            phone=phone
        )
        self.session.add(user_auth)
        
        # Password 테이블 생성
        password_record = Password(
            uuid=user_uuid,
            password=hashed_password.decode('utf-8')
        )
        self.session.add(password_record)
        
        return {
            "uuid": user_uuid,
            "email": email,
            "nickname": user_info.nickname
        }
            
    def create_oauth_user(self, email: str, social_code: str, access_token: str, nickname: str = None) -> Dict[str, Any]:
        """
        OAuth를 통해 새로운 사용자를 생성합니다.
        
        Args:
            email: 사용자 이메일
            social_code: 소셜 로그인 제공자 코드 (google, kakao, naver 등)
            access_token: OAuth 액세스 토큰
            nickname: 사용자 닉네임 (옵션)
            
        Returns:
            Dict: 생성된 사용자 정보 또는 기존 사용자 정보
        """
        
        # 이메일 중복 확인
        existing_auth = self.session.query(UserAuth).filter(UserAuth.email == email).first()
        
        # 이미 가입된 사용자인 경우
        if existing_auth:
            # 기존 소셜 로그인 정보 업데이트
            social_login = self.session.query(SocialLogin).filter(SocialLogin.uuid == existing_auth.uuid).first()
            
            if social_login:
                social_login.social_code = social_code
                social_login.access_token = access_token
                social_login.update_date = datetime.now()
            else:
                # 일반 계정이었으나 소셜 로그인을 연결하는 경우
                social_login = SocialLogin(
                    uuid=existing_auth.uuid,
                    social_code=social_code,
                    access_token=access_token
                )
                self.session.add(social_login)
                
            self.session.commit()
            
            user_info = self.session.query(UserInfo).filter(UserInfo.uuid == existing_auth.uuid).first()
            
            return {
                "uuid": existing_auth.uuid,
                "email": email,
                "nickname": user_info.nickname if user_info else None,
                "status": "existing"
            }
            
        # 새 사용자 등록
        user_uuid = str(uuid.uuid4())
        
        # UserInfo 테이블 생성
        user_info = UserInfo(
            uuid=user_uuid,
            nickname=nickname or f"사용자{user_uuid[:8]}"
        )
        self.session.add(user_info)
        
        # UserAuth 테이블 생성
        user_auth = UserAuth(
            uuid=user_uuid,
            email=email,
            phone=None
        )
        self.session.add(user_auth)
        
        # SocialLogin 테이블 생성
        social_login = SocialLogin(
            uuid=user_uuid,
            social_code=social_code,
            access_token=access_token
        )
        self.session.add(social_login)
        
        self.session.commit()
        
        return {
            "uuid": user_uuid,
            "email": email,
            "nickname": user_info.nickname,
            "status": "new"
        }
    
    def verify_user(self, email: str, password: str) -> Union[Dict[str, Any], None]:
        """
        사용자 로그인 정보를 검증합니다.
        
        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호
            
        Returns:
            Dict: 검증 성공 시 사용자 정보, 실패 시 None
        """
        
        # 사용자 조회
        user_auth = self.session.query(UserAuth).filter(UserAuth.email == email).first()
        if not user_auth:
            return None
            
        # 비밀번호 조회
        password_record = self.session.query(Password).filter(Password.uuid == user_auth.uuid).first()
        if not password_record:
            return None
            
        # 비밀번호 검증
        if not bcrypt.checkpw(password.encode('utf-8'), password_record.password.encode('utf-8')):
            return None
            
        # 사용자 정보 조회
        user_info = self.session.query(UserInfo).filter(UserInfo.uuid == user_auth.uuid).first()
        
        return {
            "uuid": user_auth.uuid,
            "email": email,
            "nickname": user_info.nickname if user_info else None
        }
    
    def get_user_by_uuid(self, uuid: str) -> Union[Dict[str, Any], None]:
        """
        UUID로 사용자 정보를 조회합니다.
        
        Args:
            uuid: 사용자 UUID
            
        Returns:
            Dict: 사용자 정보, 없으면 None
        """
        
        # 사용자 정보 조회
        user_info = self.session.query(UserInfo).filter(UserInfo.uuid == uuid).first()
        if not user_info:
            return None
            
        user_auth = self.session.query(UserAuth).filter(UserAuth.uuid == uuid).first()
        
        return {
            "uuid": uuid,
            "email": user_auth.email if user_auth else None,
            "phone": user_auth.phone if user_auth else None,
            "nickname": user_info.nickname
        }
    
    def get_user_by_email(self, email: str) -> Union[Dict[str, Any], None]:
        """
        이메일로 사용자 정보를 조회합니다.
        
        Args:
            email: 사용자 이메일
            
        Returns:
            Dict: 사용자 정보, 없으면 None
        """
        
        # 사용자 인증 정보 조회
        user_auth = self.session.query(UserAuth).filter(UserAuth.email == email).first()
        if not user_auth:
            return None
            
        # 사용자 정보 조회
        user_info = self.session.query(UserInfo).filter(UserInfo.uuid == user_auth.uuid).first()
        
        return {
            "uuid": user_auth.uuid,
            "email": email,
            "phone": user_auth.phone,
            "nickname": user_info.nickname if user_info else None
        }
    
    def update_user_info(self, uuid: str, **kwargs) -> bool:
        """
        사용자 정보를 업데이트합니다.
        
        Args:
            uuid: 사용자 UUID
            **kwargs: 업데이트할 정보 (nickname, phone 등)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        
        # 사용자 정보 조회
        user_info = self.session.query(UserInfo).filter(UserInfo.uuid == uuid).first()
        if not user_info:
            return False
            
        # UserInfo 테이블 업데이트
        if 'nickname' in kwargs and kwargs['nickname']:
            user_info.nickname = kwargs['nickname']
            
        # UserAuth 테이블 업데이트
        user_auth = self.session.query(UserAuth).filter(UserAuth.uuid == uuid).first()
        if user_auth:
            if 'phone' in kwargs:
                user_auth.phone = kwargs['phone']
            if 'email' in kwargs:
                # 이메일 중복 확인
                existing_email = self.session.query(UserAuth).filter(
                    UserAuth.email == kwargs['email'],
                    UserAuth.uuid != uuid
                ).first()
                if existing_email:
                    raise ValueError(f"이메일 '{kwargs['email']}'은(는) 이미 등록되어 있습니다.")
                user_auth.email = kwargs['email']
        
        # 비밀번호 업데이트
        if 'password' in kwargs and kwargs['password']:
            password_record = self.session.query(Password).filter(Password.uuid == uuid).first()
            if password_record:
                hashed_password = bcrypt.hashpw(kwargs['password'].encode('utf-8'), bcrypt.gensalt())
                password_record.password = hashed_password.decode('utf-8')
                password_record.update_date = datetime.now()
        
        self.session.commit()
        return True
        
    def record_login(self, uuid: str, status_code: int, ip: str) -> bool:
        """
        사용자 로그인 기록을 저장합니다.
        
        Args:
            uuid: 사용자 UUID
            status_code: 로그인 상태 코드 (성공: 200, 실패: 401 등)
            ip: 접속 IP 주소
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        
        # 로그인 기록 생성
        login_log = LoginLog(
            uuid=uuid,
            status_code=status_code,
            ip=ip,
            datetime=datetime.now()
        )
        self.session.add(login_log)
        self.session.commit()
        return True
            
