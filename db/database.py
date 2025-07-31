from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from contextlib import contextmanager
from dotenv import load_dotenv
import os

from db.db_mixin.user_mixin import UserMixin
from db.db_mixin.food_mixin import FoodMixin

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

DATABASE_URL = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'

# SQLAlchemy 2.0 스타일 Base 클래스 정의
# 이 Base 객체를 모든 모델 파일에서 임포트하여 사용합니다.
class Base(DeclarativeBase):
    pass

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 연결 사용 전에 유효성 검사
    pool_size=10,            # 풀에 최소 10개의 연결 유지
    max_overflow=20,         # 최대 20개까지 추가 연결 허용
    pool_recycle=3600,       # 1시간(3600초)마다 연결 재활용
    pool_timeout=30,         # 연결을 얻기 위해 최대 30초 대기
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DBManager(UserMixin, FoodMixin):
    """
    데이터베이스 관리 클래스
    세션을 효율적으로 관리하며 음식 및 태그 정보를 다룹니다.
    """
    
    def __init__(self):
        """DBManager 초기화"""
        self.session = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입 시 세션 시작"""
        if self.session is None:
            self.session = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 세션 종료"""
        if exc_type is not None:
            # 예외 발생 시 롤백
            if self.session:
                self.session.rollback()
        
        if self.session:
            self.session.close()
            self.session = None

    @contextmanager
    def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        if self.session is None:
            self.session = SessionLocal()
        try:
            yield self
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        

db_manager = DBManager()

class DBManagerTest:
    def __init__(self):
        self.db_manager = DBManager()

    def user_test(self):
        with self.db_manager.transaction() as manager:
            user_uuid = manager.create_user(
                nickname="test",
                email="test@test.com",
            )
            user = manager.get_user_by_uuid(user_uuid)
            print(user)

if __name__ == "__main__":
    db_manager_test = DBManagerTest()
    db_manager_test.user_test()