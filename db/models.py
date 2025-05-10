from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, Boolean, MetaData
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.sqlite import REAL # SQLite 에서 Float 대신 REAL 사용 권장

# SQLAlchemy Base 클래스 생성
Base = declarative_base()


class FoodItem(Base):
    """
    음식 영양 정보 테이블 모델 클래스
    """
    __tablename__ = 'food_items' # 데이터베이스 테이블 이름

    # 컬럼 정의 (영어 컬럼명 사용)
    food_code = Column(String(50), primary_key=True, comment='식품코드 (PK)') # 고유 식별자, PK로 설정
    food_name = Column(String(255), nullable=False, comment='식품명 (필수)') # 식품 이름, 필수값

    data_category_code = Column(String(10), comment='데이터구분코드')
    data_category_name = Column(String(100), comment='데이터구분명')
    serving_size = Column(String(50), comment='영양성분함량기준량 (문자열로 저장, 예: 100g)') # 단위가 포함될 수 있으므로 String

    # 영양 성분 (수치 데이터는 Float/REAL, Null 허용)
    energy_kcal = Column(Float, comment='에너지 (kcal)')
    water_g = Column(Float, comment='수분 (g)')
    protein_g = Column(Float, comment='단백질 (g)')
    fat_g = Column(Float, comment='지방 (g)')
    ash_g = Column(Float, comment='회분 (g)')
    carbohydrate_g = Column(Float, comment='탄수화물 (g)')
    sugar_g = Column(Float, comment='당류 (g)')
    dietary_fiber_g = Column(Float, comment='식이섬유 (g)')
    calcium_mg = Column(Float, comment='칼슘 (mg)')
    iron_mg = Column(Float, comment='철 (mg)')
    phosphorus_mg = Column(Float, comment='인 (mg)')
    potassium_mg = Column(Float, comment='칼륨 (mg)')
    sodium_mg = Column(Float, comment='나트륨 (mg)')
    vitamin_a_rae_mcg = Column(Float, comment='비타민 A (μg RAE)')
    retinol_mcg = Column(Float, comment='레티놀 (μg)')
    beta_carotene_mcg = Column(Float, comment='베타카로틴 (μg)')
    thiamin_mg = Column(Float, comment='티아민 (mg)')
    riboflavin_mg = Column(Float, comment='리보플라빈 (mg)')
    niacin_mg = Column(Float, comment='니아신 (mg)')
    vitamin_c_mg = Column(Float, comment='비타민 C (mg)')
    vitamin_d_mcg = Column(Float, comment='비타민 D (μg)')
    cholesterol_mg = Column(Float, comment='콜레스테롤 (mg)')
    saturated_fat_g = Column(Float, comment='포화지방산 (g)')
    trans_fat_g = Column(Float, comment='트랜스지방산 (g)')

    # 기타 정보
    waste_rate_percent = Column(Float, comment='폐기율 (%)')
    source_code = Column(String(50), comment='출처코드')
    source_name = Column(String(100), comment='출처명')
    food_weight = Column(String(50), comment='식품중량 (단위 포함될 수 있으므로 String)') # 예: '500g'
    is_imported = Column(Boolean, comment='수입여부 (True/False)') # CSV 값 변환 필요
    origin_country_code = Column(String(10), comment='원산지국코드')
    origin_country_name = Column(String(100), comment='원산지국명')
    manufacturing_report_no = Column(String(100), comment='품목제조보고번호')
    company_name = Column(String(100), comment='업체명')
    manufacturer_name = Column(String(100), comment='제조사명')
    importer_name = Column(String(100), comment='수입업체명')
    distributor_name = Column(String(100), comment='유통업체명')
    data_gen_method_code = Column(String(10), comment='데이터생성방법코드')
    data_gen_method_name = Column(String(100), comment='데이터생성방법명')
    data_creation_date = Column(Date, comment='데이터생성일자') # 날짜 형식
    data_reference_date = Column(Date, comment='데이터기준일자') # 날짜 형식

    def __repr__(self):
        # 객체 출력 시 표시 형식 정의
        return f"<FoodItem(food_code='{self.food_code}', food_name='{self.food_name}')>"