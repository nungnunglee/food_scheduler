"""
01_basic_connection.py - SQLAlchemy 기본 연결 및 테이블 생성 예제

이 파일은 다음 내용을 다룹니다:
1. SQLAlchemy와 MySQL 연결 설정
2. 기본 모델(테이블) 정의
3. 데이터베이스에 테이블 생성
"""

import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. 데이터베이스 연결 설정 ---
# 환경 변수에서 데이터베이스 접속 정보를 가져오거나 기본값 사용
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

# MySQL 연결 문자열 생성
# mysql+mysqlconnector: MySQL용 Python 커넥터 지정
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 데이터베이스 엔진 생성
# echo=True: 실행되는 SQL 쿼리를 콘솔에 출력 (디버깅용)
engine = create_engine(DATABASE_URL, echo=True)

# 세션 팩토리 생성
# autocommit=False: 명시적으로 commit()을 호출해야 변경사항이 적용됨
# autoflush=False: 쿼리 실행 전 자동으로 flush하지 않음
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델 정의를 위한 기본 클래스
Base = declarative_base()

# --- 2. 모델(테이블) 정의 ---
class User(Base):
    """사용자 정보를 저장하는 테이블"""
    __tablename__ = "users"  # 테이블 이름
    
    # 컬럼 정의
    id = Column(Integer, primary_key=True, index=True)  # 기본키, 인덱스 생성
    name = Column(String(50), nullable=False)  # 이름 (최대 50자, NULL 불가)
    email = Column(String(100), unique=True, nullable=False)  # 이메일 (고유값, NULL 불가)
    
    def __repr__(self):
        """객체의 문자열 표현 (디버깅용)"""
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"

# --- 3. 테이블 생성 및 연결 테스트 ---
def create_tables():
    """데이터베이스에 정의된 모든 테이블 생성"""
    try:
        # 모든 정의된 테이블 생성 (이미 존재하면 무시)
        Base.metadata.create_all(bind=engine)
        print("테이블이 성공적으로 생성되었습니다.")
        return True
    except Exception as e:
        print(f"테이블 생성 중 오류 발생: {e}")
        return False

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        # 엔진으로 직접 연결 테스트
        with engine.connect() as connection:
            print("데이터베이스에 성공적으로 연결되었습니다.")
            # 버전 등 정보 확인을 위한 SQL 실행
            result = connection.execute("SELECT VERSION()")
            version = result.scalar()
            print(f"MySQL 버전: {version}")
        return True
    except Exception as e:
        print(f"데이터베이스 연결 중 오류 발생: {e}")
        return False

# 파일이 직접 실행될 때만 아래 코드 실행
if __name__ == "__main__":
    # 1. 데이터베이스 연결 테스트
    print("\n=== 데이터베이스 연결 테스트 ===")
    test_connection()
    
    # 2. 테이블 생성
    print("\n=== 테이블 생성 ===")
    create_tables()
    
    # 3. 세션 생성 및 연결 확인
    print("\n=== 세션 생성 테스트 ===")
    try:
        # 컨텍스트 매니저를 사용한 세션 생성 (자동으로 세션 닫힘)
        with SessionLocal() as session:
            print("세션이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"세션 생성 중 오류 발생: {e}")

"""
실행 결과 예시:

=== 데이터베이스 연결 테스트 ===
2023-04-12 12:34:56,789 INFO sqlalchemy.engine.Engine SELECT VERSION()
2023-04-12 12:34:56,790 INFO sqlalchemy.engine.Engine [raw sql] {}
데이터베이스에 성공적으로 연결되었습니다.
MySQL 버전: 8.0.28

=== 테이블 생성 ===
2023-04-12 12:34:56,791 INFO sqlalchemy.engine.Engine CREATE TABLE users (
    id INTEGER NOT NULL AUTO_INCREMENT, 
    name VARCHAR(50) NOT NULL, 
    email VARCHAR(100) NOT NULL, 
    PRIMARY KEY (id)
)
2023-04-12 12:34:56,791 INFO sqlalchemy.engine.Engine [no key 0.00007s] {}
2023-04-12 12:34:56,792 INFO sqlalchemy.engine.Engine CREATE INDEX ix_users_id ON users (id)
2023-04-12 12:34:56,792 INFO sqlalchemy.engine.Engine [no key 0.00005s] {}
테이블이 성공적으로 생성되었습니다.

=== 세션 생성 테스트 ===
세션이 성공적으로 생성되었습니다.
""" 