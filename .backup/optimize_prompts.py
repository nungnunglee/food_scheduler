import json
import re


SYSTEM_PROMPT_CONTENT = """
당신은 AI 모델의 프롬프트 최적화를 전문적으로 수행하는 프롬프트 엔지니어입니다. 주어진 기존 프롬프트, 해당 프롬프트에 사용된 쿼리, 그리고 그 결과로 AI 모델이 생성한 실제 출력을 면밀히 분석하고, 분석 결과를 바탕으로 기존 프롬프트의 강점과 부족한 점을 명확히 진단하여 성능을 최적화할 수 있는 새로운 프롬프트를 제안해야 합니다.
"""

USER_PROMPT_TEMPLATE = """
**[분석 및 개선 기준]**
다음 기준들은 **최적화 대상 프롬프트의 성능과 그 프롬프트가 생성한 출력의 품질**을 평가하는 데 사용되어야 합니다. 입력 쿼리 자체의 적합성은 평가하지 않습니다.

1.  **목표 달성도**: 모델이 각 쿼리에 대해 의도한 출력을 얼마나 정확하고 일관성 있게 생성했는가?
2.  **출력 형식 준수**: 지정된 출력 형식(예: #태그, 쉼표 구분)을 잘 지켰는가?
3.  **정보 누락 및 과다**: 필요한 정보가 누락되거나 불필요한 정보가 포함되지는 않았는가?
4.  **모델 오작동 방지**: 모델이 불필요한 설명이나, 의도하지 않은 문장을 생성하는 등 '탈선'하는 경향은 없었는가?
5.  **명확성 및 간결성**: 프롬프트의 지시가 명확하고 불필요한 부분이 없는가?
6.  **확장성 및 일반화**: 다양한 입력(새로운 음식 이름)에 대해서도 일관성 있고 정확한 태그를 생성할 수 있도록 일반화된 패턴을 포함하는가? (특히 영양성분/기능성 태그와 같이 데이터에 직접 명시되지 않은 정보를 유추해야 하는 경우)
7.  **Few-shot Learning 활용**: 예시들이 다양성과 대표성을 잘 갖추어 모델 학습에 효과적인가?

**[입력 형식]**
아래 세 가지 요소를 바탕으로 프롬프트 최적화를 요청합니다. 특히, `<테스트 케이스>` 섹션은 하나의 기존 프롬프트에 대한 여러 쿼리와 각각의 실제 모델 출력으로 구성된 JSON 배열입니다. JSON 형식은 엄격하게 준수되어야 합니다.

<기존 프롬프트>
{existing_prompt_content}
</기존 프롬프트>

<테스트 케이스>
```json
{test_cases_json}
```
</테스트 케이스>

**[출력 형식]**
당신은 다음 JSON 형식으로 응답을 제공해야 합니다. JSON 형식은 엄격하게 준수되어야 합니다.

```json
{{
  "analysis_results": {{
    "strengths": [
      "기존 프롬프트의 강점 1",
      "기존 프롬프트의 강점 2"
    ],
    "weaknesses": [
      "개선이 필요한 부족한 점 1",
      "개선이 필요한 부족한 점 2"
    ]
  }},
  "improvement_direction": [
    "개선 방향 1",
    "개선 방향 2"
  ],
  "optimized_new_prompt": "여기에 최적화된 새 프롬프트 내용이 들어갑니다. 예시 사용은 반드시 10개 이하로 제한합니다.",
  "optimization_score": 85
}}
```
**'optimization_score' 필드 설명:**
이 필드는 현재 프롬프트의 최적화 정도를 0부터 100 사이의 정수 값으로 나타냅니다.
* **0-40 (낮음)**: 여전히 중요한 개선이 필요하거나, 많은 테스트 케이스에서 의도된 성능을 내지 못하고 있음.
* **41-70 (보통)**: 일부 개선이 이루어졌지만, 여전히 중요한 부분에서 최적화가 더 필요함.
* **71-90 (좋음)**: 대부분의 테스트 케이스를 잘 처리하며, 프롬프트가 상당히 최적화되었음.
* **91-100 (매우 좋음)**: 프롬프트가 거의 완벽하게 최적화되었으며, 모든 테스트 케이스를 매우 효과적으로 처리함.
이 점수는 당신의 분석을 종합하여 결정해야 합니다.
"""

# 다음 세 부분으로 구성된 응답을 제공해주세요.

# 1.  **분석 결과**:
#     * **강점**: 기존 프롬프트의 잘된 점들을 나열합니다.
#     * **부족한 점**: 각 테스트 케이스의 결과를 종합하여 개선이 필요한 부분들을 구체적으로 설명합니다. (각각의 부족한 점에 대해 왜 부족한지, 어떤 문제가 발생할 수 있는지 명확히 설명)
# 2.  **개선 방향**: 부족한 점을 보완하기 위한 구체적인 전략이나 접근 방식을 요약하여 설명합니다.
# 3.  **최적화된 새 프롬프트**: 분석 결과와 개선 방향을 반영하여 새롭게 제안하는 프롬프트 전문을 제공합니다. 이는 API 호출 시 `prompt` 파라미터로 직접 사용할 수 있는 형태여야 합니다.


def generate_optimization_request(existing_prompt: str, test_cases: list) -> str:
    """
    프롬프트 최적화를 요청하기 위한 최종 유저 프롬프트 내용을 생성합니다.

    Args:
        existing_prompt (str): 최적화 대상인 Gemma 모델의 현재 프롬프트 내용.
        test_cases (list): 각 테스트 케이스를 담은 리스트.
                          각 케이스는 {'query': '...', 'model_output': '...'} 형태의 딕셔너리.

    Returns:
        str: LangChain HumanMessage에 들어갈 최종 유저 프롬프트 문자열.
    """
    # 테스트 케이스 리스트를 JSON 문자열로 변환합니다.
    # indent=2는 JSON을 읽기 쉽게 들여쓰기 해주고, ensure_ascii=False는 한글이 깨지지 않도록 합니다.
    test_cases_json_str = json.dumps(test_cases, indent=2, ensure_ascii=False)

    # 유저 프롬프트 템플릿에 기존 프롬프트와 테스트 케이스 JSON을 채워 넣습니다.
    formatted_user_prompt = USER_PROMPT_TEMPLATE.format(
        existing_prompt_content=existing_prompt,
        test_cases_json=test_cases_json_str
    )
    return formatted_user_prompt


def extract_optimized_prompt(response_text: str) -> str | None:
    """
    LLM 응답 텍스트에서 JSON을 파싱하고 'optimized_new_prompt' 값을 추출합니다.

    Args:
        response_text (str): LLM으로부터 받은 전체 응답 문자열.
                            이 응답은 JSON 형식이어야 합니다.

    Returns:
        str | None: 추출된 최적화된 프롬프트 문자열.
                    JSON 파싱에 실패하거나 'optimized_new_prompt' 키가 없으면 None을 반환합니다.
    """
    try:
        # 응답 텍스트에서 JSON 코드 블록만 추출합니다.
        # 모델이 JSON 응답을 ```json ... ``` 형태로 감싸서 줄 수도 있기 때문에 이를 처리합니다.
        json_match = re.search(r"```json\n(.*)\n```", response_text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
        else:
            # ```json``` 블록이 없으면 전체 응답이 JSON이라고 가정합니다.
            json_string = response_text

        # JSON 문자열을 파싱합니다.
        response_data = json.loads(json_string)

        # 'optimized_new_prompt' 키의 값을 반환합니다.
        return response_data.get("optimized_new_prompt")
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 텍스트: {response_text[:200]}...") # 디버깅을 위해 응답 일부 출력
        return None
    except KeyError:
        print("응답 JSON에 'optimized_new_prompt' 키가 없습니다.")
        return None
    except Exception as e:
        print(f"예상치 못한 추출 오류: {e}")
        return None


def extract_tags_from_gemma_output(gemma_output_string: str) -> list[str]:
    """
    Gemma 모델의 출력 문자열에서 태그 리스트를 추출하고,
    각 태그에서 '#'을 제거한 후 문자열 리스트로 반환합니다.
    태그 형식이 유효한지 (예: #으로 시작하는지) 검사하는 로직을 포함합니다.

    Args:
        gemma_output_string (str): Gemma 모델의 출력 문자열.
                                   예: "음식: 덮밥_낙지\n태그: #메인요리, #한식, #덮밥, #낙지, #매콤한, #해산물"
                                   또는 "#메인요리, #밥, #고섬유질" (태그 부분만 있는 경우)

    Returns:
        list[str]: '#'이 제거된 유효한 태그 문자열 리스트.
                   태그 부분을 찾지 못하거나 유효한 태그가 없으면 빈 리스트를 반환합니다.
    """
    tags_string_to_process = ""

    # "태그: "로 시작하는 줄을 찾기 위한 정규 표현식
    # re.IGNORECASE는 대소문자 구분 없이 매치하도록 합니다.
    match = re.search(r"태그:\s*(.*)", gemma_output_string, re.IGNORECASE)

    if match:
        # "태그: " 접두사가 있는 경우, 그 뒤의 문자열을 태그 부분으로 추출
        tags_string_to_process = match.group(1).strip()
    else:
        # "태그: " 접두사가 없는 경우, 입력 문자열 전체를 태그 부분으로 간주
        tags_string_to_process = gemma_output_string.strip()

    if tags_string_to_process:
        # 쉼표로 분리하여 개별 태그 문자열 리스트 생성
        # 빈 문자열이 생성되지 않도록 필터링합니다.
        raw_tags = [tag.strip() for tag in tags_string_to_process.split(',') if tag.strip()]

        cleaned_tags = []
        for tag in raw_tags:
            # 태그 유효성 검사: '#'으로 시작하고, '#' 뒤에 최소 한 글자 이상이 있는지 확인
            # 예: #메인요리, #밥, #123 (유효)
            # 예: #, # (무효)
            # 예: 그냥문자열 (무효)
            if re.fullmatch(r"#[^\s#]+", tag): # #으로 시작하고, 공백이나 #이 아닌 문자가 하나 이상 오는 경우
                cleaned_tags.append(tag.lstrip('#'))
            else:
                # 유효하지 않은 태그는 건너뜁니다.
                print(f"경고: 유효하지 않은 태그 형식입니다. 스킵합니다: '{tag}'")
                pass # 또는 로그를 남길 수 있습니다.

        return cleaned_tags
    else:
        return [] # 태그 부분을 찾지 못하거나 처리할 문자열이 없으면 빈 리스트 반환