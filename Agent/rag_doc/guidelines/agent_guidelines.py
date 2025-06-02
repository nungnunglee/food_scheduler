# Selenium: 웹 브라우저를 자동화하는 도구
# webdriver: 브라우저를 제어하는 기본 클래스
from selenium import webdriver
# By: 웹 요소를 찾는 방법을 정의 (ID, CLASS_NAME, TAG_NAME 등)
from selenium.webdriver.common.by import By
# WebDriverWait: 특정 조건이 만족될 때까지 기다리는 기능
from selenium.webdriver.support.ui import WebDriverWait
# expected_conditions: 기다릴 조건들을 정의 (요소가 나타날 때, 클릭 가능할 때 등)
from selenium.webdriver.support import expected_conditions as EC
# 예외 처리: 타임아웃, 요소를 찾지 못했을 때 등의 예외 상황 처리
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time  # 시간 지연을 위한 모듈
import json  # JSON 데이터 처리를 위한 모듈
import os    # 파일 시스템 작업을 위한 모듈


def setup_driver():
    """
    웹드라이버 설정 및 초기화
    - ChromeOptions(): 크롬 브라우저의 설정을 관리하는 객체
    - add_argument(): 브라우저 실행 옵션 추가
        - '--headless': 브라우저 창을 띄우지 않고 백그라운드에서 실행
        - '--no-sandbox': 보안 샌드박스 비활성화 (리눅스 환경에서 필요)
        - '--disable-dev-shm-usage': 공유 메모리 사용 제한 해제
    """
    # ChromeOptions 객체 생성: 브라우저 설정을 관리
    options = webdriver.ChromeOptions()
    # 헤드리스 모드 설정: 브라우저 창을 띄우지 않음
    options.add_argument('--headless')
    # 샌드박스 비활성화: 리눅스 환경에서 필요한 설정
    options.add_argument('--no-sandbox')
    # 공유 메모리 사용 제한 해제: 안정성 향상
    options.add_argument('--disable-dev-shm-usage')
    # 설정된 옵션으로 Chrome 웹드라이버 생성 및 반환
    return webdriver.Chrome(options=options)


def wait_for_element(driver, by, value, timeout=10):
    """
    특정 요소가 나타날 때까지 대기하는 함수
    - driver: 웹드라이버 객체
    - by: 요소를 찾는 방법 (By.ID, By.CLASS_NAME 등)
    - value: 찾을 요소의 값
    - timeout: 최대 대기 시간(초)
    - EC.presence_of_element_located: 요소가 DOM에 존재할 때까지 대기
    """
    try:
        # WebDriverWait 객체 생성: 최대 timeout 초 동안 대기
        # EC.presence_of_element_located: 요소가 DOM에 존재할 때까지 대기
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        # 타임아웃 발생 시 에러 메시지 출력
        print(f"요소를 찾을 수 없습니다: {value}")
        return None


def scroll_to_bottom(driver):
    """
    페이지를 끝까지 스크롤하는 함수
    - execute_script(): JavaScript 코드 실행
    - scrollHeight: 페이지의 전체 높이
    - 스크롤 후 새로운 콘텐츠가 로드될 때까지 2초 대기
    - 더 이상 새로운 콘텐츠가 로드되지 않으면 종료
    """
    # 현재 페이지의 전체 높이를 JavaScript로 가져옴
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # JavaScript로 페이지를 맨 아래로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 새로운 콘텐츠 로드를 위해 2초 대기
        time.sleep(2)
        # 스크롤 후 새로운 페이지 높이 확인
        new_height = driver.execute_script("return document.body.scrollHeight")
        # 높이가 같으면 더 이상 로드할 콘텐츠가 없음
        if new_height == last_height:
            break
        # 새로운 높이를 마지막 높이로 저장
        last_height = new_height


def extract_text_content(element):
    """
    웹 요소에서 텍스트를 추출하는 함수
    - element: 웹 요소 객체
    - text: 요소의 텍스트 내용
    - strip(): 앞뒤 공백 제거
    - 예외 처리: 요소가 None이거나 text 속성이 없는 경우
    """
    try:
        # element.text: 요소의 텍스트 내용 가져오기
        # strip(): 앞뒤 공백 제거
        return element.text.strip()
    except AttributeError:
        # 요소가 None이거나 text 속성이 없는 경우 빈 문자열 반환
        return ""


def save_to_json(data, filename):
    """
    데이터를 JSON 파일로 저장하는 함수
    - data: 저장할 데이터 (딕셔너리 또는 리스트)
    - filename: 저장할 파일 이름
    - ensure_ascii=False: 한글 등 유니코드 문자를 그대로 저장
    - indent=2: JSON 파일을 보기 좋게 들여쓰기
    """
    # 파일을 쓰기 모드('w')로 열고 UTF-8 인코딩 사용
    with open(filename, 'w', encoding='utf-8') as f:
        # json.dump(): 데이터를 JSON 형식으로 파일에 저장
        # ensure_ascii=False: 한글 등 유니코드 문자를 그대로 저장
        # indent=2: JSON 파일을 보기 좋게 들여쓰기
        json.dump(data, f, ensure_ascii=False, indent=2)


def scrape_guidelines(url):
    """
    메인 스크래핑 함수
    - url: 스크래핑할 웹페이지 주소
    - driver.get(): 웹페이지 로드
    - find_elements(): 여러 요소 찾기 (리스트 반환)
    - find_element(): 단일 요소 찾기
    - try-except-finally: 예외 처리 및 리소스 정리
    """
    # 웹드라이버 초기화
    driver = setup_driver()
    try:
        # 지정된 URL로 페이지 로드
        driver.get(url)
        
        # body 태그가 로드될 때까지 대기
        wait_for_element(driver, By.TAG_NAME, "body")
        
        # 페이지 끝까지 스크롤하여 모든 콘텐츠 로드
        scroll_to_bottom(driver)
        
        # 가이드라인 데이터를 저장할 리스트
        guidelines = []
        # 'article' 클래스를 가진 모든 요소 찾기
        articles = driver.find_elements(By.CLASS_NAME, "article")
        
        # 각 article 요소에 대해 반복
        for article in articles:
            try:
                # article 내의 'title' 클래스를 가진 요소에서 텍스트 추출
                title = extract_text_content(article.find_element(By.CLASS_NAME, "title"))
                # article 내의 'content' 클래스를 가진 요소에서 텍스트 추출
                content = extract_text_content(article.find_element(By.CLASS_NAME, "content"))
                
                # 추출한 데이터를 딕셔너리로 만들어 리스트에 추가
                guidelines.append({
                    "title": title,
                    "content": content
                })
            except NoSuchElementException:
                # 요소를 찾지 못한 경우 다음 article로 진행
                continue
        
        # 수집한 데이터를 JSON 파일로 저장
        save_to_json(guidelines, "guidelines_data.json")
        return guidelines
        
    except Exception as e:
        # 예외 발생 시 에러 메시지 출력
        print(f"스크래핑 중 오류 발생: {str(e)}")
        return None
        
    finally:
        # 브라우저 종료 및 리소스 정리
        driver.quit()


# 메인 실행 부분
if __name__ == "__main__":
    # 스크래핑할 웹페이지 URL 설정
    target_url = "https://example.com/guidelines"
    # 스크래핑 실행
    results = scrape_guidelines(target_url)
    # 결과가 있으면 수집된 가이드라인 수 출력
    if results:
        print(f"총 {len(results)}개의 가이드라인을 수집했습니다.")
