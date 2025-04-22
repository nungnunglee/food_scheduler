"""
06_performance_best_practices.py - SQLAlchemy 성능 최적화 및 모범 사례

이 파일은 다음 내용을 다룹니다:
1. 쿼리 성능 최적화 기법
2. 대용량 데이터 처리
3. 캐싱 전략
4. SQLAlchemy 사용 모범 사례
"""

import os
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload, contains_eager, subqueryload
from sqlalchemy.pool import QueuePool
import datetime
import random

# --- 데이터베이스 연결 설정 ---
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

# 성능 최적화를 위한 연결 풀 설정
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # SQL 로깅 비활성화 (성능 향상)
    pool_size=5,  # 연결 풀 크기
    max_overflow=10,  # 최대 초과 연결 수
    pool_timeout=30,  # 연결 타임아웃 (초)
    pool_recycle=1800  # 연결 재활용 시간 (초)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 모델 정의 ---
class Supplier(Base):
    """공급업체 정보"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_email = Column(String(100))
    
    # 관계: 이 공급업체의 제품들
    products = relationship("PerformanceProduct", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}')>"

class Category(Base):
    """제품 카테고리"""
    __tablename__ = 'perf_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # 관계: 이 카테고리에 속한 제품들
    products = relationship("PerformanceProduct", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class PerformanceProduct(Base):
    """제품 정보 (성능 테스트용)"""
    __tablename__ = 'perf_products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)  # 인덱스 추가
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    sku = Column(String(20), unique=True, nullable=False)
    
    # 외래키
    category_id = Column(Integer, ForeignKey('perf_categories.id'), nullable=False, index=True)  # 인덱스 추가
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)  # 인덱스 추가
    
    # 관계
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

# --- 1. 쿼리 성능 최적화 기법 ---
def create_sample_data(num_products=1000):
    """대량의 샘플 데이터 생성"""
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as session:
        # 카테고리 생성
        categories = [
            Category(name="전자제품"),
            Category(name="의류"),
            Category(name="식품"),
            Category(name="도서")
        ]
        session.add_all(categories)
        session.flush()
        
        # 공급업체 생성
        suppliers = [
            Supplier(name="전자나라", contact_email="electronic@example.com"),
            Supplier(name="의류왕국", contact_email="clothing@example.com"),
            Supplier(name="식품천국", contact_email="food@example.com"),
            Supplier(name="도서출판", contact_email="books@example.com")
        ]
        session.add_all(suppliers)
        session.flush()
        
        # 대량 제품 생성
        print(f"샘플 제품 {num_products}개 생성 중...")
        
        # 배치 처리를 위한 제품 리스트
        products = []
        batch_size = 100
        
        for i in range(1, num_products + 1):
            category_id = categories[i % len(categories)].id
            supplier_id = suppliers[i % len(suppliers)].id
            price = round(random.uniform(1000, 100000), 2)
            
            product = PerformanceProduct(
                name=f"제품 {i}",
                price=price,
                stock=random.randint(0, 100),
                sku=f"SKU-{i:06d}",
                category_id=category_id,
                supplier_id=supplier_id
            )
            products.append(product)
            
            # 배치 처리: 100개씩 커밋
            if i % batch_size == 0:
                session.add_all(products)
                session.commit()
                products = []
                print(f"  {i}/{num_products} 처리 완료")
        
        # 남은 제품 처리
        if products:
            session.add_all(products)
            session.commit()
        
        print("샘플 데이터 생성 완료")

# --- 효율적인 쿼리 전략 ---
def benchmark_query(query_func, name, iterations=3):
    """쿼리 성능 벤치마크"""
    total_time = 0
    results = None
    
    for i in range(iterations):
        start_time = time.time()
        results = query_func()
        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time
    
    avg_time = total_time / iterations
    print(f"{name}: {avg_time:.4f}초 (평균, {iterations}회 실행)")
    return results, avg_time

def run_query_comparisons():
    """다양한 쿼리 전략 비교"""
    print("\n=== 쿼리 전략 성능 비교 ===")
    
    # 1. 기본 조인 쿼리
    def basic_query():
        with SessionLocal() as session:
            products = session.query(PerformanceProduct).filter(
                PerformanceProduct.price > 50000
            ).all()
            
            # N+1 문제 발생: 각 제품마다 추가 쿼리 실행
            for product in products:
                _ = product.category.name
                _ = product.supplier.name
            
            return products
    
    # 2. 즉시 로딩(Eager Loading)을 사용한 쿼리
    def eager_loading_query():
        with SessionLocal() as session:
            products = session.query(PerformanceProduct).options(
                joinedload(PerformanceProduct.category),
                joinedload(PerformanceProduct.supplier)
            ).filter(
                PerformanceProduct.price > 50000
            ).all()
            
            # N+1 문제 해결: 미리 모든 관계를 로드
            for product in products:
                _ = product.category.name
                _ = product.supplier.name
            
            return products
    
    # 3. 서브쿼리 로딩을 사용한 쿼리
    def subquery_loading_query():
        with SessionLocal() as session:
            products = session.query(PerformanceProduct).options(
                subqueryload(PerformanceProduct.category),
                subqueryload(PerformanceProduct.supplier)
            ).filter(
                PerformanceProduct.price > 50000
            ).all()
            
            for product in products:
                _ = product.category.name
                _ = product.supplier.name
            
            return products
    
    # 4. 명시적 조인을 사용한 쿼리 (데이터 중복 가능성)
    def explicit_join_query():
        with SessionLocal() as session:
            products = session.query(PerformanceProduct).join(
                PerformanceProduct.category
            ).join(
                PerformanceProduct.supplier
            ).options(
                contains_eager(PerformanceProduct.category),
                contains_eager(PerformanceProduct.supplier)
            ).filter(
                PerformanceProduct.price > 50000
            ).all()
            
            for product in products:
                _ = product.category.name
                _ = product.supplier.name
            
            return products
    
    # 5. 효율적인 필드 선택 (특정 컬럼만 선택)
    def select_columns_query():
        with SessionLocal() as session:
            results = session.query(
                PerformanceProduct.id,
                PerformanceProduct.name,
                PerformanceProduct.price,
                Category.name.label('category_name'),
                Supplier.name.label('supplier_name')
            ).join(
                Category,
                PerformanceProduct.category_id == Category.id
            ).join(
                Supplier,
                PerformanceProduct.supplier_id == Supplier.id
            ).filter(
                PerformanceProduct.price > 50000
            ).all()
            
            return results
    
    # 각 쿼리 전략 벤치마크
    benchmark_query(basic_query, "1. 기본 쿼리 (N+1 문제 발생)")
    benchmark_query(eager_loading_query, "2. 즉시 로딩(Eager Loading)")
    benchmark_query(subquery_loading_query, "3. 서브쿼리 로딩")
    benchmark_query(explicit_join_query, "4. 명시적 조인")
    benchmark_query(select_columns_query, "5. 특정 컬럼만 선택")

# --- 2. 대용량 데이터 처리 ---
def bulk_operations_example():
    """대용량 데이터에 대한 벌크 작업 예제"""
    print("\n=== 대용량 데이터 처리 ===")
    
    # 1. ORM 방식의 개별 업데이트 (느림)
    def orm_individual_updates():
        start_time = time.time()
        updated_count = 0
        
        with SessionLocal() as session:
            # 가격이 80,000원 이상인 제품들
            products = session.query(PerformanceProduct).filter(
                PerformanceProduct.price >= 80000
            ).all()
            
            # 각 제품을 개별적으로 업데이트
            for product in products:
                product.price = product.price * 0.9  # 10% 할인
                updated_count += 1
            
            session.commit()
        
        end_time = time.time()
        print(f"ORM 개별 업데이트: {updated_count}개 제품, {end_time - start_time:.4f}초 소요")
    
    # 2. 벌크 업데이트 (빠름)
    def bulk_update():
        start_time = time.time()
        
        with SessionLocal() as session:
            # 한 번의 쿼리로 모든 해당 제품 업데이트
            result = session.query(PerformanceProduct).filter(
                PerformanceProduct.price >= 80000
            ).update(
                {PerformanceProduct.price: PerformanceProduct.price * 1.1},  # 10% 가격 인상
                synchronize_session=False
            )
            
            session.commit()
        
        end_time = time.time()
        print(f"벌크 업데이트: {result}개 제품, {end_time - start_time:.4f}초 소요")
    
    # 3. 원시 SQL 사용 (더 빠름)
    def raw_sql_update():
        start_time = time.time()
        
        with engine.connect() as connection:
            result = connection.execute(
                text("UPDATE perf_products SET price = price * 0.95 WHERE price >= 70000")
            )
            
        end_time = time.time()
        print(f"원시 SQL 업데이트: {result.rowcount}개 제품, {end_time - start_time:.4f}초 소요")
    
    # 벌크 처리 예제 실행
    orm_individual_updates()
    bulk_update()
    raw_sql_update()
    
    print("\n=== 청크 단위 처리 예제 ===")
    # 대용량 데이터 청크 단위 처리
    def process_in_chunks():
        with SessionLocal() as session:
            # 전체 레코드 수 확인
            total_count = session.query(func.count(PerformanceProduct.id)).scalar()
            chunk_size = 100
            processed = 0
            
            print(f"총 {total_count}개 레코드를 {chunk_size}개씩 처리 중...")
            start_time = time.time()
            
            # 청크 단위로 처리
            for offset in range(0, total_count, chunk_size):
                # 청크 가져오기
                products_chunk = session.query(PerformanceProduct).limit(chunk_size).offset(offset).all()
                
                # 각 제품에 대한 가공 작업 (예시)
                for product in products_chunk:
                    # 메모리 사용량을 줄이기 위해 세션에서 분리
                    session.expunge(product)
                    processed += 1
                
                # 청크 처리 후 세션 정리
                session.expire_all()
                
                if (offset + chunk_size) % 500 == 0 or (offset + chunk_size) >= total_count:
                    print(f"  {min(offset + chunk_size, total_count)}/{total_count} 처리 완료")
            
            end_time = time.time()
            print(f"청크 단위 처리 완료: {processed}개 레코드, {end_time - start_time:.4f}초 소요")
    
    process_in_chunks()

# --- 3. 메모리 최적화 및 모범 사례 ---
def best_practices_demo():
    """SQLAlchemy 모범 사례 데모"""
    print("\n=== SQLAlchemy 모범 사례 ===")
    
    print("1. 세션 관리 - 컨텍스트 매니저 사용")
    with SessionLocal() as session:
        # 컨텍스트 매니저 사용 (with 문) - 자동으로 세션 닫힘
        product_count = session.query(func.count(PerformanceProduct.id)).scalar()
        print(f"  제품 수: {product_count}")
    
    print("\n2. yield_per를 사용한 스트리밍 쿼리 (대용량 데이터)")
    with SessionLocal() as session:
        # yield_per: 지정된 개수만큼만 메모리에 로드하여 처리
        start_time = time.time()
        count = 0
        
        for product in session.query(PerformanceProduct).yield_per(100):
            # 대용량 데이터를 한 번에 메모리에 로드하지 않고 처리
            count += 1
            # 실제 작업 수행
            if count % 500 == 0:
                print(f"  {count}개 처리 중...")
        
        end_time = time.time()
        print(f"  yield_per로 {count}개 레코드 처리: {end_time - start_time:.4f}초")
    
    print("\n3. 효율적인 레코드 존재 여부 확인")
    with SessionLocal() as session:
        # 비효율적 방법 (레코드 전체를 가져옴)
        start_time = time.time()
        product = session.query(PerformanceProduct).filter(PerformanceProduct.id == 1).first()
        exists_inefficient = product is not None
        end_time = time.time()
        time_inefficient = end_time - start_time
        
        # 효율적 방법 (존재 여부만 확인)
        start_time = time.time()
        exists_efficient = session.query(
            session.query(PerformanceProduct).filter(PerformanceProduct.id == 1).exists()
        ).scalar()
        end_time = time.time()
        time_efficient = end_time - start_time
        
        print(f"  비효율적 방법: {time_inefficient:.6f}초 (full record)")
        print(f"  효율적 방법: {time_efficient:.6f}초 (EXISTS)")
    
    print("\n4. 인덱스 활용 중요성")
    with SessionLocal() as session:
        # 인덱스 칼럼 활용 쿼리
        start_time = time.time()
        product_by_sku = session.query(PerformanceProduct).filter(
            PerformanceProduct.sku == "SKU-000100"
        ).first()
        end_time = time.time()
        time_with_index = end_time - start_time
        
        # 비인덱스 칼럼 활용 쿼리
        start_time = time.time()
        product_by_name = session.query(PerformanceProduct).filter(
            PerformanceProduct.name == "제품 100"
        ).first()
        end_time = time.time()
        time_without_index = end_time - start_time
        
        print(f"  인덱스 활용 쿼리(sku): {time_with_index:.6f}초")
        print(f"  일반 칼럼 쿼리(name): {time_without_index:.6f}초")

# --- 메인 코드 ---
if __name__ == "__main__":
    # 샘플 데이터 생성 (필요 시 주석 해제)
    create_sample_data(num_products=2000)
    
    # 쿼리 전략 비교
    run_query_comparisons()
    
    # 대용량 데이터 처리
    bulk_operations_example()
    
    # 모범 사례 데모
    best_practices_demo()

"""
실행 결과 예시:

샘플 제품 2000개 생성 중...
  100/2000 처리 완료
  200/2000 처리 완료
  ...
  2000/2000 처리 완료
샘플 데이터 생성 완료

=== 쿼리 전략 성능 비교 ===
1. 기본 쿼리 (N+1 문제 발생): 0.1234초 (평균, 3회 실행)
2. 즉시 로딩(Eager Loading): 0.0456초 (평균, 3회 실행)
3. 서브쿼리 로딩: 0.0567초 (평균, 3회 실행)
4. 명시적 조인: 0.0345초 (평균, 3회 실행)
5. 특정 컬럼만 선택: 0.0234초 (평균, 3회 실행)

=== 대용량 데이터 처리 ===
ORM 개별 업데이트: 245개 제품, 0.0789초 소요
벌크 업데이트: 270개 제품, 0.0123초 소요
원시 SQL 업데이트: 293개 제품, 0.0045초 소요

=== 청크 단위 처리 예제 ===
총 2000개 레코드를 100개씩 처리 중...
  500/2000 처리 완료
  1000/2000 처리 완료
  1500/2000 처리 완료
  2000/2000 처리 완료
청크 단위 처리 완료: 2000개 레코드, 0.1234초 소요

=== SQLAlchemy 모범 사례 ===
1. 세션 관리 - 컨텍스트 매니저 사용
  제품 수: 2000

2. yield_per를 사용한 스트리밍 쿼리 (대용량 데이터)
  500개 처리 중...
  1000개 처리 중...
  1500개 처리 중...
  2000개 처리 중...
  yield_per로 2000개 레코드 처리: 0.0567초

3. 효율적인 레코드 존재 여부 확인
  비효율적 방법: 0.000456초 (full record)
  효율적 방법: 0.000123초 (EXISTS)

4. 인덱스 활용 중요성
  인덱스 활용 쿼리(sku): 0.000345초
  일반 칼럼 쿼리(name): 0.000567초
""" 