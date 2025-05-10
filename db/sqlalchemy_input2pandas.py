import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String
) # text는 SQL 쿼리를 직접 실행할 때 필요할 수 있습니다 (여기서는 to_sql 사용).
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
load_dotenv()

# --- 1. 데이터 준비 (Pandas DataFrame 생성) ---
# 실제 사용 시에는 이 부분을 pd.read_csv('파일경로.csv'), pd.read_excel('파일경로.xlsx') 등으로 대체하여
# 파일로부터 데이터를 읽어오거나, 다른 방식으로 DataFrame을 생성하면 됩니다.

def get_df(file_path=None):
    if file_path is None:
        data = {
            'id': [1, 2, 3, 4],
            '이름': ['홍길동', '이순신', '강감찬', '유관순'],
            '나이': [30, 45, 55, 18]
        }
        df = pd.DataFrame(data)
    else:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = None
    print("df 생성 완료")
    return df

db_connection_str = f'mysql+mysqlconnector://{os.getenv("MYSQL_USER")}:{os.getenv("MYSQL_PASSWORD")}@{os.getenv("MYSQL_HOST")}:{os.getenv("MYSQL_PORT")}/{os.getenv("MYSQL_DATABASE")}'

def gemini_create_table():
    try:
        db_connection = create_engine(db_connection_str)
        print("--- 데이터베이스 연결 성공 ---")
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return
    try:
        df = get_df("source/20250408_음식DB.xlsx")

        table_name = 'foodDB_20250408'  # 원하는 테이블 이름으로 지정하세요.
        df.to_sql(name=table_name, con=db_connection, if_exists='append', index=False)

    except Exception as e:
        print(f"데이터 저장 중 오류 발생: {e}")

    finally:
        if 'db_connection' in locals() and db_connection:
            db_connection.dispose()
            print("--- 데이터베이스 연결 리소스 해제 완료 ---")


def create_table2df(df):
    db_connection = create_engine(db_connection_str)
    df = get_df("source/20250408_음식DB.xlsx")

    Base = declarative_base()

    class FoodTable(Base):
        __tablename__ = 'food_table'  # 테이블 이름 정의

        food_id = Column(String(50), primary_key=True, index=True, nullable=False)  # 기본 키, 자동 증가
        food_name = Column(String(50), unique=True, index=True, nullable=False)  # 사용자 이름, 고유값, 필수
        email = Column(String(100), unique=True, index=True, nullable=False)  # 이메일, 고유값, 필수


if __name__ == "__main__":
    ...