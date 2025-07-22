from db.tables.food_table import FoodTag, FoodInfo, FoodInfoTag
from typing import List, Optional


class FoodMixin:
    
    def get_tag(self, tag_name: str = None, tag_id: str = None) -> FoodTag:
        """
        태그명으로 기존 태그를 조회하거나 새로운 태그를 생성합니다.
        
        Args:
            tag_name: 태그명
            
        Returns:
            FoodTag: 기존 또는 새로 생성된 태그 객체
        """
        if self.session is None:
            raise RuntimeError("세션이 활성화되지 않았습니다. DBManager를 with 구문이나 transaction 컨텍스트 내에서 사용하세요.")


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
                'serving_size_g': food.nutrition.serving_size_g,
                'nutrient_reference_amount_g': food.nutrition.nutrient_reference_amount_g,
                'energy_kcal': food.nutrition.energy_kcal,
                'moisture_g': food.nutrition.moisture_g,
                'protein_g': food.nutrition.protein_g,
                'fat_g': food.nutrition.fat_g,
                'ash_g': food.nutrition.ash_g,
                'carbohydrate_g': food.nutrition.carbohydrate_g,
                'sugars_g': food.nutrition.sugars_g,
                'dietary_fiber_g': food.nutrition.dietary_fiber_g,
                'calcium_mg': food.nutrition.calcium_mg,
                'iron_mg': food.nutrition.iron_mg,
                'phosphorus_mg': food.nutrition.phosphorus_mg,
                'potassium_mg': food.nutrition.potassium_mg,
                'sodium_mg': food.nutrition.sodium_mg,
                'vitamin_a_ug_rae': food.nutrition.vitamin_a_ug_rae,
                'retinol_ug': food.nutrition.retinol_ug,
                'beta_carotene_ug': food.nutrition.beta_carotene_ug,
                'thiamin_mg': food.nutrition.thiamin_mg,
                'riboflavin_mg': food.nutrition.riboflavin_mg,
                'niacin_mg': food.nutrition.niacin_mg,
                'vitamin_c_mg': food.nutrition.vitamin_c_mg,
                'vitamin_d_ug': food.nutrition.vitamin_d_ug,
                'cholesterol_mg': food.nutrition.cholesterol_mg,
                'saturated_fat_g': food.nutrition.saturated_fat_g,
                'trans_fat_g': food.nutrition.trans_fat_g
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
        
        tags = self.session.query(FoodTag).all()
        return tags
        # return [tag[0] for tag in tags]
