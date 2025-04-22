"""
02_basic_crud.py - SQLAlchemy 기본 CRUD 작업 예제

이 파일은 다음 내용을 다룹니다:
1. 데이터 생성 (Create)
2. 데이터 조회 (Read)
3. 데이터 수정 (Update)
4. 데이터 삭제 (Delete)

기본적인 CRUD 작업은 대부분의 데이터베이스 애플리케이션에서 가장 많이 사용되는 작업입니다.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# --- 데이터베이스 연결 설정 ---
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 모델 정의 ---
class Product(Base):
    """상품 정보를 저장하는 테이블"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

# 테이블 생성
Base.metadata.create_all(bind=engine)

# --- 1. 생성 (Create) 작업 ---
def create_product(session: Session, name: str, description: str, price: int):
    """새 상품을 데이터베이스에 추가"""
    try:
        # 새 상품 객체 생성
        new_product = Product(
            name=name,
            description=description,
            price=price
        )
        
        # 세션에 객체 추가
        session.add(new_product)
        
        # 변경사항 커밋 (데이터베이스에 저장)
        session.commit()
        
        # 생성된 객체의 ID 등 정보를 가져오기 위해 새로고침
        session.refresh(new_product)
        print(f"상품 생성 성공: {new_product}")
        return new_product
    
    except SQLAlchemyError as e:
        # 오류 발생 시 롤백
        session.rollback()
        print(f"상품 생성 중 오류 발생: {e}")
        return None

# --- 2. 조회 (Read) 작업 ---
def get_product_by_id(session: Session, product_id: int):
    """ID로 상품 조회"""
    product = session.query(Product).filter(Product.id == product_id).first()
    if product:
        print(f"상품 조회 성공: {product}")
    else:
        print(f"ID {product_id}에 해당하는 상품이 없습니다.")
    return product

def get_all_products(session: Session):
    """모든 상품 조회"""
    products = session.query(Product).all()
    print(f"전체 상품 수: {len(products)}")
    for product in products:
        print(f"- {product}")
    return products

def get_products_by_price_range(session: Session, min_price: int, max_price: int):
    """가격 범위로 상품 필터링"""
    products = session.query(Product).filter(
        Product.price >= min_price,
        Product.price <= max_price
    ).all()
    
    print(f"가격 범위 {min_price}~{max_price}원의 상품 수: {len(products)}")
    for product in products:
        print(f"- {product}")
    return products

# --- 3. 수정 (Update) 작업 ---
def update_product_price(session: Session, product_id: int, new_price: int):
    """상품 가격 업데이트"""
    try:
        # 업데이트할 상품 조회
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            print(f"ID {product_id}에 해당하는 상품이 없습니다.")
            return None
        
        print(f"상품 가격 변경: {product.name}, {product.price}원 -> {new_price}원")
        
        # 가격 업데이트
        product.price = new_price
        
        # 변경사항 커밋
        session.commit()
        
        # 업데이트된 정보로 새로고침
        session.refresh(product)
        print(f"상품 가격 업데이트 성공: {product}")
        return product
    
    except SQLAlchemyError as e:
        # 오류 발생 시 롤백
        session.rollback()
        print(f"상품 업데이트 중 오류 발생: {e}")
        return None

def update_product(session: Session, product_id: int, **kwargs):
    """상품 정보 여러 필드 업데이트"""
    try:
        # 업데이트할 상품 조회
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            print(f"ID {product_id}에 해당하는 상품이 없습니다.")
            return None
        
        print(f"상품 업데이트 전: {product}")
        
        # 전달된 키워드 인자로 객체 속성 업데이트
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        # 변경사항 커밋
        session.commit()
        
        # 업데이트된 정보로 새로고침
        session.refresh(product)
        print(f"상품 업데이트 성공: {product}")
        return product
    
    except SQLAlchemyError as e:
        # 오류 발생 시 롤백
        session.rollback()
        print(f"상품 업데이트 중 오류 발생: {e}")
        return None

# --- 4. 삭제 (Delete) 작업 ---
def delete_product(session: Session, product_id: int):
    """상품 삭제"""
    try:
        # 삭제할 상품 조회
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            print(f"ID {product_id}에 해당하는 상품이 없습니다.")
            return False
        
        print(f"상품 삭제: {product}")
        
        # 객체 삭제
        session.delete(product)
        
        # 변경사항 커밋
        session.commit()
        print(f"ID {product_id} 상품이 성공적으로 삭제되었습니다.")
        return True
    
    except SQLAlchemyError as e:
        # 오류 발생 시 롤백
        session.rollback()
        print(f"상품 삭제 중 오류 발생: {e}")
        return False

# --- 테스트 코드 ---
if __name__ == "__main__":
    # 세션 생성
    session = SessionLocal()
    
    try:
        print("\n=== 1. 상품 생성 테스트 ===")
        laptop = create_product(
            session, 
            name="노트북", 
            description="고성능 개발용 노트북", 
            price=1500000
        )
        
        create_product(
            session, 
            name="스마트폰", 
            description="최신형 스마트폰", 
            price=900000
        )
        
        create_product(
            session, 
            name="헤드폰", 
            description="노이즈 캔슬링 블루투스 헤드폰", 
            price=300000
        )
        
        print("\n=== 2. 상품 조회 테스트 ===")
        # 단일 상품 조회
        if laptop:
            get_product_by_id(session, laptop.id)
        
        # 모든 상품 조회
        get_all_products(session)
        
        # 가격 범위로 상품 조회
        get_products_by_price_range(session, 500000, 1000000)
        
        print("\n=== 3. 상품 업데이트 테스트 ===")
        # 가격만 업데이트
        if laptop:
            update_product_price(session, laptop.id, 1350000)
        
        # 여러 필드 업데이트
        if laptop:
            update_product(
                session,
                laptop.id,
                name="고성능 노트북",
                description="개발자용 최고급 워크스테이션 노트북"
            )
        
        # 업데이트된 상품 확인
        if laptop:
            get_product_by_id(session, laptop.id)
        
        print("\n=== 4. 상품 삭제 테스트 ===")
        # 마지막으로 추가된 상품 삭제
        products = get_all_products(session)
        if products:
            delete_product(session, products[-1].id)
        
        # 삭제 후 목록 확인
        get_all_products(session)
    
    finally:
        # 항상 세션 닫기
        session.close()

"""
실행 결과 예시:

=== 1. 상품 생성 테스트 ===
2023-04-12 12:34:56,789 INFO sqlalchemy.engine.Engine INSERT INTO products (name, description, price) VALUES (?, ?, ?)
2023-04-12 12:34:56,790 INFO sqlalchemy.engine.Engine [generated in 0.00010s] ('노트북', '고성능 개발용 노트북', 1500000)
상품 생성 성공: <Product(id=1, name='노트북', price=1500000)>
2023-04-12 12:34:56,791 INFO sqlalchemy.engine.Engine INSERT INTO products (name, description, price) VALUES (?, ?, ?)
2023-04-12 12:34:56,791 INFO sqlalchemy.engine.Engine [generated in 0.00008s] ('스마트폰', '최신형 스마트폰', 900000)
상품 생성 성공: <Product(id=2, name='스마트폰', price=900000)>
2023-04-12 12:34:56,792 INFO sqlalchemy.engine.Engine INSERT INTO products (name, description, price) VALUES (?, ?, ?)
2023-04-12 12:34:56,792 INFO sqlalchemy.engine.Engine [generated in 0.00008s] ('헤드폰', '노이즈 캔슬링 블루투스 헤드폰', 300000)
상품 생성 성공: <Product(id=3, name='헤드폰', price=300000)>

=== 2. 상품 조회 테스트 ===
2023-04-12 12:34:56,793 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.id = ?
2023-04-12 12:34:56,793 INFO sqlalchemy.engine.Engine [generated in 0.00007s] (1,)
상품 조회 성공: <Product(id=1, name='노트북', price=1500000)>
2023-04-12 12:34:56,794 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products
2023-04-12 12:34:56,794 INFO sqlalchemy.engine.Engine [generated in 0.00006s] ()
전체 상품 수: 3
- <Product(id=1, name='노트북', price=1500000)>
- <Product(id=2, name='스마트폰', price=900000)>
- <Product(id=3, name='헤드폰', price=300000)>
2023-04-12 12:34:56,795 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.price >= ? AND products.price <= ?
2023-04-12 12:34:56,795 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (500000, 1000000)
가격 범위 500000~1000000원의 상품 수: 1
- <Product(id=2, name='스마트폰', price=900000)>

=== 3. 상품 업데이트 테스트 ===
2023-04-12 12:34:56,796 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.id = ?
2023-04-12 12:34:56,796 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (1,)
상품 가격 변경: 노트북, 1500000원 -> 1350000원
2023-04-12 12:34:56,797 INFO sqlalchemy.engine.Engine UPDATE products SET price=? WHERE products.id = ?
2023-04-12 12:34:56,797 INFO sqlalchemy.engine.Engine [generated in 0.00007s] (1350000, 1)
상품 가격 업데이트 성공: <Product(id=1, name='노트북', price=1350000)>
2023-04-12 12:34:56,798 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.id = ?
2023-04-12 12:34:56,798 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (1,)
상품 업데이트 전: <Product(id=1, name='노트북', price=1350000)>
2023-04-12 12:34:56,799 INFO sqlalchemy.engine.Engine UPDATE products SET name=?, description=? WHERE products.id = ?
2023-04-12 12:34:56,799 INFO sqlalchemy.engine.Engine [generated in 0.00007s] ('고성능 노트북', '개발자용 최고급 워크스테이션 노트북', 1)
상품 업데이트 성공: <Product(id=1, name='고성능 노트북', price=1350000)>
2023-04-12 12:34:56,800 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.id = ?
2023-04-12 12:34:56,800 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (1,)
상품 조회 성공: <Product(id=1, name='고성능 노트북', price=1350000)>

=== 4. 상품 삭제 테스트 ===
2023-04-12 12:34:56,801 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products
2023-04-12 12:34:56,801 INFO sqlalchemy.engine.Engine [generated in 0.00007s] ()
전체 상품 수: 3
- <Product(id=1, name='고성능 노트북', price=1350000)>
- <Product(id=2, name='스마트폰', price=900000)>
- <Product(id=3, name='헤드폰', price=300000)>
2023-04-12 12:34:56,802 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products WHERE products.id = ?
2023-04-12 12:34:56,802 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (3,)
상품 삭제: <Product(id=3, name='헤드폰', price=300000)>
2023-04-12 12:34:56,803 INFO sqlalchemy.engine.Engine DELETE FROM products WHERE products.id = ?
2023-04-12 12:34:56,803 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (3,)
ID 3 상품이 성공적으로 삭제되었습니다.
2023-04-12 12:34:56,804 INFO sqlalchemy.engine.Engine SELECT products.id, products.name, products.description, products.price FROM products
2023-04-12 12:34:56,804 INFO sqlalchemy.engine.Engine [generated in 0.00006s] ()
전체 상품 수: 2
- <Product(id=1, name='고성능 노트북', price=1350000)>
- <Product(id=2, name='스마트폰', price=900000)>
""" 