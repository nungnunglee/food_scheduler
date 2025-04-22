"""
04_advanced_queries.py - SQLAlchemy 고급 쿼리 기능 예제

이 파일은 다음 내용을 다룹니다:
1. 조인(JOIN) 쿼리
2. 집계(Aggregation) 함수
3. 서브쿼리(Subquery)
4. 고급 필터링
5. 정렬 및 페이징
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, func, desc, and_, or_, case
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, aliased
from datetime import datetime

# --- 데이터베이스 연결 설정 ---
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)  # echo=False로 설정하여 SQL 로그 출력 제한
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 모델 정의 ---
class Category(Base):
    """상품 카테고리"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # 관계: 이 카테고리에 속한 상품들
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Product(Base):
    """상품 정보"""
    __tablename__ = 'products_adv'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    
    # 관계: 이 상품이 속한 카테고리
    category = relationship("Category", back_populates="products")
    
    # 관계: 이 상품의 주문 내역
    order_items = relationship("OrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, stock={self.stock})>"

class Customer(Base):
    """고객 정보"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    address = Column(String(200))
    
    # 관계: 이 고객이 생성한 주문들
    orders = relationship("Order", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}')>"

class Order(Base):
    """주문 정보"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_date = Column(String(10), nullable=False)  # YYYY-MM-DD 형식
    status = Column(String(20), nullable=False, default='pending')  # pending, completed, cancelled
    
    # 관계: 이 주문을 생성한 고객
    customer = relationship("Customer", back_populates="orders")
    
    # 관계: 이 주문에 포함된 상품 항목들
    items = relationship("OrderItem", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, customer_id={self.customer_id}, order_date='{self.order_date}', status='{self.status}')>"

class OrderItem(Base):
    """주문 항목 정보 (주문과 상품의 다대다 관계를 위한 중간 테이블)"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products_adv.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # 주문 시점의 가격
    
    # 관계: 이 항목이 속한 주문
    order = relationship("Order", back_populates="items")
    
    # 관계: 이 항목의 상품
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"

# --- 테이블 생성 및 샘플 데이터 추가 ---
def create_tables_and_samples():
    """테이블 생성 및 샘플 데이터 추가"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as session:
        # 카테고리 데이터 생성
        categories = [
            Category(name="전자제품"),
            Category(name="의류"),
            Category(name="식품"),
            Category(name="도서")
        ]
        session.add_all(categories)
        session.flush()
        
        # 상품 데이터 생성
        products = [
            # 전자제품
            Product(name="노트북", price=1200000, stock=10, category_id=categories[0].id),
            Product(name="스마트폰", price=800000, stock=20, category_id=categories[0].id),
            Product(name="태블릿", price=500000, stock=15, category_id=categories[0].id),
            Product(name="무선이어폰", price=180000, stock=30, category_id=categories[0].id),
            # 의류
            Product(name="티셔츠", price=25000, stock=100, category_id=categories[1].id),
            Product(name="청바지", price=50000, stock=80, category_id=categories[1].id),
            Product(name="패딩", price=120000, stock=50, category_id=categories[1].id),
            # 식품
            Product(name="과일세트", price=35000, stock=20, category_id=categories[2].id),
            Product(name="고기세트", price=75000, stock=15, category_id=categories[2].id),
            # 도서
            Product(name="파이썬 프로그래밍", price=28000, stock=40, category_id=categories[3].id),
            Product(name="데이터베이스 이론", price=32000, stock=35, category_id=categories[3].id)
        ]
        session.add_all(products)
        session.flush()
        
        # 고객 데이터 생성
        customers = [
            Customer(name="김고객", email="kim@example.com", address="서울시 강남구"),
            Customer(name="이고객", email="lee@example.com", address="서울시 서초구"),
            Customer(name="박고객", email="park@example.com", address="경기도 성남시"),
            Customer(name="최고객", email="choi@example.com", address="인천시 남동구")
        ]
        session.add_all(customers)
        session.flush()
        
        # 주문 및 주문 항목 데이터 생성
        orders = [
            # 김고객의 주문
            Order(customer_id=customers[0].id, order_date="2023-01-15", status="completed"),
            Order(customer_id=customers[0].id, order_date="2023-03-20", status="completed"),
            # 이고객의 주문
            Order(customer_id=customers[1].id, order_date="2023-02-10", status="completed"),
            # 박고객의 주문
            Order(customer_id=customers[2].id, order_date="2023-03-05", status="completed"),
            Order(customer_id=customers[2].id, order_date="2023-04-10", status="pending"),
            # 최고객의 주문
            Order(customer_id=customers[3].id, order_date="2023-04-01", status="cancelled")
        ]
        session.add_all(orders)
        session.flush()
        
        # 주문 항목 데이터
        order_items = [
            # 김고객의 첫 번째 주문
            OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=1, price=products[0].price),  # 노트북
            OrderItem(order_id=orders[0].id, product_id=products[3].id, quantity=1, price=products[3].price),  # 무선이어폰
            
            # 김고객의 두 번째 주문
            OrderItem(order_id=orders[1].id, product_id=products[4].id, quantity=2, price=products[4].price),  # 티셔츠 2개
            OrderItem(order_id=orders[1].id, product_id=products[5].id, quantity=1, price=products[5].price),  # 청바지
            
            # 이고객의 주문
            OrderItem(order_id=orders[2].id, product_id=products[1].id, quantity=1, price=products[1].price),  # 스마트폰
            OrderItem(order_id=orders[2].id, product_id=products[9].id, quantity=1, price=products[9].price),  # 파이썬 프로그래밍
            
            # 박고객의 첫 번째 주문
            OrderItem(order_id=orders[3].id, product_id=products[7].id, quantity=1, price=products[7].price),  # 과일세트
            OrderItem(order_id=orders[3].id, product_id=products[8].id, quantity=1, price=products[8].price),  # 고기세트
            
            # 박고객의 두 번째 주문
            OrderItem(order_id=orders[4].id, product_id=products[2].id, quantity=1, price=products[2].price),  # 태블릿
            
            # 최고객의 주문 (취소됨)
            OrderItem(order_id=orders[5].id, product_id=products[6].id, quantity=1, price=products[6].price),  # 패딩
            OrderItem(order_id=orders[5].id, product_id=products[10].id, quantity=1, price=products[10].price)  # 데이터베이스 이론
        ]
        session.add_all(order_items)
        
        # 모든 변경사항 커밋
        session.commit()
        print("샘플 데이터가 성공적으로 생성되었습니다.")

# --- 1. 조인(JOIN) 쿼리 ---
def join_queries():
    """다양한 조인 쿼리 예제"""
    with SessionLocal() as session:
        print("\n=== 1. 내부 조인(INNER JOIN) ===")
        # 상품과 카테고리 조인
        results = session.query(
            Product.name.label('product_name'),
            Product.price,
            Category.name.label('category_name')
        ).join(Category).all()
        
        print("상품별 카테고리 정보:")
        for result in results:
            print(f"상품: {result.product_name}, 가격: {result.price:,}원, 카테고리: {result.category_name}")
        
        print("\n=== 2. 여러 테이블 조인 ===")
        # 주문, 고객, 주문항목, 상품 조인
        results = session.query(
            Order.id.label('order_id'),
            Customer.name.label('customer_name'),
            Product.name.label('product_name'),
            OrderItem.quantity,
            OrderItem.price,
            (OrderItem.quantity * OrderItem.price).label('subtotal')
        ).join(Customer).join(OrderItem).join(Product).all()
        
        print("주문 상세 정보:")
        for result in results:
            print(f"주문 ID: {result.order_id}, 고객: {result.customer_name}, "
                  f"상품: {result.product_name}, 수량: {result.quantity}, "
                  f"가격: {result.price:,}원, 소계: {result.subtotal:,}원")
        
        print("\n=== 3. 외부 조인(LEFT OUTER JOIN) ===")
        # 고객과 주문 외부 조인 (주문이 없는 고객도 포함)
        results = session.query(
            Customer.name.label('customer_name'),
            Customer.email,
            Order.id.label('order_id'),
            Order.order_date,
            Order.status
        ).outerjoin(Order).all()
        
        print("고객별 주문 정보 (외부 조인):")
        for result in results:
            order_info = f"주문 ID: {result.order_id}, 날짜: {result.order_date}, 상태: {result.status}" if result.order_id else "주문 없음"
            print(f"고객: {result.customer_name}, 이메일: {result.email}, {order_info}")

# --- 2. 집계(Aggregation) 함수 ---
def aggregation_queries():
    """집계 함수를 사용한 쿼리 예제"""
    with SessionLocal() as session:
        print("\n=== 1. 기본 집계 함수 ===")
        # 상품 수, 평균 가격, 최소/최대 가격
        result = session.query(
            func.count(Product.id).label('total_products'),
            func.avg(Product.price).label('avg_price'),
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price'),
            func.sum(Product.price * Product.stock).label('inventory_value')
        ).one()
        
        print(f"총 상품 수: {result.total_products}")
        print(f"평균 가격: {result.avg_price:,.2f}원")
        print(f"최저 가격: {result.min_price:,}원")
        print(f"최고 가격: {result.max_price:,}원")
        print(f"재고 가치 합계: {result.inventory_value:,}원")
        
        print("\n=== 2. GROUP BY를 사용한 집계 ===")
        # 카테고리별 상품 수, 평균 가격
        results = session.query(
            Category.name.label('category_name'),
            func.count(Product.id).label('product_count'),
            func.avg(Product.price).label('avg_price'),
            func.sum(Product.stock).label('total_stock')
        ).join(Category).group_by(Category.name).all()
        
        print("카테고리별 상품 통계:")
        for result in results:
            print(f"카테고리: {result.category_name}, 상품 수: {result.product_count}, "
                  f"평균 가격: {result.avg_price:,.2f}원, 총 재고: {result.total_stock}개")
        
        print("\n=== 3. HAVING을 사용한 필터링 ===")
        # 평균 가격이 50,000원 이상인 카테고리
        results = session.query(
            Category.name.label('category_name'),
            func.avg(Product.price).label('avg_price')
        ).join(Category).group_by(Category.name).having(func.avg(Product.price) > 50000).all()
        
        print("평균 가격이 50,000원 이상인 카테고리:")
        for result in results:
            print(f"카테고리: {result.category_name}, 평균 가격: {result.avg_price:,.2f}원")
        
        print("\n=== 4. 주문 관련 집계 ===")
        # 고객별 총 주문 금액
        results = session.query(
            Customer.name.label('customer_name'),
            func.sum(OrderItem.quantity * OrderItem.price).label('total_spent')
        ).join(Order).join(OrderItem).group_by(Customer.name).all()
        
        print("고객별 총 지출액:")
        for result in results:
            print(f"고객: {result.customer_name}, 총 지출액: {result.total_spent:,}원")

# --- 3. 서브쿼리(Subquery) ---
def subquery_examples():
    """서브쿼리 사용 예제"""
    with SessionLocal() as session:
        print("\n=== 1. 서브쿼리를 사용한 필터링 ===")
        # 평균 가격보다 비싼 상품 찾기
        subq = session.query(func.avg(Product.price)).scalar_subquery()
        products = session.query(Product).filter(Product.price > subq).all()
        
        print(f"평균 가격보다 비싼 상품 ({subq:,.2f}원 초과):")
        for product in products:
            print(f"{product.name}: {product.price:,}원")
        
        print("\n=== 2. 상관 서브쿼리(Correlated Subquery) ===")
        # 각 카테고리에서 가장 비싼 상품 찾기
        subq = session.query(
            func.max(Product.price)
        ).filter(
            Product.category_id == Category.id
        ).scalar_subquery()
        
        results = session.query(
            Category.name.label('category_name'),
            Product.name.label('product_name'),
            Product.price
        ).join(Category).filter(
            Product.price == subq
        ).all()
        
        print("각 카테고리에서 가장 비싼 상품:")
        for result in results:
            print(f"카테고리: {result.category_name}, 상품: {result.product_name}, 가격: {result.price:,}원")
        
        print("\n=== 3. FROM 절에 서브쿼리 사용 ===")
        # 고객별 주문 횟수 조회
        subq = session.query(
            Order.customer_id,
            func.count(Order.id).label('order_count')
        ).group_by(Order.customer_id).subquery()
        
        results = session.query(
            Customer.name,
            Customer.email,
            subq.c.order_count
        ).join(
            subq,
            Customer.id == subq.c.customer_id
        ).all()
        
        print("고객별 주문 횟수:")
        for result in results:
            print(f"고객: {result.name}, 이메일: {result.email}, 주문 횟수: {result.order_count}회")

# --- 4. 고급 필터링 ---
def advanced_filtering():
    """고급 필터링 사용 예제"""
    with SessionLocal() as session:
        print("\n=== 1. 복합 조건 필터링 ===")
        # 가격이 500,000원 이상이거나 재고가 50개 이상인 상품
        products = session.query(Product).filter(
            or_(
                Product.price >= 500000,
                Product.stock >= 50
            )
        ).all()
        
        print("가격이 500,000원 이상이거나 재고가 50개 이상인 상품:")
        for product in products:
            print(f"{product.name}: 가격 {product.price:,}원, 재고 {product.stock}개")
        
        print("\n=== 2. LIKE 및 IN 연산자 ===")
        # 이름에 '폰'이 포함되거나 가격이 특정 범위에 있는 상품
        products = session.query(Product).filter(
            or_(
                Product.name.like('%폰%'),
                Product.price.in_([25000, 50000, 75000])
            )
        ).all()
        
        print("이름에 '폰'이 포함되거나 가격이 25,000원, 50,000원, 75,000원인 상품:")
        for product in products:
            print(f"{product.name}: {product.price:,}원")
        
        print("\n=== 3. CASE 문 사용 ===")
        # 가격대별 상품 분류
        results = session.query(
            Product.name,
            Product.price,
            case(
                [
                    (Product.price < 50000, "저가"),
                    (Product.price < 500000, "중가")
                ],
                else_="고가"
            ).label('price_category')
        ).all()
        
        print("가격대별 상품 분류:")
        for result in results:
            print(f"{result.name}: {result.price:,}원 ({result.price_category})")

# --- 5. 정렬 및 페이징 ---
def sorting_and_paging():
    """정렬 및 페이징 사용 예제"""
    with SessionLocal() as session:
        print("\n=== 1. 정렬(ORDER BY) ===")
        # 가격 내림차순으로 상품 정렬
        products = session.query(Product).order_by(desc(Product.price)).all()
        
        print("가격 내림차순 상품 목록:")
        for product in products:
            print(f"{product.name}: {product.price:,}원")
        
        print("\n=== 2. 복합 정렬 ===")
        # 카테고리 이름 오름차순, 가격 내림차순 정렬
        results = session.query(
            Category.name.label('category_name'),
            Product.name.label('product_name'),
            Product.price
        ).join(Category).order_by(
            Category.name,
            desc(Product.price)
        ).all()
        
        print("카테고리별, 가격 내림차순 정렬:")
        current_category = None
        for result in results:
            if current_category != result.category_name:
                current_category = result.category_name
                print(f"\n카테고리: {current_category}")
            print(f"  - {result.product_name}: {result.price:,}원")
        
        print("\n=== 3. 페이징(LIMIT/OFFSET) ===")
        # 페이지 크기: 3, 페이지 번호: 2 (두 번째 페이지)
        page_size = 3
        page_number = 2
        offset = (page_number - 1) * page_size
        
        products = session.query(Product).order_by(Product.price).limit(page_size).offset(offset).all()
        
        total_count = session.query(func.count(Product.id)).scalar()
        total_pages = (total_count + page_size - 1) // page_size
        
        print(f"페이지: {page_number}/{total_pages} (전체 상품 수: {total_count})")
        for product in products:
            print(f"{product.name}: {product.price:,}원")

# --- 메인 코드 ---
if __name__ == "__main__":
    # 테이블 생성 및 샘플 데이터 추가
    print("=== 테이블 생성 및 샘플 데이터 추가 ===")
    create_tables_and_samples()
    
    # 고급 쿼리 예제 실행
    join_queries()
    aggregation_queries()
    subquery_examples()
    advanced_filtering()
    sorting_and_paging()

"""
실행 결과 예시:

=== 테이블 생성 및 샘플 데이터 추가 ===
샘플 데이터가 성공적으로 생성되었습니다.

=== 1. 내부 조인(INNER JOIN) ===
상품별 카테고리 정보:
상품: 노트북, 가격: 1,200,000원, 카테고리: 전자제품
상품: 스마트폰, 가격: 800,000원, 카테고리: 전자제품
...

=== 2. 여러 테이블 조인 ===
주문 상세 정보:
주문 ID: 1, 고객: 김고객, 상품: 노트북, 수량: 1, 가격: 1,200,000원, 소계: 1,200,000원
...

=== 1. 기본 집계 함수 ===
총 상품 수: 11
평균 가격: 267,727.27원
최저 가격: 25,000원
최고 가격: 1,200,000원
재고 가치 합계: 53,700,000원

=== 2. GROUP BY를 사용한 집계 ===
카테고리별 상품 통계:
카테고리: 전자제품, 상품 수: 4, 평균 가격: 670,000.00원, 총 재고: 75개
...

=== 1. 서브쿼리를 사용한 필터링 ===
평균 가격보다 비싼 상품 (267,727.27원 초과):
노트북: 1,200,000원
스마트폰: 800,000원
...

=== 1. 복합 조건 필터링 ===
가격이 500,000원 이상이거나 재고가 50개 이상인 상품:
노트북: 가격 1,200,000원, 재고 10개
...

=== 1. 정렬(ORDER BY) ===
가격 내림차순 상품 목록:
노트북: 1,200,000원
스마트폰: 800,000원
...

=== 3. 페이징(LIMIT/OFFSET) ===
페이지: 2/4 (전체 상품 수: 11)
청바지: 50,000원
태블릿: 500,000원
패딩: 120,000원
""" 