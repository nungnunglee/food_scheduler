import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.database import SessionLocal
from db.model.food_table import *
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import contextmanager


class DBManager:
    """
    데이터베이스 관리 클래스
    세션을 효율적으로 관리하며 음식 및 태그 정보를 다룹니다.
    """
    
    def __init__(self):
        """DBManager 초기화"""
        self.session = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입 시 세션 시작"""
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 세션 종료"""
        if exc_type is not None:
            # 예외 발생 시 롤백
            self.rollback()
        self.close_session()
    
    def start_session(self):
        """세션 시작"""
        if self.session is None:
            self.session = SessionLocal()
        return self.session
    
    def close_session(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            self.session = None
    
    def commit(self):
        """현재 트랜잭션 커밋"""
        if self.session:
            self.session.commit()
    
    def rollback(self):
        """현재 트랜잭션 롤백"""
        if self.session:
            self.session.rollback()
    
    @contextmanager
    def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise e
    
    def get_or_create_tag(self, tag_name: str) -> FoodTag:
        """
        태그명으로 기존 태그를 조회하거나 새로운 태그를 생성합니다.
        
        Args:
            tag_name: 태그명
            
        Returns:
            FoodTag: 기존 또는 새로 생성된 태그 객체
        """
        # 세션 확인
        self.start_session()
        
        # 기존 태그 조회
        existing_tag = self.session.query(FoodTag).filter(FoodTag.tag_name == tag_name).first()
        
        if existing_tag:
            return existing_tag
        
        # 새 태그 생성
        new_tag = FoodTag(tag_name=tag_name)
        self.session.add(new_tag)
        self.session.flush()  # ID를 얻기 위해 flush 실행
        return new_tag
    
    def add_food_tags(self, food_id: str, tag_names: List[str], auto_commit: bool = True) -> bool:
        """
        음식 ID와 태그 리스트를 받아서 데이터베이스에 태그를 추가합니다.
        
        Args:
            food_id: 음식 ID (예: "D102-082290000-0001")
            tag_names: 태그명 리스트 (예: ["매운맛", "한식", "국물"])
            auto_commit: 자동 커밋 여부 (기본값: True)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
            
        Raises:
            ValueError: 음식 ID가 존재하지 않을 경우
        """
        # 세션 확인
        self.start_session()
        
        try:
            # 음식 존재 여부 확인
            food = self.session.query(FoodInfo).filter(FoodInfo.food_id == food_id).first()
            if not food:
                raise ValueError(f"음식 ID '{food_id}'가 존재하지 않습니다.")
            
            # 각 태그에 대해 처리
            for tag_name in tag_names:
                if not tag_name.strip():  # 빈 태그명 스킵
                    continue
                    
                tag_name = tag_name.strip()
                
                # 태그 조회 또는 생성
                tag = self.get_or_create_tag(tag_name)
                
                # 이미 연결된 태그인지 확인
                existing_relation = self.session.query(FoodInfoTag).filter(
                    FoodInfoTag.food_id == food_id,
                    FoodInfoTag.tag_id == tag.tag_id
                ).first()
                
                # 연결되지 않은 경우에만 새로운 관계 생성
                if not existing_relation:
                    food_tag_relation = FoodInfoTag(food_id=food_id, tag_id=tag.tag_id)
                    self.session.add(food_tag_relation)
            
            # 자동 커밋 설정에 따라 커밋
            if auto_commit:
                self.session.commit()
            
            return True
            
        except Exception as e:
            if auto_commit:
                self.session.rollback()
            raise e
    
    def get_food_tags(self, food_id: str) -> List[str]:
        """
        음식 ID로 해당 음식의 모든 태그를 조회합니다.
        
        Args:
            food_id: 음식 ID
            
        Returns:
            List[str]: 태그명 리스트
        """
        # 세션 확인
        self.start_session()
        
        tags = self.session.query(FoodTag.tag_name).join(
            FoodInfoTag, FoodTag.tag_id == FoodInfoTag.tag_id
        ).filter(FoodInfoTag.food_id == food_id).all()
        
        return [tag[0] for tag in tags]
    
    def remove_food_tags(self, food_id: str, tag_names: List[str], auto_commit: bool = True) -> bool:
        """
        음식 ID와 태그 리스트를 받아서 해당 태그들을 음식에서 제거합니다.
        
        Args:
            food_id: 음식 ID
            tag_names: 제거할 태그명 리스트
            auto_commit: 자동 커밋 여부 (기본값: True)
            
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        # 세션 확인
        self.start_session()
        
        try:
            for tag_name in tag_names:
                if not tag_name.strip():
                    continue
                    
                tag_name = tag_name.strip()
                
                # 태그 조회
                tag = self.session.query(FoodTag).filter(FoodTag.tag_name == tag_name).first()
                if not tag:
                    continue  # 태그가 존재하지 않으면 스킵
                
                # 관계 제거
                self.session.query(FoodInfoTag).filter(
                    FoodInfoTag.food_id == food_id,
                    FoodInfoTag.tag_id == tag.tag_id
                ).delete()
            
            if auto_commit:
                self.session.commit()
            
            return True
            
        except Exception as e:
            if auto_commit:
                self.session.rollback()
            raise e
    
    def get_food_info(self, food_id: str) -> Optional[dict]:
        """
        음식 ID로 해당 음식의 정보를 조회합니다.
        
        Args:
            food_id: 음식 ID
            
        Returns:
            Optional[dict]: 음식 정보 (없으면 None)
        """
        # 세션 확인
        self.start_session()
        
        food = self.session.query(FoodInfo).filter(FoodInfo.food_id == food_id).first()
        if not food:
            return None
        
        # 태그 정보 조회
        tags = self.get_food_tags(food_id)
        
        # 기본 정보
        result = {
            'food_id': food.food_id,
            'food_name': food.food_name,
            'data_type_code': food.data_type_code,
            'tags': tags
        }
        
        # 카테고리 정보
        if food.category:
            result['category'] = {
                'major': food.category.major_category_name,
                'medium': food.category.medium_category_name,
                'minor': food.category.minor_category_name,
                'detail': food.category.detail_category_name,
                'representative': food.category.representative_food_name
            }
        
        # 영양 정보
        if food.nutrition:
            result['nutrition'] = {
                'energy_kcal': float(food.nutrition.energy_kcal) if food.nutrition.energy_kcal else None,
                'protein_g': float(food.nutrition.protein_g) if food.nutrition.protein_g else None,
                'fat_g': float(food.nutrition.fat_g) if food.nutrition.fat_g else None,
                'carbohydrate_g': float(food.nutrition.carbohydrate_g) if food.nutrition.carbohydrate_g else None,
                'sugars_g': float(food.nutrition.sugars_g) if food.nutrition.sugars_g else None
            }
        
        return result
    
    def search_foods_by_name(self, name_keyword: str, limit: int = 10) -> List[dict]:
        """
        음식 이름으로 검색합니다.
        
        Args:
            name_keyword: 검색 키워드
            limit: 결과 제한 수 (기본값: 10)
            
        Returns:
            List[dict]: 검색된 음식 정보 리스트
        """
        # 세션 확인
        self.start_session()
        
        foods = self.session.query(FoodInfo).filter(
            FoodInfo.food_name.like(f"%{name_keyword}%")
        ).limit(limit).all()
        
        result = []
        for food in foods:
            food_info = {
                'food_id': food.food_id,
                'food_name': food.food_name,
                'tags': self.get_food_tags(food.food_id)
            }
            result.append(food_info)
        
        return result
    
    def search_foods_by_tag(self, tag_name: str, limit: int = 10) -> List[dict]:
        """
        태그명으로 음식을 검색합니다.
        
        Args:
            tag_name: 태그명
            limit: 결과 제한 수 (기본값: 10)
            
        Returns:
            List[dict]: 검색된 음식 정보 리스트
        """
        # 세션 확인
        self.start_session()
        
        foods = self.session.query(FoodInfo).join(
            FoodInfoTag, FoodInfo.food_id == FoodInfoTag.food_id
        ).join(
            FoodTag, FoodInfoTag.tag_id == FoodTag.tag_id
        ).filter(
            FoodTag.tag_name == tag_name
        ).limit(limit).all()
        
        result = []
        for food in foods:
            food_info = {
                'food_id': food.food_id,
                'food_name': food.food_name,
                'tags': self.get_food_tags(food.food_id)
            }
            result.append(food_info)
        
        return result
    
    def get_all_tags(self) -> List[str]:
        """
        모든 태그를 조회합니다.
        
        Returns:
            List[str]: 모든 태그명 리스트
        """
        # 세션 확인
        self.start_session()
        
        tags = self.session.query(FoodTag.tag_name).all()
        return [tag[0] for tag in tags]


# 예시 코드
if __name__ == "__main__":
    # DBManager 사용 예시
    db = DBManager()
    
    try:
        # 컨텍스트 매니저를 사용한 예제
        with db as manager:
            # 태그 추가
            manager.add_food_tags("D102-082290000-0001", ["매운맛", "한식", "국물요리"])
            
            # 태그 조회
            tags = manager.get_food_tags("D102-082290000-0001")
            print(f"현재 태그들: {tags}")
            
            # 여러 작업을 하나의 트랜잭션으로 처리
            with manager.transaction():
                manager.add_food_tags("D102-082290000-0001", ["신선한"], auto_commit=False)
                manager.remove_food_tags("D102-082290000-0001", ["매운맛"], auto_commit=False)
                # 트랜잭션 컨텍스트 종료 시 자동 커밋
        
        # 다른 방식의 사용 예시
        db2 = DBManager()
        db2.start_session()
        
        # 음식 검색
        foods = db2.search_foods_by_name("국밥")
        print(f"국밥 검색 결과: {len(foods)}개")
        
        # 태그로 검색
        tag_foods = db2.search_foods_by_tag("한식")
        print(f"'한식' 태그 음식: {len(tag_foods)}개")
        
        # 트랜잭션 사용
        try:
            db2.session.begin()
            db2.add_food_tags("D102-082290000-0001", ["새로운태그1", "새로운태그2"], auto_commit=False)
            db2.session.commit()
        except Exception as e:
            db2.session.rollback()
            print(f"오류 발생: {e}")
        finally:
            db2.close_session()
        
    except Exception as e:
        print(f"오류 발생: {e}")