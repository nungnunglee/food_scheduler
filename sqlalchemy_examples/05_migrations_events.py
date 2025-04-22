"""
05_migrations_events.py - SQLAlchemy 마이그레이션 및 이벤트 훅 예제

이 파일은 다음 내용을 다룹니다:
1. Alembic을 사용한 데이터베이스 마이그레이션
2. SQLAlchemy 이벤트 리스너
3. 모델 클래스에서 이벤트 후킹

Alembic은 SQLAlchemy 작성자가 만든 데이터베이스 마이그레이션 도구로,
스키마 변경을 버전 관리하고 안전하게 적용할 수 있게 해줍니다.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.schema import DDL
import datetime
from typing import Any, Dict, List, Optional, Type
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 데이터베이스 연결 설정 ---
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy 이벤트 트래킹을 위한 기본 모델 클래스 ---
class TimestampMixin:
    """자동 타임스탬프 처리를 위한 Mixin 클래스"""
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class HistoryMixin:
    """모델 변경 이력 추적을 위한 Mixin 클래스"""
    __history__ = {}  # 변경 이력 저장용 딕셔너리
    
    @classmethod
    def __declare_last__(cls):
        """모델 클래스가 선언된 후 실행되는 이벤트 훅"""
        # 엔티티 변경 이력 트래킹을 위한 이벤트 리스너 설정
        event.listen(cls, 'before_update', cls._before_update)
    
    @staticmethod
    def _before_update(mapper, connection, target):
        """업데이트 전 현재 상태 저장"""
        state = inspect(target)
        changes = {}
        
        # 변경된 속성 추적
        for attr in state.attrs:
            hist = state.get_history(attr.key, True)
            if hist.has_changes():
                # 변경 전후 값 기록
                changes[attr.key] = {
                    'old': hist.deleted[0] if hist.deleted else None,
                    'new': hist.added[0] if hist.added else None
                }
        
        # 변경 내역 저장
        target.__history__[datetime.datetime.now()] = changes
        logger.info(f"변경 이력 기록: {target.__tablename__} ID: {target.id}, 변경 내역: {changes}")

# --- 모델 정의 ---
class Product(Base, TimestampMixin, HistoryMixin):
    """이벤트 훅 기능이 추가된 상품 모델"""
    __tablename__ = 'products_events'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))
    sku = Column(String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

class AuditLog(Base):
    """데이터베이스 변경 내역 로깅을 위한 감사 로그 테이블"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(10), nullable=False)  # INSERT, UPDATE, DELETE
    timestamp = Column(DateTime, default=datetime.datetime.now)
    user_id = Column(Integer)  # 실제 앱에서는 인증된 사용자 ID
    change_details = Column(String(500))
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', record_id={self.record_id}, action='{self.action}')>"

# --- 1. Alembic 마이그레이션 설정 예제 ---
"""
아래는 Alembic 마이그레이션 설정 및 사용법에 대한 설명입니다.
실제 적용을 위해서는 Alembic을 설치하고 초기화해야 합니다.

# 1. Alembic 설치
$ pip install alembic

# 2. Alembic 초기화
$ alembic init migrations

# 3. alembic.ini 파일 업데이트 (데이터베이스 연결 정보)
# sqlalchemy.url = mysql+mysqlconnector://appuser:apppassword@localhost:3306/myappdb

# 4. env.py 파일 수정 (모델 메타데이터 참조 설정)
# from sqlalchemy_examples.models import Base
# target_metadata = Base.metadata

# 5. 새 마이그레이션 생성
$ alembic revision --autogenerate -m "Create products table"

# 6. 마이그레이션 적용 (최신 버전으로)
$ alembic upgrade head

# 7. 마이그레이션 롤백 (이전 버전으로)
$ alembic downgrade -1
"""

# --- 아래는 Alembic 없이 스키마 변경을 위한 간단한 함수들 ---
def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    logger.info("테이블이 생성되었습니다.")

def drop_tables():
    """모든 테이블 삭제 (주의: 모든 데이터가 삭제됨)"""
    Base.metadata.drop_all(bind=engine)
    logger.info("테이블이 삭제되었습니다.")

def add_column_example():
    """컬럼 추가 예제 (직접 실행하지 마세요 - 설명용)"""
    # 컬럼 추가 SQL 실행
    # 이 방식은 프로덕션에서는 권장하지 않음 (Alembic 사용 권장)
    alter_stmt = DDL("ALTER TABLE products_events ADD COLUMN stock INTEGER DEFAULT 0")
    engine.execute(alter_stmt)
    logger.info("stock 컬럼이 추가되었습니다.")

# --- 2. SQLAlchemy 이벤트 리스너 설정 ---

# 세션 레벨 이벤트 리스너
@event.listens_for(SessionLocal, 'before_commit')
def receive_before_commit(session):
    """커밋 전 이벤트 리스너"""
    logger.info("트랜잭션 커밋 전 이벤트 발생")

@event.listens_for(SessionLocal, 'after_commit')
def receive_after_commit(session):
    """커밋 후 이벤트 리스너"""
    logger.info("트랜잭션 커밋 후 이벤트 발생")

@event.listens_for(SessionLocal, 'after_rollback')
def receive_after_rollback(session):
    """롤백 후 이벤트 리스너"""
    logger.info("트랜잭션 롤백 후 이벤트 발생")

# 테이블 레벨 이벤트 리스너
def audit_insert_listener(mapper, connection, target):
    """INSERT 작업 감사 로깅"""
    # 실제 앱에서는 현재 인증된 사용자 정보 추가
    log = AuditLog(
        table_name=target.__tablename__,
        record_id=target.id,
        action='INSERT',
        user_id=1,  # 예시 값
        change_details=f"New record created: {str(target)}"
    )
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'table_name': log.table_name,
            'record_id': log.record_id,
            'action': log.action,
            'user_id': log.user_id,
            'change_details': log.change_details
        }
    )
    logger.info(f"감사 로그 추가: {log.table_name} 테이블에 새 레코드 추가됨, ID: {log.record_id}")

def audit_update_listener(mapper, connection, target):
    """UPDATE 작업 감사 로깅"""
    state = inspect(target)
    changes = []
    
    # 변경된 속성 추적
    for attr in state.attrs:
        hist = state.get_history(attr.key, True)
        if hist.has_changes():
            changes.append(f"{attr.key}: {hist.deleted[0] if hist.deleted else None} -> {hist.added[0] if hist.added else None}")
    
    if changes:
        log = AuditLog(
            table_name=target.__tablename__,
            record_id=target.id,
            action='UPDATE',
            user_id=1,  # 예시 값
            change_details=f"Changes: {', '.join(changes)}"
        )
        connection.execute(
            AuditLog.__table__.insert(),
            {
                'table_name': log.table_name,
                'record_id': log.record_id,
                'action': log.action,
                'user_id': log.user_id,
                'change_details': log.change_details
            }
        )
        logger.info(f"감사 로그 추가: {log.table_name} 테이블 레코드 수정됨, ID: {log.record_id}, 변경: {', '.join(changes)}")

def audit_delete_listener(mapper, connection, target):
    """DELETE 작업 감사 로깅"""
    log = AuditLog(
        table_name=target.__tablename__,
        record_id=target.id,
        action='DELETE',
        user_id=1,  # 예시 값
        change_details=f"Record deleted: {str(target)}"
    )
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'table_name': log.table_name,
            'record_id': log.record_id,
            'action': log.action,
            'user_id': log.user_id,
            'change_details': log.change_details
        }
    )
    logger.info(f"감사 로그 추가: {log.table_name} 테이블 레코드 삭제됨, ID: {log.record_id}")

# 이벤트 리스너 등록
event.listen(Product, 'after_insert', audit_insert_listener)
event.listen(Product, 'after_update', audit_update_listener)
event.listen(Product, 'after_delete', audit_delete_listener)

# --- 테스트 함수 ---
def create_test_products():
    """테스트 상품 생성"""
    with SessionLocal() as session:
        try:
            # 상품 1 생성 및 저장
            product1 = Product(
                name="노트북",
                price=1500000,
                description="고성능 개발용 노트북",
                sku="LT-12345"
            )
            session.add(product1)
            session.flush()
            logger.info(f"상품 생성됨: {product1}")
            
            # 상품 2 생성 및 저장
            product2 = Product(
                name="스마트폰",
                price=800000,
                description="최신 안드로이드 스마트폰",
                sku="SP-67890"
            )
            session.add(product2)
            session.commit()
            logger.info(f"상품 생성됨: {product2}")
            
            return product1.id, product2.id
        except Exception as e:
            session.rollback()
            logger.error(f"상품 생성 중 오류 발생: {e}")
            return None, None

def update_product(product_id: int):
    """상품 정보 업데이트"""
    with SessionLocal() as session:
        try:
            # 상품 조회
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"상품 ID {product_id}를 찾을 수 없습니다.")
                return False
            
            # 상품 정보 이전 값 로깅
            logger.info(f"상품 업데이트 전: {product}")
            
            # 상품 정보 업데이트
            product.price = product.price * 0.9  # 10% 할인
            product.description = f"{product.description} (할인 중)"
            
            # 변경사항 커밋
            session.commit()
            logger.info(f"상품 업데이트 후: {product}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"상품 업데이트 중 오류 발생: {e}")
            return False

def delete_product(product_id: int):
    """상품 삭제"""
    with SessionLocal() as session:
        try:
            # 상품 조회
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"상품 ID {product_id}를 찾을 수 없습니다.")
                return False
            
            # 상품 삭제
            logger.info(f"상품 삭제: {product}")
            session.delete(product)
            
            # 변경사항 커밋
            session.commit()
            logger.info(f"상품 ID {product_id} 삭제됨")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"상품 삭제 중 오류 발생: {e}")
            return False

def view_audit_logs():
    """감사 로그 조회"""
    with SessionLocal() as session:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp).all()
        
        print("\n=== 감사 로그 ===")
        for log in logs:
            print(f"ID: {log.id}, 테이블: {log.table_name}, 레코드 ID: {log.record_id}, " 
                  f"작업: {log.action}, 시간: {log.timestamp}, 변경 내용: {log.change_details}")
        
        return logs

# --- 메인 코드 ---
if __name__ == "__main__":
    # 테이블 생성
    print("=== 테이블 생성 ===")
    create_tables()
    
    # 테스트 상품 생성
    print("\n=== 테스트 상품 생성 ===")
    product1_id, product2_id = create_test_products()
    
    if product1_id:
        # 상품 업데이트
        print("\n=== 상품 업데이트 ===")
        update_product(product1_id)
        
        # 상품 삭제
        print("\n=== 상품 삭제 ===")
        delete_product(product2_id)
    
    # 감사 로그 조회
    view_audit_logs()

"""
실행 결과 예시:

=== 테이블 생성 ===
2023-04-12 12:34:56,789 - __main__ - INFO - 테이블이 생성되었습니다.

=== 테스트 상품 생성 ===
2023-04-12 12:34:56,790 - __main__ - INFO - 트랜잭션 커밋 전 이벤트 발생
2023-04-12 12:34:56,791 - __main__ - INFO - 감사 로그 추가: products_events 테이블에 새 레코드 추가됨, ID: 1
2023-04-12 12:34:56,792 - __main__ - INFO - 감사 로그 추가: products_events 테이블에 새 레코드 추가됨, ID: 2
2023-04-12 12:34:56,793 - __main__ - INFO - 트랜잭션 커밋 후 이벤트 발생
2023-04-12 12:34:56,794 - __main__ - INFO - 상품 생성됨: <Product(id=2, name='스마트폰', price=800000.0)>

=== 상품 업데이트 ===
2023-04-12 12:34:56,795 - __main__ - INFO - 상품 업데이트 전: <Product(id=1, name='노트북', price=1500000.0)>
2023-04-12 12:34:56,796 - __main__ - INFO - 트랜잭션 커밋 전 이벤트 발생
2023-04-12 12:34:56,797 - __main__ - INFO - 변경 이력 기록: products_events ID: 1, 변경 내역: {'price': {'old': 1500000.0, 'new': 1350000.0}, 'description': {'old': '고성능 개발용 노트북', 'new': '고성능 개발용 노트북 (할인 중)'}}
2023-04-12 12:34:56,798 - __main__ - INFO - 감사 로그 추가: products_events 테이블 레코드 수정됨, ID: 1, 변경: price: 1500000.0 -> 1350000.0, description: 고성능 개발용 노트북 -> 고성능 개발용 노트북 (할인 중)
2023-04-12 12:34:56,799 - __main__ - INFO - 트랜잭션 커밋 후 이벤트 발생
2023-04-12 12:34:56,800 - __main__ - INFO - 상품 업데이트 후: <Product(id=1, name='노트북', price=1350000.0)>

=== 상품 삭제 ===
2023-04-12 12:34:56,801 - __main__ - INFO - 상품 삭제: <Product(id=2, name='스마트폰', price=800000.0)>
2023-04-12 12:34:56,802 - __main__ - INFO - 트랜잭션 커밋 전 이벤트 발생
2023-04-12 12:34:56,803 - __main__ - INFO - 감사 로그 추가: products_events 테이블 레코드 삭제됨, ID: 2
2023-04-12 12:34:56,804 - __main__ - INFO - 트랜잭션 커밋 후 이벤트 발생
2023-04-12 12:34:56,805 - __main__ - INFO - 상품 ID 2 삭제됨

=== 감사 로그 ===
ID: 1, 테이블: products_events, 레코드 ID: 1, 작업: INSERT, 시간: 2023-04-12 12:34:56.791234, 변경 내용: New record created: <Product(id=1, name='노트북', price=1500000.0)>
ID: 2, 테이블: products_events, 레코드 ID: 2, 작업: INSERT, 시간: 2023-04-12 12:34:56.792345, 변경 내용: New record created: <Product(id=2, name='스마트폰', price=800000.0)>
ID: 3, 테이블: products_events, 레코드 ID: 1, 작업: UPDATE, 시간: 2023-04-12 12:34:56.798765, 변경 내용: Changes: price: 1500000.0 -> 1350000.0, description: 고성능 개발용 노트북 -> 고성능 개발용 노트북 (할인 중)
ID: 4, 테이블: products_events, 레코드 ID: 2, 작업: DELETE, 시간: 2023-04-12 12:34:56.803456, 변경 내용: Record deleted: <Product(id=2, name='스마트폰', price=800000.0)>
""" 