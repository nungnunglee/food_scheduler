import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.database import SessionLocal
from db.model.food_table import *
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union, Tuple
from contextlib import contextmanager
from datetime import datetime
import uuid
import bcrypt

from db.model.user_table import UserInfo, UserAuth, Password, SocialLogin, LoginLog


class DBManager:
    """
    데이터베이스 관리 클래스
    세션을 효율적으로 관리하며 음식 및 태그 정보를 다룹니다.
    """
    
    def __init__(self):
        """DBManager 초기화"""
        self.session = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입 시 세션 시작"""
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 세션 종료"""
        if exc_type is not None:
            # 예외 발생 시 롤백
            self.rollback()
        self.close_session()
    
    def start_session(self):
        """세션 시작"""
        if self.session is None:
            self.session = SessionLocal()
        return self.session
    
    def close_session(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            self.session = None
    
    def commit(self):
        """현재 트랜잭션 커밋"""
        if self.session:
            self.session.commit()
    
    def rollback(self):
        """현재 트랜잭션 롤백"""
        if self.session:
            self.session.rollback()
    
    @contextmanager
    def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise e
    
    def get_or_create_tag(self, tag_name: str) -> FoodTag:
        """
        태그명으로 기존 태그를 조회하거나 새로운 태그를 생성합니다.
        
        Args:
            tag_name: 태그명
            
        Returns:
            FoodTag: 기존 또는 새로 생성된 태그 객체
        """
        # 세션 확인
        self.start_session()
        
        # 기존 태그 조회
        existing_tag = self.session.query(FoodTag).filter(FoodTag.tag_name == tag_name).first()
        
        if existing_tag:
            return existing_tag
        
        # 새 태그 생성
        new_tag = FoodTag(tag_name=tag_name)
        self.session.add(new_tag)
        self.session.flush()  # ID를 얻기 위해 flush 실행
        return new_tag
    
    def add_food_tags(self, food_id: str, tag_names: List[str], auto_commit: bool = True) -> bool:
        """
        음식 ID와 태그 리스트를 받아서 데이터베이스에 태그를 추가합니다.
        
        Args:
            food_id: 음식 ID (예: "D102-082290000-0001")
            tag_names: 태그명 리스트 (예: ["매운맛", "한식", "국물"])
            auto_commit: 자동 커밋 여부 (기본값: True)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
            
        Raises:
            ValueError: 음식 ID가 존재하지 않을 경우
        """
        # 세션 확인
        self.start_session()
        
        try:
            # 음식 존재 여부 확인
            food = self.session.query(FoodInfo).filter(FoodInfo.food_id == food_id).first()
            if not food:
                raise ValueError(f"음식 ID '{food_id}'가 존재하지 않습니다.")
            
            # 각 태그에 대해 처리
            for tag_name in tag_names:
                if not tag_name.strip():  # 빈 태그명 스킵
                    continue
                    
                tag_name = tag_name.strip()
                
                # 태그 조회 또는 생성
                tag = self.get_or_create_tag(tag_name)
                
                # 이미 연결된 태그인지 확인
                existing_relation = self.session.query(FoodInfoTag).filter(
                    FoodInfoTag.food_id == food_id,
                    FoodInfoTag.tag_id == tag.tag_id
                ).first()
                
                # 연결되지 않은 경우에만 새로운 관계 생성
                if not existing_relation:
                    food_tag_relation = FoodInfoTag(food_id=food_id, tag_id=tag.tag_id)
                    self.session.add(food_tag_relation)
            
            # 자동 커밋 설정에 따라 커밋
            if auto_commit:
                self.session.commit()
            
            return True
            
        except Exception as e:
            if auto_commit:
                self.session.rollback()
            raise e
    
    def get_food_tags(self, food_id: str) -> List[str]:
        """
        음식 ID로 해당 음식의 모든 태그를 조회합니다.
        
        Args:
            food_id: 음식 ID
            
        Returns:
            List[str]: 태그명 리스트
        """
        # 세션 확인
        self.start_session()
        
        tags = self.session.query(FoodTag.tag_name).join(
            FoodInfoTag, FoodTag.tag_id == FoodInfoTag.tag_id
        ).filter(FoodInfoTag.food_id == food_id).all()
        
        return [tag[0] for tag in tags]
    
    def remove_food_tags(self, food_id: str, tag_names: List[str], auto_commit: bool = True) -> bool:
        """
        음식 ID와 태그 리스트를 받아서 해당 태그들을 음식에서 제거합니다.
        
        Args:
            food_id: 음식 ID
            tag_names: 제거할 태그명 리스트
            auto_commit: 자동 커밋 여부 (기본값: True)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        # 세션 확인
        self.start_session()
        
        try:
            for tag_name in tag_names:
                if not tag_name.strip():
                    continue
                    
                tag_name = tag_name.strip()
                
                # 태그 조회
                tag = self.session.query(FoodTag).filter(FoodTag.tag_name == tag_name).first()
                if not tag:
                    continue  # 태그가 존재하지 않으면 스킵
                
                # 관계 제거
                self.session.query(FoodInfoTag).filter(
                    FoodInfoTag.food_id == food_id,
                    FoodInfoTag.tag_id == tag.tag_id
                ).delete()
            
            if auto_commit:
                self.session.commit()
            
            return True
            
        except Exception as e:
            if auto_commit:
                self.session.rollback()
            raise e
    
    def get_food_info(self, food_id: str) -> Optional[dict]:
        """
        음식 ID로 해당 음식의 정보를 조회합니다.
        
        Args:
            food_id: 음식 ID
            
        Returns:
            Optional[dict]: 음식 정보 (없으면 None)
        """
        # 세션 확인
        self.start_session()
        
        food = self.session.query(FoodInfo).filter(FoodInfo.food_id == food_id).first()
        if not food:
            return None
        
        # 태그 정보 조회
        tags = self.get_food_tags(food_id)
        
        # 기본 정보
        result = {
            'food_id': food.food_id,
            'food_name': food.food_name,
            'data_type_code': food.data_type_code,
            'tags': tags
        }
        
        # 카테고리 정보
        if food.category:
            result['category'] = {
                'major': food.category.major_category_name,
                'medium': food.category.medium_category_name,
                'minor': food.category.minor_category_name,
                'detail': food.category.detail_category_name,
                'representative': food.category.representative_food_name
            }
        
        # 영양 정보
        if food.nutrition:
            result['nutrition'] = {
                'serving_size_g': food.nutrition.serving_size_g,
                'nutrient_reference_amount_g': food.nutrition.nutrient_reference_amount_g,
                'energy_kcal': food.nutrition.energy_kcal,
                'moisture_g': food.nutrition.moisture_g,
                'protein_g': food.nutrition.protein_g,
                'fat_g': food.nutrition.fat_g,
                'ash_g': food.nutrition.ash_g,
                'carbohydrate_g': food.nutrition.carbohydrate_g,
                'sugars_g': food.nutrition.sugars_g,
                'dietary_fiber_g': food.nutrition.dietary_fiber_g,
                'calcium_mg': food.nutrition.calcium_mg,
                'iron_mg': food.nutrition.iron_mg,
                'phosphorus_mg': food.nutrition.phosphorus_mg,
                'potassium_mg': food.nutrition.potassium_mg,
                'sodium_mg': food.nutrition.sodium_mg,
                'vitamin_a_ug_rae': food.nutrition.vitamin_a_ug_rae,
                'retinol_ug': food.nutrition.retinol_ug,
                'beta_carotene_ug': food.nutrition.beta_carotene_ug,
                'thiamin_mg': food.nutrition.thiamin_mg,
                'riboflavin_mg': food.nutrition.riboflavin_mg,
                'niacin_mg': food.nutrition.niacin_mg,
                'vitamin_c_mg': food.nutrition.vitamin_c_mg,
                'vitamin_d_ug': food.nutrition.vitamin_d_ug,
                'cholesterol_mg': food.nutrition.cholesterol_mg,
                'saturated_fat_g': food.nutrition.saturated_fat_g,
                'trans_fat_g': food.nutrition.trans_fat_g
            }
        
        return result
    
    def search_foods_by_name(self, name_keyword: str, limit: int = 10) -> List[dict]:
        """
        음식 이름으로 검색합니다.
        
        Args:
            name_keyword: 검색 키워드
            limit: 결과 제한 수 (기본값: 10)
            
        Returns:
            List[dict]: 검색된 음식 정보 리스트
        """
        # 세션 확인
        self.start_session()
        
        foods = self.session.query(FoodInfo).filter(
            FoodInfo.food_name.like(f"%{name_keyword}%")
        ).limit(limit).all()
        
        result = []
        for food in foods:
            food_info = {
                'food_id': food.food_id,
                'food_name': food.food_name,
                'tags': self.get_food_tags(food.food_id)
            }
            result.append(food_info)
        
        return result
    
    def search_foods_by_tag(self, tag_name: str, limit: int = 10) -> List[dict]:
        """
        태그명으로 음식을 검색합니다.
        
        Args:
            tag_name: 태그명
            limit: 결과 제한 수 (기본값: 10)
            
        Returns:
            List[dict]: 검색된 음식 정보 리스트
        """
        # 세션 확인
        self.start_session()
        
        foods = self.session.query(FoodInfo).join(
            FoodInfoTag, FoodInfo.food_id == FoodInfoTag.food_id
        ).join(
            FoodTag, FoodInfoTag.tag_id == FoodTag.tag_id
        ).filter(
            FoodTag.tag_name == tag_name
        ).limit(limit).all()
        
        result = []
        for food in foods:
            food_info = {
                'food_id': food.food_id,
                'food_name': food.food_name,
                'tags': self.get_food_tags(food.food_id)
            }
            result.append(food_info)
        
        return result
    
    def get_all_tags(self) -> List[str]:
        """
        모든 태그를 조회합니다.
        
        Returns:
            List[str]: 모든 태그명 리스트
        """
        # 세션 확인
        self.start_session()
        
        tags = self.session.query(FoodTag).all()
        return tags
        # return [tag[0] for tag in tags]

    # 사용자 관련 메서드
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
        # 세션 확인
        self.start_session()
        
        # 이메일 중복 확인
        existing_user = self.session.query(UserAuth).filter(UserAuth.email == email).first()
        if existing_user:
            raise ValueError(f"이메일 '{email}'은(는) 이미 등록되어 있습니다.")
            
        # UUID 생성
        user_uuid = str(uuid.uuid4())
        
        # 비밀번호 해싱
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
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
            
            self.session.commit()
            
            return {
                "uuid": user_uuid,
                "email": email,
                "nickname": user_info.nickname
            }
            
        except Exception as e:
            self.session.rollback()
            raise e
            
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
        # 세션 확인
        self.start_session()
        
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
        
        try:
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
            
        except Exception as e:
            self.session.rollback()
            raise e
    
    def verify_user(self, email: str, password: str) -> Union[Dict[str, Any], None]:
        """
        사용자 로그인 정보를 검증합니다.
        
        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호
            
        Returns:
            Dict: 검증 성공 시 사용자 정보, 실패 시 None
        """
        # 세션 확인
        self.start_session()
        
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
        # 세션 확인
        self.start_session()
        
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
        # 세션 확인
        self.start_session()
        
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
        # 세션 확인
        self.start_session()
        
        try:
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
            
        except Exception as e:
            self.session.rollback()
            raise e
    
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
        # 세션 확인
        self.start_session()
        
        try:
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
            
        except Exception as e:
            self.session.rollback()
            return False


# 예시 코드
if __name__ == "__main__":
    # DBManager 사용 예시
    db = DBManager()
    
    try:
        # 컨텍스트 매니저를 사용한 예제
        with db as manager:
            # 태그 추가
            manager.add_food_tags("D102-082290000-0001", ["매운맛", "한식", "국물요리"])
            
            # 태그 조회
            tags = manager.get_food_tags("D102-082290000-0001")
            print(f"현재 태그들: {tags}")
            
            # 여러 작업을 하나의 트랜잭션으로 처리
            with manager.transaction():
                manager.add_food_tags("D102-082290000-0001", ["신선한"], auto_commit=False)
                manager.remove_food_tags("D102-082290000-0001", ["매운맛"], auto_commit=False)
                # 트랜잭션 컨텍스트 종료 시 자동 커밋
        
        # 다른 방식의 사용 예시
        db2 = DBManager()
        db2.start_session()
        
        # 음식 검색
        foods = db2.search_foods_by_name("국밥")
        print(f"국밥 검색 결과: {len(foods)}개")
        
        # 태그로 검색
        tag_foods = db2.search_foods_by_tag("한식")
        print(f"'한식' 태그 음식: {len(tag_foods)}개")
        
        # 트랜잭션 사용
        try:
            db2.session.begin()
            db2.add_food_tags("D102-082290000-0001", ["새로운태그1", "새로운태그2"], auto_commit=False)
            db2.session.commit()
        except Exception as e:
            db2.session.rollback()
            print(f"오류 발생: {e}")
        finally:
            db2.close_session()
        
    except Exception as e:
        print(f"오류 발생: {e}")