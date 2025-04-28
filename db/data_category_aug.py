import ollama
from dotenv import load_dotenv
load_dotenv()


def get_food_category(food_name: str):
    ollama_response = ollama.chat(model='gemma3', messages=[
        {
            'role': 'system',
            'content': "넌 음식 분류 모델이야. 음식을 입력 받으면 다음 중 하나를 번호로 대댑해."
                       "1. 밥/죽/면류 (Rice/Porridge/Noodles): 밥, 죽, 국수, 파스타 등 곡물/면이 주를 이루는 형태"
                       "2. 국/찌개/탕류 (Soups/Stews/Casseroles): 국물이 많은 형태"
                       "3. 찜/조림류 (Steamed/Braised Dishes): 찌거나 국물이 적게 졸여진 형태"
                       "4. 구이/볶음류 (Grilled/Stir-fried Dishes): 굽거나 기름에 볶아진 형태"
                       "5. 튀김/전류 (Fried/Pancake Dishes): 기름에 튀기거나 부쳐진 형태"
                       "6. 무침/숙채/샐러드류 (Seasoned Salads - Cooked/Raw): 데치거나 익힌 채소 등을 양념에 버무리거나, 생채소에 드레싱을 곁들인 형태"
                       "7. 김치/절임류 (Kimchi/Pickles): 발효되거나 절여진 형태의 반찬"
                       "8. 빵/샌드위치/버거/피자류 (Bread/Sandwiches/Burgers/Pizzas): 빵이나 도우가 주를 이루는 형태 (인기 품목은 별도 L1으로 분리)"
                       "9. 분식류 (Snack Foods - Korean Style): 한국 길거리/분식집에서 인기 있는 특정 품목 모음"
                       "10. 후식/간식류 (Desserts/Snacks): 달콤하거나 식사 외에 가볍게 먹는 형태"
                       "11. 음료 (Beverages): 마시는 것"
                       "12. 기타 (Others): 위 카테고리에 속하기 어려운 품목 (예: 과일 단품, 마른 안주 등)"
        },
        {
            'role': 'user',
            'content': food_name,
        },
    ])
    return ollama_response['message']['content']


if __name__ == "__main__":
    print(get_food_category("탕수육"))