import sys
from pathlib import Path
import pandas as pd
import numpy as np
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.database import engine, Base
from db.model.user_table import *
from db.model.food_table import *

def create_all_tables(food_data_path):
    print("모든 데이터베이스 테이블 생성 시작...")
    Base.metadata.create_all(engine)
    print("모든 데이터베이스 테이블 생성 완료!")

    if food_data_path is None:
        return

    print("음식 데이터 입력 시작...")
    
    # 데이터를 청크 단위로 읽기
    chunk_size = 1000
    total_rows = 0
    
    for chunk in pd.read_csv(food_data_path, encoding="utf-8", chunksize=chunk_size):
        # Create copies of the chunks to avoid SettingWithCopyWarning
        chunk = chunk.copy()
        chunk = chunk.replace({pd.NA: None})
        
        # FoodInfo 테이블에 데이터 삽입
        food_info_df = chunk.loc[:, ['food_id', 'food_name', 'data_type_code']]
        food_info_df.to_sql('food_info', engine, if_exists='append', index=False)
        
        # FoodCategory 테이블에 데이터 삽입
        category_df = chunk.loc[:, ['food_id', 'major_category_name', 
                           'medium_category_name', 'minor_category_name',
                           'detail_category_name', 'representative_food_name']]
        category_df.to_sql('food_categories', engine, if_exists='append', index=False)

        # FoodSourceInfo 테이블에 데이터 삽입
        source_info_df = chunk.loc[:, ['food_id', 'origin_name', 
                              'source_name', 'generation_method_name',
                              'reference_date']]
        source_info_df.loc[:, 'reference_date'] = pd.to_datetime(source_info_df['reference_date']).dt.date
        source_info_df.to_sql('food_source_info', engine, if_exists='append', index=False)

        # FoodCompany 테이블에 데이터 삽입
        company_df = chunk.loc[:, ['food_id', 'company_name', 'manufacturer_name', 
                         'origin_country_name', 'importer_name', 
                         'distributor_name', 'mfg_report_no']]
        # Convert scientific notation to integer for mfg_report_no
        company_df.loc[:, 'mfg_report_no'] = pd.to_numeric(company_df['mfg_report_no'], errors='coerce')
        company_df = company_df.replace({np.nan: None})
        
        # food_id를 제외한 모든 컬럼이 None인 행 제외
        columns_to_check = [col for col in company_df.columns if col != 'food_id']
        company_df = company_df[~company_df[columns_to_check].isna().all(axis=1)]
        
        if not company_df.empty:
            company_df.to_sql('food_companies', engine, if_exists='append', index=False)

        # FoodNutrition 테이블에 데이터 삽입
        nutrition_df = chunk.loc[:, ['food_id', 'weight', 'serving_size_g', 'nutrient_reference_amount_g',
                           'energy_kcal', 'moisture_g', 'protein_g', 'fat_g', 'ash_g',
                           'carbohydrate_g', 'sugars_g', 'dietary_fiber_g', 'calcium_mg',
                           'iron_mg', 'phosphorus_mg', 'potassium_mg', 'sodium_mg',
                           'vitamin_a_ug_rae', 'retinol_ug', 'beta_carotene_ug',
                           'thiamin_mg', 'riboflavin_mg', 'niacin_mg', 'vitamin_c_mg',
                           'vitamin_d_ug', 'cholesterol_mg', 'saturated_fat_g', 'trans_fat_g']]
        nutrition_df.to_sql('food_nutrition', engine, if_exists='append', index=False)

        total_rows += len(chunk)
        print(f"{total_rows}개 데이터 처리 완료")

    print("음식 데이터 입력 완료!")

if __name__ == "__main__":
    food_data_path = "db/combine_data.csv"
    create_all_tables(food_data_path)