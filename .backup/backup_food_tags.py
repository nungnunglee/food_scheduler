import json
from sqlalchemy.orm import Session
from db.database import engine
from db.model.food_table import FoodInfo, FoodTag
from tqdm import tqdm
from db.db_manager import DBManager

def backup_food_tags_to_json(output_file='food_tags_backup.json'):
    """
    food_id별 태그 정보를 JSON 파일로 백업하는 함수
    """
    # 세션 생성
    session = Session(engine)
    
    try:
        # 모든 FoodInfo와 연결된 태그 가져오기
        foods_with_tags = session.query(FoodInfo).all()
        
        # JSON 형식으로 데이터 구조화
        result = dict()
        
        for food in tqdm(foods_with_tags, total=len(foods_with_tags), desc="백업 진행 중"):

            tag_names = []
            if food.tags:
                tag_names.extend([tag.tag_name for tag in food.tags])
            result[food.food_id] = tag_names
        
        # JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        print(f"태그 정보가 {output_file}에 성공적으로 저장되었습니다.")
        
    finally:
        # 세션 종료
        session.close()


if __name__ == "__main__":
    # backup_food_tags_to_json()
    db = DBManager()
    with db as manager:
        foods = manager.session.query(FoodInfo).all()
        with open("foods_backup.txt", "w", encoding="utf-8") as f:
            for food in foods:
                f.write(f"{food.food_id}, {food.food_name}\n")