#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import time
import argparse
from datetime import datetime
import os

# 프로젝트 루트 경로 추가
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 기존 코드 임포트
from db.db_manager import DBManager
from db.model.food_table import FoodInfo
from Agent.tagging_agent import Tagger

def setup_logger(log_dir="logs"):
    """로그 디렉토리 및 파일 설정"""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        os.makedirs(log_dir)
    log_file = log_dir / f"food_tagging_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return log_file

def log_message(message, log_file=None):
    """메시지 로깅 및 출력"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

def run_food_tagging(skip_count=0, max_retries=3, retry_delay=5):
    """
    음식 태그 생성 및 저장 실행 함수
    배치 처리 없이 하나씩 처리
    
    Args:
        skip_count: 처리를 건너뛸 음식의 수
        max_retries: 실패 시 최대 재시도 횟수
        retry_delay: 재시도 사이의 대기 시간(초)
    """
    # 로거 설정
    log_file = setup_logger()
    
    # 태그 생성기 초기화
    tagger = Tagger()
    prompt_path = Path("tagging_agent_prompt.txt")
    if prompt_path.exists():
        tagger.set_prompt(prompt_path)
    else:
        log_message("프롬프트 파일이 없습니다. 기본 프롬프트를 사용합니다.", log_file)
    
    # DB 연결
    db = DBManager()
    
    try:
        # 전체 음식 수 조회
        db.start_session()
        total_foods = db.session.query(FoodInfo).count()
        log_message(f"전체 음식 수: {total_foods}", log_file)
        
        # 모든 음식 ID 가져오기
        all_foods = db.session.query(FoodInfo.food_id, FoodInfo.food_name).all()
        
        # 처리 상태 추적 변수
        processed_food_ids = set()
        
        # 건너뛰기 정보 출력
        if skip_count > 0:
            skip_percent = (skip_count / total_foods) * 100 if total_foods > 0 else 0
            log_message(f"건너뛸 음식 수: {skip_count} ({skip_percent:.2f}%)", log_file)
            log_message(f"처리 시작 위치: {skip_count + 1}번째 음식부터", log_file)
        
        # 음식 하나씩 처리
        for i, (food_id, food_name) in enumerate(all_foods):
            # 건너뛰기 처리
            if i < skip_count:
                continue
            
            time.sleep(2)
            # 이미 처리한 음식인지 확인
            if food_id in processed_food_ids:
                continue
            
            # 처리 시작
            curr_idx = i + 1
            log_message(f"[{curr_idx}/{total_foods}] 음식: {food_name} (ID: {food_id}) 처리 시작", log_file)
            
            # 태그 생성 및 저장 시도
            success = False
            for retry in range(max_retries):
                try:
                    # 재시도 메시지 출력
                    if retry > 0:
                        log_message(f"[{curr_idx}/{total_foods}] 재시도 #{retry}/{max_retries} - 음식: {food_name}", log_file)
                        time.sleep(retry_delay)
                    
                    # 태그 생성
                    tags = tagger.invoke(food_name)
                    log_message(f"[{curr_idx}/{total_foods}] 생성된 태그: {tags}", log_file)
                    
                    # 태그 저장
                    db.add_food_tags(food_id, tags)
                    processed_food_ids.add(food_id)
                    success = True
                    log_message(f"[{curr_idx}/{total_foods}] 태그 저장 완료: {food_name}", log_file)
                    break  # 성공하면 재시도 중단
                    
                except Exception as e:
                    log_message(f"[{curr_idx}/{total_foods}] 오류 발생: {e}", log_file)
                    if retry < max_retries - 1:
                        continue
            
            # 모든 재시도 실패
            if not success:
                log_message(f"[{curr_idx}/{total_foods}] 최대 재시도 횟수를 초과하여 실패: {food_name}", log_file)
            
            # 진행 상황 출력
            progress = (curr_idx / total_foods) * 100
            log_message(f"현재 진행 상황: {curr_idx}/{total_foods} ({progress:.2f}%)", log_file)
        
        # 완료 메시지
        log_message(f"모든 처리 완료! 총 {curr_idx}/{total_foods} 개 처리", log_file)
        
    except Exception as e:
        log_message(f"프로그램 실행 중 오류 발생: {e}", log_file)
    finally:
        # 세션 종료
        db.close_session()

if __name__ == "__main__":
    
    # 태깅 실행
    run_food_tagging(
        skip_count=141189,
        max_retries=20,
        retry_delay=5
    ) 