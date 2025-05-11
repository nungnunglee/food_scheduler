
TODO:
- UI:
	- figma: prototype 설계
	- flutter: 
		- OAuth2
		- 서버와 통신
		- 쇼핑몰 스크랩핑
- Agent:
	- 기능: 
		- 질의 응답:
			- 각 분야 전문 Agent들에게 동시에 물어보고 종합
		- 식단 만들기:
			1. 신체정보의 맞는 필요 영양성분 수준 정하기 (식이섬유, 해산물 위주 등 코멘트도 생성)
			2. 전문지식을 가진 Agent가 각각 평가 후 반영 (코멘트 추가)
			3. 영양성분, Agent의 코멘트, 선호식단정보태그를 반영해서 식단 설정 (음식 이름, 섭취 시간대, 영양성분을 출력)
			4. 전문지식을 가진 Agent가 각각 평가 후 코멘트 추가
			5. 최종적으로 코멘트를 식단에 반영
	- 설계:
		- RAG 시 post, pre process는 어떻게 할건지
		- graph 어떻게 묶을 것인지
		- mcp
	- prompt:
		- 적당히 해보기
	- 문서:
		- 전문성 있는 교재 취득
			- 영양학 : 확보
			- 생리학 : 확보
			- 국가건강정보포털(API 신청 완료, 지침 문서 크롤링 필요): https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoMain.do
			- 식품안전나라(생애주기별 정보, 지침 문서 크롤링 필요): https://www.foodsafetykorea.go.kr/portal/board/board.do?menu_grp=MENU_NEW03&menu_no=4847

- DB:
	- table 설계:
		- 음식과 유저 다대다 연결을 통해 식단 구현
		- 뷰, 인덱스도 할 수 있으면 해보기
	- 일단 데이터 테이블에 넣기:
		- 음식데이터는 만들어 둔 구조대로 sqlarchemy로 PK, FK를 설정 후 입력
		- 이후 LLM으로 만든 태그를 sqlarchemy로 입력
		- 회원데이터는 테이블 정의하고 더미 데이터 넣고 빼보기
	- 데이터 LLM으로 채워넣기:
		1. 프롬프팅 최적화 (분류는 로컬, 검증은 외부)
			- 분류자, 판별자, 재정비자 가 한 덩어리
			- 분류자가 n개의 음식 라벨링
			- 판별자가 n개의 라벨상태 한번에 확인
			- 재정비자가 새로운 프롬프트를 반환
			- 성능 측정 방법 구현(불통 빈도로 측정)
		2. 그래프로 구현 (100% 로컬 or 100% 외부API)
			- 태그 라벨링
			- 평가
			- 불통 시 사유와 함께 재 라벨링
			- 통과 시 다음 음식 라벨링
			- 반복
		모델:
			로컬:
			- exaone
			- gemma
			외부:
			- ChatGPT
			- gemini
			- claude
			- llama
			- mistral