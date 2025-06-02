
"""
당신은 사용자의 요청에 따라 식단을 생성하고, 생성된 식단을 JSON 형식으로 반환하는 식단 전문가입니다.

반환되는 JSON 형식은 다음과 같습니다:

```json
{
  "식단": [
    {
      "시간대": "아침",
      "음식": "스크램블 에그와 토스트"
    },
    {
      "시간대": "점심",
      "음식": "닭가슴살 샐러드"
    },
    {
      "시간대": "저녁",
      "음식": "구운 연어와 야채"
    }
  ]
}
```

- 시간대 필드에는 "아침", "점심", "저녁" 중 하나의 값이 들어갑니다.
- 음식 필드에는 해당 시간대에 적합한 음식 이름이 들어갑니다.

반드시 위 JSON 형식으로만 답변해야 합니다. 다른 설명이나 부가적인 정보는 포함하지 마세요.
"""

"""
다이어트 중인 저를 위해, 저칼로리 하루 식단을 추천해주세요.
**설명:**

*   사용자 프롬프트는 모델에게 식단을 요청하는 구체적인 내용입니다.
*   사용자의 요구사항(예: 건강, 다이어트)을 명확하게 전달합니다.
*   더 구체적인 요구사항을 추가하여 모델이 더 적절한 식단을 생성하도록 할 수 있습니다.
"""


from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
import json

# API 키 설정 (본인의 API 키로 변경)
openai_api_key = "YOUR_OPENAI_API_KEY"

# 모델 초기화
llm = ChatOpenAI(openai_api_key=openai_api_key, model_name="gpt-3.5-turbo", temperature=0.7)

# 프롬프트 템플릿 생성
system_template = """
당신은 사용자의 요청에 따라 식단을 생성하고, 생성된 식단을 JSON 형식으로 반환하는 식단 전문가입니다.

반환되는 JSON 형식은 다음과 같습니다:

```json
{
  "식단": [
    {
      "시간대": "아침",
      "음식": "스크램블 에그와 토스트"
    },
    {
      "시간대": "점심",
      "음식": "닭가슴살 샐러드"
    },
    {
      "시간대": "저녁",
      "음식": "구운 연어와 야채"
    }
  ]
}
```
시간대 필드에는 "아침", "점심", "저녁" 중 하나의 값이 들어갑니다.
음식 필드에는 해당 시간대에 적합한 음식 이름이 들어갑니다.
반드시 위 JSON 형식으로만 답변해야 합니다. 다른 설명이나 부가적인 정보는 포함하지 마세요.
"""

human_template = "{user_request}"
chat_prompt = ChatPromptTemplate.from_messages([
SystemMessagePromptTemplate.from_template(system_template),
HumanMessagePromptTemplate.from_template(human_template)
])

# LLMChain 생성
chain = LLMChain(llm=llm, prompt=chat_prompt)

# 사용자 요청 입력
user_request = "저에게 건강하고 균형 잡힌 하루 식단을 추천해주세요."

# 식단 생성 및 JSON 파싱
output = chain.run(user_request=user_request)

try:
    meal_plan = json.loads(output)
    print(json.dumps(meal_plan, indent=2, ensure_ascii=False)) # JSON 예쁘게 출력
except json.JSONDecodeError as e:
    print(f"JSON 파싱 오류: {e}")
    print(f"모델 출력: {output}") # 오류 발생 시 모델 출력 내용 확인
