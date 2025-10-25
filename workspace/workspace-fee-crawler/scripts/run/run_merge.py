#!/usr/bin/env python3
"""
데이터 병합 실행 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

def run_data_merge():
    """데이터 병합 실행"""
    from src.data_processing.data_merge_main import main as merge_main
    
    print("\n=== 데이터 병합 시작 ===")
    
    # 병합 실행
    merge_main()

def main():
    parser = argparse.ArgumentParser(description='데이터 병합 실행')
    parser.add_argument('--carrier', choices=['kt', 'lg', 'sk', 'all'], 
                        default='all', help='병합할 통신사 선택')
    
    args = parser.parse_args()
    
    start_time = datetime.now(ZoneInfo('Asia/Seoul'))
    print(f"데이터 병합 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    run_data_merge()
    
    end_time = datetime.now(ZoneInfo('Asia/Seoul'))
    elapsed = (end_time - start_time).total_seconds() / 60
    
    print(f"\n데이터 병합 완료: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"소요 시간: {elapsed:.1f}분")

if __name__ == '__main__':
    main()