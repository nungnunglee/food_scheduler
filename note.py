from db.model.food_table import *
from db.model.user_table import *
from db.database import SessionLocal

def print_food_nutrition(uuid: str):
    with SessionLocal() as db:
        # 음식 정보와 영양성분 정보를 함께 조회
        user_info = db.query(UserInfo).filter(UserInfo.uuid == uuid).first()
        
        if user_info:

            print(f"user_info: ")
            for key, value in user_info.__dict__.items():
                print(f"{key}: {value}")

            if user_info.user_body:

                print(f"user_info.user_body: ")
                for key, value in user_info.user_body.__dict__.items():
                    print(f"{key}: {value}")

            else:
                print(f"user_info.user_body is None")
        else:
            print(f"음식 ID {uuid}에 대한 정보를 찾을 수 없습니다.")

def len_food_table():
    with SessionLocal() as db:
        food_info = db.query(FoodInfo).all()
        for idx, food in enumerate(sorted(food_info, key=lambda x: x.food_id)):
            print(f"{idx}:\t{food.food_id}: {food.food_name}")
            if idx > 10:
                break

if __name__ == "__main__":
    # 예시: 음식 ID를 입력받아 영양성분 출력
    print_food_nutrition("D101-004160000-0001")
    len_food_table()




