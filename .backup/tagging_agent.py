from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI # Google Gemini 모델 사용
from langchain_core.prompts import PromptTemplate
from Agent.optimize_prompts import SYSTEM_PROMPT_CONTENT, USER_PROMPT_TEMPLATE, extract_tags_from_gemma_output
from dotenv import load_dotenv
import sys
import re
import json
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict, Optional, Tuple

# DB 관련 추가
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.db_manager import DBManager
from db.model.food_table import FoodInfo


load_dotenv()

GEMMA_CURRENT_PROMPT = """
다음은 음식 이름과 그에 해당하는 태그 리스트를 추출하는 작업입니다. 각 음식 이름에 대해 적절한 태그들을 쉼표로 구분하여 나열해주세요. 태그는 #으로 시작해야 합니다.

음식: 닭가슴살 샐러드
태그: #샐러드, #고단백, #다이어트, #저탄수화물, #생식, #닭고기

음식: 김치찌개
태그: #한식, #국물요리, #매콤한, #김치, #돼지고기

음식: 현미밥
태그: #밥, #고섬유질, #혈당관리

음식: {food_name}
태그:
"""

# TEST_CASES_DATA = [
#     {
#         "query": "덮밥_낙지",
#         "model_output": "음식: 덮밥_낙지\n태그: #메인요리, #덮밥, #낙지, #매콤한, #해산물, #밥"
#     },
#     {
#         "query": "비건 두부 스테이크",
#         "model_output": "음식: 비건 두부 스테이크\n태그: #메인요리, #비건, #두부, #스테이크, #채소" # 고단백 태그가 누락되었다고 가정
#     },
#     {
#         "query": "저칼로리 닭가슴살 소시지",
#         "model_output": "음식: 저칼로리 닭가슴살 소시지\n태그: #간식, #닭고기, #저칼로리" # 가공식품, 다이어트 태그가 누락되었다고 가정
#     },
#     {
#         "query": "그릭 요거트",
#         "model_output": "음식: 그릭 요거트\n태그: #간식, #유제품" # 고단백, 저지방, 장건강 태그가 누락되었다고 가정
#     }
# ]

class Tagger:

    def __init__(self):
        self.tagging_llm = ChatOllama(
            model="gemma3:27b",
            base_url="http://localhost:11434",
            temperature=0.0,  # 창의성 조절 (0.0 ~ 1.0)
            top_k=40,         # 다음 토큰 선택 시 고려할 상위 k개 토큰
            top_p=0.9,        # 누적 확률이 p를 넘지 않는 가장 작은 토큰 집합
            num_ctx=2048,     # 컨텍스트 윈도우 크기
            repeat_penalty=1.1,  # 반복 패널티 (1.0 이상)
            num_predict=512,  # 생성할 최대 토큰 수
        )
        self.tagging_prompt = None
        self.tagging_agent = None
        self.history = []
    
    def set_prompt(self, prompt: str | Path):
        if isinstance(prompt, Path):
            prompt_content = prompt.read_text(encoding="utf-8")
        else:
            prompt_content = prompt
        self.tagging_prompt = PromptTemplate.from_template(prompt_content)
        self.tagging_agent = self.tagging_prompt | self.tagging_llm
        self.history = []

    def invoke(self, food_name: str) -> List[str]:
        cls_response = self.tagging_agent.invoke({"food_name": food_name})
        tags = extract_tags_from_gemma_output(cls_response.content)
        self.history.append({"query": food_name, "response": cls_response.content, "parsed_response": tags})
        return tags

    def get_history(self) -> List[Dict]:
        return self.history
    

class PromptOptimizer:

    def __init__(self, prompt_path: Path, model_name: str = "gemini-2.0-flash", temperature: float = 0.7, log_file: Path | None = None):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        self.log_file = log_file
        self.prompt_path = prompt_path

    def generate_optimization_request(self, existing_prompt: str, test_cases: list) -> str:
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

    def extract_dict_from_response(self, response_text: str) -> dict | None:
        """
        LLM 응답 텍스트에서 JSON을 파싱하고 'optimized_new_prompt' 값을 추출합니다.

        Args:
            response_text (str): LLM으로부터 받은 전체 응답 문자열.
                                이 응답은 JSON 형식이어야 합니다.

        Returns:
            dict | None: 파싱된 JSON 딕셔너리. JSON 파싱에 실패하면 None을 반환합니다.
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

            return response_data
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"응답 텍스트: {response_text[:200]}...") # 디버깅을 위해 응답 일부 출력
            return None
        except Exception as e:
            print(f"예상치 못한 추출 오류: {e}")
            return None

    def invoke(self, now_prompt: str, output_cases: list) -> Tuple[str, float, bool]:
        """
        프롬프트 최적화를 실행합니다.
        
        Args:
            now_prompt: 현재 프롬프트
            output_cases: 테스트 케이스
            
        Returns:
            Tuple[str, float, bool]: (최적화된 프롬프트, 점수, 성공 여부)
                                    JSON 파싱 실패 시 성공 여부는 False
        """
        human_message = self.generate_optimization_request(now_prompt, output_cases)
        messages = [
            ("system", SYSTEM_PROMPT_CONTENT),
            ("human", human_message)
        ]
        response = self.llm.invoke(messages)
        optimized_dict = self.extract_dict_from_response(response.content)
        
        # JSON 파싱 실패
        if optimized_dict is None:
            log_str = f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                      f"JSON 파싱 실패!\n" \
                      f"response: \n{response.content[:500]}...\n\n\n"
            if self.log_file:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_str)
            print(log_str)
            return now_prompt, 0.0, False
        
        # 성공적인 파싱
        optimized_prompt = optimized_dict.get("optimized_new_prompt", now_prompt)
        optimization_score = optimized_dict.get("optimization_score", 0)
        
        log_str = f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                    f"before: \n{now_prompt}\n" \
                    f"output_cases: \n{json.dumps(output_cases, indent=2, ensure_ascii=False)}\n" \
                    f"optimized_dict: \n{json.dumps(optimized_dict, indent=2, ensure_ascii=False)}\n\n\n"
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_str)
        
        # 최적화된 프롬프트 저장
        if optimized_prompt:
            self.prompt_path.write_text(optimized_prompt, encoding="utf-8")
        print(log_str)
        
        return optimized_prompt, optimization_score, True
    

class FoodTagger:
    """
    DB에서 음식을 가져와 태그를 생성하고, 최적화된 태그를 DB에 저장하는 클래스
    """
    def __init__(self, batch_size: int = 20, max_epochs: int = 10, min_score: float = 85.0, skip_count: int = 0, optimize_prompt: bool = True, max_retries: int = 3, retry_delay: int = 5):
        """
        Args:
            batch_size: 한 번에 처리할 음식 수
            max_epochs: 최대 프롬프트 최적화 횟수
            min_score: 태그를 DB에 저장하기 위한 최소 프롬프트 점수
            skip_count: 처리를 건너뛸 음식의 수 (이미 처리된 음식 수)
            optimize_prompt: 프롬프트 최적화 모드 활성화 여부 (True: 최적화 모드, False: 실사용 모드)
            max_retries: 실패 시 최대 재시도 횟수
            retry_delay: 재시도 사이의 대기 시간(초)
        """
        self.db = DBManager()
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.min_score = min_score
        self.skip_count = skip_count
        self.optimize_prompt = optimize_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 프롬프트 파일 경로
        self.prompt_path = Path("tagging_agent_prompt.txt")
        self.log_file = Path("prompt_optimizer_log.txt")
        
        # Tagger 및 Optimizer 초기화
        self.tagger = Tagger()
        if self.prompt_path.exists():
            self.tagger.set_prompt(self.prompt_path)
        else:
            self.tagger.set_prompt(GEMMA_CURRENT_PROMPT)  # 초기 프롬프트 설정
            
        self.prompt_optimizer = None
        if self.optimize_prompt:
            self.prompt_optimizer = PromptOptimizer(self.prompt_path, log_file=self.log_file)
        
        # 처리 상태 추적
        self.processed_food_ids = set()  # 이미 처리한 음식 ID 목록
        self.total_processed = skip_count  # 지금까지 처리한 총 음식 수 (건너뛴 수로 초기화)
        self.total_foods_count = 0  # 전체 음식 수
        self.current_batch_num = 0  # 현재 처리 중인 배치 번호
        
    def get_total_foods_count(self) -> int:
        """
        전체 음식 수를 조회합니다.
        
        Returns:
            int: 전체 음식 수
        """
        self.db.start_session()
        count = self.db.session.query(FoodInfo).count()
        return count
        
    def get_next_batch(self) -> List[Dict]:
        """
        DB에서 다음 batch_size 개의 음식을 가져옵니다.
        이미 처리한 음식은 제외합니다.
        
        Returns:
            List[Dict]: 음식 정보 목록 [{food_id: str, food_name: str}, ...]
        """
        # 세션을 열고 음식 정보 가져오기
        self.db.start_session()
        try:
            # processed_food_ids에 없는 food_id만 선택
            # 실제 구현 시 DB 쿼리를 최적화할 수 있음
            foods = []
            
            # 모든 음식 정보 조회 (실제 구현에서는 페이지네이션이나 더 효율적인 쿼리 필요)
            all_foods = self.db.session.query(FoodInfo.food_id, FoodInfo.food_name).all()
            
            # 이미 처리한 음식 ID 목록을 업데이트
            # self.skip_count가 0보다 크면, 처음 skip_count 개의 음식을 이미 처리된 것으로 간주
            if self.skip_count > 0 and not self.processed_food_ids:
                print(f"처음 {self.skip_count}개 음식을 건너뜁니다...")
                
                # skip_count 만큼의 음식을 processed_food_ids에 추가
                for idx, (food_id, _) in enumerate(all_foods):
                    if idx < self.skip_count:
                        self.processed_food_ids.add(food_id)
                    else:
                        break
                        
                print(f"{len(self.processed_food_ids)}개 음식을 건너뛰었습니다.")
            
            # 나머지 음식 중에서 batch_size만큼 가져오기
            for food_id, food_name in all_foods:
                if food_id not in self.processed_food_ids and len(foods) < self.batch_size:
                    foods.append({
                        "food_id": food_id,
                        "food_name": food_name
                    })
                    
            return foods
        finally:
            # 세션 유지 (close_session 호출하지 않음)
            pass
    
    def save_tags_to_db(self, food_id: str, tags: List[str]) -> bool:
        """
        생성된 태그를 DB에 저장합니다.
        
        Args:
            food_id: 음식 ID
            tags: 태그 리스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            # DB에 태그 저장
            self.db.add_food_tags(food_id, tags)
            # 처리 완료 목록에 추가
            self.processed_food_ids.add(food_id)
            # 전체 처리 개수 증가는 배치 단위로 처리하기 위해 주석 처리
            # self.total_processed += 1
            return True
        except Exception as e:
            print(f"태그 저장 오류 (음식 ID: {food_id}): {e}")
            return False
    
    def run(self):
        """
        전체 태깅 프로세스를 실행합니다.
        1. DB에서 음식을 batch_size개 가져옴
        2. Tagger로 태그 생성
        3. (최적화 모드인 경우) Optimizer로 프롬프트 최적화
        4. (최적화 모드인 경우) 점수가 min_score 이상이면 태그를 DB에 저장
        5. (실사용 모드인 경우) 바로 태그를 DB에 저장
        6. 다음 배치로 이동
        """
        try:
            # 전체 음식 수 조회
            self.total_foods_count = self.get_total_foods_count()
            
            # 건너뛰기 정보 출력
            if self.skip_count > 0:
                skip_percent = (self.skip_count / self.total_foods_count) * 100 if self.total_foods_count > 0 else 0
                print(f"전체 음식 수: {self.total_foods_count}, 건너뛸 음식 수: {self.skip_count} ({skip_percent:.2f}%)")
                print(f"처리 시작 위치: {self.skip_count + 1}번째 음식부터")
                
                # 건너뛰기 정보를 로그 파일에 기록
                with open(self.log_file, "a", encoding="utf-8") as f:
                    log_entry = f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                    log_entry += f"프로그램 재시작\n"
                    log_entry += f"전체 음식 수: {self.total_foods_count}\n"
                    log_entry += f"건너뛸 음식 수: {self.skip_count} ({skip_percent:.2f}%)\n"
                    log_entry += f"처리 시작 위치: {self.skip_count + 1}번째 음식부터\n\n"
                    f.write(log_entry)
            else:
                print(f"전체 음식 수: {self.total_foods_count}")
                
            # 모드 정보 출력
            if self.optimize_prompt:
                print(f"실행 모드: 최적화 모드 (프롬프트 최적화 활성화)")
            else:
                print(f"실행 모드: 실사용 모드 (고정 프롬프트 사용)")
            
            while True:
                # 다음 배치 가져오기
                foods = self.get_next_batch()
                
                # 더 이상 처리할 음식이 없으면 종료
                if not foods:
                    print(f"모든 음식 처리 완료! 총 {self.total_processed}/{self.total_foods_count} 개 처리")
                    break
                
                self.current_batch_num += 1
                print(f"배치 #{self.current_batch_num} 시작: {len(foods)}개 음식 처리 (전체 진행 상황: {self.total_processed}/{self.total_foods_count})")
                
                # 실사용 모드와 최적화 모드에 따라 처리 방식 분기
                if self.optimize_prompt:
                    # 최적화 모드 - 기존 로직 사용
                    self._run_optimize_mode(foods)
                else:
                    # 실사용 모드 - 프롬프트 최적화 없이 바로 태그 생성 및 저장
                    self._run_production_mode(foods)
                
                # 새 배치에 대해 히스토리 초기화
                self.tagger.history = []
                
                # 현재 시간과 진행 상황을 로그 파일에 기록
                with open(self.log_file, "a", encoding="utf-8") as f:
                    log_entry = f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                    log_entry += f"배치 #{self.current_batch_num} 완료\n"
                    log_entry += f"전체 진행 상황: {self.total_processed}/{self.total_foods_count} ({(self.total_processed/self.total_foods_count)*100:.2f}%)\n\n"
                    f.write(log_entry)
                
                # 잠시 대기 (API 제한 등을 고려)
                time.sleep(1)
                
        finally:
            # 모든 작업 완료 후 세션 종료
            self.db.close_session()
    
    def _run_optimize_mode(self, foods: List[Dict]):
        """
        최적화 모드로 실행 - 프롬프트 최적화 과정 포함
        
        Args:
            foods: 처리할 음식 목록
        """
        # 태그 생성 및 프롬프트 최적화
        for epoch in range(self.max_epochs):
            print(f"Epoch {epoch+1}/{self.max_epochs}")
            
            # 태그 생성
            failed_in_current_epoch = 0
            for i, food in enumerate(foods):
                food_id = food["food_id"]
                food_name = food["food_name"]
                
                # 현재 처리 중인 음식 번호와 진행 상황 출력
                curr_idx = self.total_processed + i + 1
                
                # 태그 생성 시도 및 재시도
                tag_generated = False
                for retry in range(self.max_retries):
                    try:
                        if retry > 0:
                            print(f"[{curr_idx}/{self.total_foods_count}] 재시도 #{retry}/{self.max_retries} - 음식: {food_name} (ID: {food_id})")
                            time.sleep(self.retry_delay)  # 재시도 전 대기
                        else:
                            print(f"[{curr_idx}/{self.total_foods_count}] 음식: {food_name} (ID: {food_id}) 태그 생성 중...")
                        
                        # 태그 생성
                        tags = self.tagger.invoke(food_name)
                        print(f"[{curr_idx}/{self.total_foods_count}] 태그: {tags}")
                        tag_generated = True
                        break  # 성공하면 재시도 반복문 종료
                        
                    except Exception as e:
                        print(f"[{curr_idx}/{self.total_foods_count}] 태그 생성 오류 (음식: {food_name}): {e}")
                        if retry < self.max_retries - 1:
                            continue  # 마지막 시도가 아니면 재시도
                
                # 모든 재시도에도 실패한 경우
                if not tag_generated:
                    failed_in_current_epoch += 1
                    print(f"[{curr_idx}/{self.total_foods_count}] 최대 재시도 횟수를 초과하여 이 음식은 건너뜁니다: {food_name}")
                    
                    # 실패 로그 기록
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                        f.write(f"Epoch {epoch+1}: 태그 생성 실패 (최대 재시도 횟수 초과): 음식 ID={food_id}, 이름={food_name}\n\n")
            
            # 너무 많은 실패가 있으면 다음 에폭으로 넘어감
            if failed_in_current_epoch > len(foods) // 2:
                print(f"Epoch {epoch+1}: 너무 많은 실패 ({failed_in_current_epoch}/{len(foods)}). 다음 에폭으로 넘어갑니다.")
                continue
            
            # 프롬프트 최적화
            try:
                print(f"배치 #{self.current_batch_num} 프롬프트 최적화 중... (진행 상황: {self.total_processed}/{self.total_foods_count})")
                new_prompt, score, success = self.prompt_optimizer.invoke(
                    self.tagger.tagging_prompt.template, 
                    self.tagger.get_history()
                )
                print(f"배치 #{self.current_batch_num} 프롬프트 최적화 점수: {score}")
                
                # JSON 파싱에 실패한 경우
                if not success:
                    print(f"배치 #{self.current_batch_num} JSON 파싱 실패! 전체 프로세스를 다시 시도합니다.")
                    
                    # 히스토리 초기화하고 현재 epoch에서 다시 시작
                    self.tagger.history = []
                    
                    # 잠시 대기 후 재시도 - 태그 생성부터 다시 시작
                    time.sleep(5)
                    break  # 현재 epoch 종료하고 다음 epoch 시작 (태그 생성부터 다시)
                
                # 충분한 점수를 받았으면 태그를 DB에 저장하고 다음 배치로 이동
                if score >= self.min_score:
                    print(f"배치 #{self.current_batch_num} 목표 점수 달성: {score} >= {self.min_score}")
                    break
                
                # 그렇지 않으면 프롬프트 업데이트 후 다시 시도
                self.tagger.set_prompt(new_prompt)
                
            except Exception as e:
                print(f"배치 #{self.current_batch_num} 프롬프트 최적화 오류: {e}")
                # 최적화 실패 시 마지막 결과로 진행
                break
        
        # 최종 태그를 DB에 저장
        self._save_tags_to_db_batch(foods)
    
    def _run_production_mode(self, foods: List[Dict]):
        """
        실사용 모드로 실행 - 프롬프트 최적화 없이 바로 저장
        
        Args:
            foods: 처리할 음식 목록
        """
        # 태그 생성만 수행하고 최적화는 건너뜀
        success_count = 0
        failed_foods = []
        
        for i, food in enumerate(foods):
            food_id = food["food_id"]
            food_name = food["food_name"]
            
            curr_idx = self.total_processed + i + 1
            for retry in range(self.max_retries):
                try:
                    if retry > 0:
                        print(f"[{curr_idx}/{self.total_foods_count}] 재시도 #{retry}/{self.max_retries} - 음식: {food_name} (ID: {food_id})")
                        time.sleep(self.retry_delay)  # 재시도 전 대기
                    else:
                        print(f"[{curr_idx}/{self.total_foods_count}] 음식: {food_name} (ID: {food_id}) 태그 생성 중...")
                    
                    # 태그 생성
                    tags = self.tagger.invoke(food_name)
                    print(f"[{curr_idx}/{self.total_foods_count}] 태그: {tags}")
                    
                    # DB에 저장
                    success = self.save_tags_to_db(food_id, tags)
                    if success:
                        success_count += 1
                        print(f"[{curr_idx}/{self.total_foods_count}] 태그 저장 완료 (음식: {food_name})")
                        break  # 성공하면 재시도 반복문 종료
                    else:
                        print(f"[{curr_idx}/{self.total_foods_count}] 태그 저장 실패 (음식: {food_name}) - 재시도 중...")
                        continue  # 저장 실패 시 재시도
                    
                except Exception as e:
                    print(f"[{curr_idx}/{self.total_foods_count}] 태그 생성 오류 (음식: {food_name}): {e}")
                    if retry < self.max_retries - 1:
                        continue  # 마지막 시도가 아니면 재시도
            
            # 모든 재시도에도 실패한 경우
            if retry == self.max_retries - 1 and (not success or 'success' not in locals()):
                failed_foods.append({"food_id": food_id, "food_name": food_name})
                print(f"[{curr_idx}/{self.total_foods_count}] 최대 재시도 횟수 초과 - 건너뜁니다: {food_name}")
                
                # 실패 로그 기록
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    f.write(f"처리 실패 (최대 재시도 횟수 초과): 음식 ID={food_id}, 이름={food_name}\n\n")
        
        # 배치 처리 완료 후 전체 처리 개수 한 번에 증가
        self.total_processed += success_count
        
        print(f"배치 #{self.current_batch_num} 완료: {success_count}/{len(foods)} 성공, {len(failed_foods)} 실패 (전체 진행 상황: {self.total_processed}/{self.total_foods_count})")
        
        # 실패한 항목이 있으면 로그에 출력
        if failed_foods:
            print(f"실패한 음식 목록 ({len(failed_foods)}개):")
            for i, food in enumerate(failed_foods):
                print(f"  {i+1}. {food['food_name']} (ID: {food['food_id']})")
    
    def _save_tags_to_db_batch(self, foods: List[Dict]):
        """
        배치의 모든 음식에 대한 태그를 DB에 저장합니다.
        
        Args:
            foods: 처리할 음식 목록
        """
        success_count = 0
        for i, food in enumerate(foods):
            food_id = food["food_id"]
            food_name = food["food_name"]
            
            # 해당 음식에 대한 마지막 태그 결과 찾기
            last_result = None
            for result in reversed(self.tagger.get_history()):
                if result["query"] == food_name:
                    last_result = result
                    break
            
            # 결과가 있으면 DB에 저장
            if last_result:
                curr_idx = self.total_processed + i + 1
                tags = last_result["parsed_response"]
                success = self.save_tags_to_db(food_id, tags)
                if success:
                    success_count += 1
                    print(f"[{curr_idx}/{self.total_foods_count}] 태그 저장 완료 (음식: {food_name})")
                else:
                    print(f"[{curr_idx}/{self.total_foods_count}] 태그 저장 실패 (음식: {food_name})")
        
        # 배치 처리 완료 후 전체 처리 개수 한 번에 증가
        self.total_processed += success_count
        
        print(f"배치 #{self.current_batch_num} 완료: {success_count}/{len(foods)} 성공 (전체 진행 상황: {self.total_processed}/{self.total_foods_count})")

if __name__ == "__main__":
    import argparse
    
    # 명령줄 인자 파서 설정
    parser = argparse.ArgumentParser(description='음식 태그 생성 및 DB 저장')
    parser.add_argument('--batch-size', type=int, default=100, help='한 번에 처리할 음식 수')
    parser.add_argument('--max-epochs', type=int, default=10, help='최대 프롬프트 최적화 횟수')
    parser.add_argument('--min-score', type=float, default=85.0, help='태그를 DB에 저장하기 위한 최소 프롬프트 점수')
    parser.add_argument('--skip', type=int, default=0, help='처리를 건너뛸 음식의 수 (이미 처리된 음식 수)')
    parser.add_argument('--no-optimize', action='store_true', help='프롬프트 최적화 없이 실사용 모드로 실행 (고정 프롬프트 사용)')
    parser.add_argument('--max-retries', type=int, default=20, help='태그 생성 실패 시 최대 재시도 횟수')
    parser.add_argument('--retry-delay', type=int, default=5, help='재시도 사이의 대기 시간(초)')
    
    # 인자 파싱
    args = parser.parse_args()
    
    # FoodTagger 객체 생성 및 실행
    tagger = FoodTagger(
        batch_size=args.batch_size, 
        max_epochs=args.max_epochs, 
        min_score=args.min_score,
        # skip_count=args.skip
        skip_count=49833,
        # optimize_prompt=not args.no_optimize,  # --no-optimize 옵션이 있으면 optimize_prompt=False
        optimize_prompt=False,  # --no-optimize 옵션이 있으면 optimize_prompt=False
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    tagger.run()



# init_categorizer_prompt = """다음은 음식 이름과 그에 해당하는 태그 리스트를 추출하는 작업입니다. 각 음식 이름에 대해 적절한 태그들을 쉼표로 구분하여 나열해주세요. 태그는 #으로 시작해야 합니다.

# 음식: 닭가슴살 샐러드
# 태그: #메인요리, #샐러드, #고단백, #다이어트, #저탄수화물, #생식, #닭고기

# 음식: 김치찌개
# 태그: #메인요리, #한식, #국물요리, #매콤한, #김치, #돼지고기

# 음식: 현미밥
# 태그: #메인요리, #밥, #고섬유질, #혈당관리

# 음식: {food_name}
# 태그:"""

# categorizer_prompt = PromptTemplate.from_template(init_categorizer_prompt)
# categorizer = (categorizer_prompt | llm)

# food_name = "덮밥_낙지"

# cls_response = categorizer.invoke({"food_name": food_name})

# print(cls_response.content)


"""
## 프롬프트 최적화 결과

**1. 분석 결과**

*   **강점**:
    *   Few-shot learning을 활용하여 모델이 태그 생성 패턴을 학습하도록 유도한 점이 효과적입니다. 특히 음식의 종류, 조리 방식, 재료, 맛, 특징 등을 태그로 연결하는 방식을 잘 학습했습니다.
    *   출력 형식을 명확하게 지정하여 (쉼표 구분, #으로 시작) 모델이 형식을 잘 따르도록 했습니다.
    *   비교적 간단하고 직관적인 프롬프트 구조를 가지고 있어 이해하기 쉽습니다.

*   **부족한 점**:
    *   **정보 누락**: 몇몇 경우, 음식의 특징을 나타내는 중요한 태그가 누락되었습니다. 예를 들어, "그릭 요거트"의 경우 `#고단백`
"""