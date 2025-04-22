# SQLAlchemy MySQL 예제 모음

이 저장소는 SQLAlchemy를 사용하여 MySQL 데이터베이스에 접근하는 다양한 예제를 포함하고 있습니다. 기본 기능부터 고급 기능까지 단계별로 구성되어 있습니다.

## 필수 요구사항

- Python 3.6+
- MySQL 서버 (또는 Docker로 실행)
- 필요한 Python 패키지:
  - sqlalchemy
  - mysql-connector-python
  - alembic (마이그레이션 예제용)

## 설치 방법

1. 필요한 패키지 설치:

```bash
pip install sqlalchemy mysql-connector-python alembic
```

2. MySQL 서버 준비:
   - 직접 설치하거나, 제공된 docker-compose 파일을 사용하여 Docker로 실행

```bash
docker-compose -f docker-compose-mysql.yml up -d
```

## 파일 구성

1. **01_basic_connection.py**
   - SQLAlchemy 기본 연결 설정
   - 기본 모델 정의 및 테이블 생성

2. **02_basic_crud.py**
   - 기본 CRUD 작업 (생성, 조회, 수정, 삭제)
   - 기본 필터링 및 정렬

3. **03_relationships.py**
   - 다양한 관계 모델링 (일대다, 다대다, 일대일, 자기 참조)
   - 관계 모델 쿼리 및 활용

4. **04_advanced_queries.py**
   - 고급 쿼리 기능 (조인, 집계, 서브쿼리)
   - 복합 필터링 및 정렬
   - 페이징 처리

5. **05_migrations_events.py**
   - Alembic을 사용한 데이터베이스 마이그레이션
   - SQLAlchemy 이벤트 리스너 및 트리거

6. **06_performance_best_practices.py**
   - 쿼리 성능 최적화
   - 대용량 데이터 처리
   - 모범 사례

## 사용 방법

각 파일은 독립적으로 실행할 수 있으며, 주석과 테스트 코드가 포함되어 있습니다:

```bash
python 01_basic_connection.py
python 02_basic_crud.py
# ... 기타 예제 파일
```

## 주요 기능 설명

### 기본 연결 및 모델 정의

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 연결 설정
engine = create_engine("mysql+mysqlconnector://user:password@host:port/dbname")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# 모델 정의
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
```

### 세션 관리 및 CRUD 작업

```python
# 세션 관리
with SessionLocal() as session:
    # 생성
    new_user = User(name="홍길동")
    session.add(new_user)
    
    # 조회
    user = session.query(User).filter_by(id=1).first()
    
    # 수정
    user.name = "김철수"
    
    # 삭제
    session.delete(user)
    
    # 변경사항 커밋
    session.commit()
```

### 관계 정의 및 활용

```python
# 일대다 관계
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="employees")
```

## 팁과 트릭

- **세션 관리**: 항상 `with` 구문이나 `try-finally` 블록을 사용하여 세션을 관리하세요.
- **대량 작업**: 대량 데이터 처리 시 `bulk_save_objects`, `bulk_update_mappings` 또는 `yield_per`를 사용하세요.
- **관계 로딩**: N+1 쿼리 문제를 피하기 위해 `joinedload`, `subqueryload` 등의 로딩 전략을 사용하세요.
- **성능 최적화**: 자주 사용되는 필드에는 인덱스를 추가하고, 필요한 컬럼만 선택적으로 쿼리하세요.

## 참고 자료

- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [Alembic 문서](https://alembic.sqlalchemy.org/en/latest/) 