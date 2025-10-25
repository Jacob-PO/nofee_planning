#!/usr/bin/env python3
"""
전체 워크플로우 실행 스크립트
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

def run_full_workflow():
    """전체 워크플로우 실행"""
    print("\n" + "="*60)
    print("통신사 요금 데이터 수집 및 분석 시스템")
    print("전체 워크플로우 실행")
    print("="*60)
    
    # 1. 크롤링 실행
    print("\n[1/4] 웹 크롤링 시작...")
    from src.crawlers.kt_crawler import KTCrawler
    from src.crawlers.lg_crawler import LGUPlusCrawler
    from src.crawlers.sk_crawler import TworldCrawler
    
    crawl_results = []
    
    # KT 크롤링
    try:
        kt_crawler = KTCrawler({'max_workers': 3, 'headless': True})
        kt_results = kt_crawler.run()
        crawl_results.extend(kt_results or [])
        print(f"✓ KT 크롤링 완료: {len(kt_results or [])}개 파일")
    except Exception as e:
        print(f"✗ KT 크롤링 실패: {e}")
    
    # LG 크롤링
    try:
        lg_crawler = LGUPlusCrawler({'max_workers': 3, 'headless': True})
        lg_results = lg_crawler.run()
        crawl_results.extend(lg_results or [])
        print(f"✓ LG 크롤링 완료: {len(lg_results or [])}개 파일")
    except Exception as e:
        print(f"✗ LG 크롤링 실패: {e}")
    
    # SK 크롤링
    try:
        sk_crawler = TworldCrawler({'max_workers': 3, 'headless': True})
        sk_results = sk_crawler.run()
        crawl_results.extend(sk_results or [])
        print(f"✓ SK 크롤링 완료: {len(sk_results or [])}개 파일")
    except Exception as e:
        print(f"✗ SK 크롤링 실패: {e}")
    
    # 2. OCR 처리
    print("\n[2/4] OCR 처리 시작...")
    try:
        import subprocess
        ocr_script = project_root / "src" / "ocr" / "clova_ocr.py"
        result = subprocess.run(['python3', str(ocr_script), 'batch', '--table'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ OCR 처리 완료")
        else:
            print(f"✗ OCR 처리 실패: {result.stderr}")
    except Exception as e:
        print(f"✗ OCR 처리 실패: {e}")
    
    # 3. 요약 생성
    print("\n[3/4] 요약 데이터 생성...")
    try:
        from src.data_processing.create_summary_clean import main as create_summary
        create_summary()
        print("✓ 요약 데이터 생성 완료")
    except Exception as e:
        print(f"✗ 요약 생성 실패: {e}")
    
    # 4. 데이터 병합
    print("\n[4/4] 데이터 병합...")
    try:
        from src.data_processing.data_merge_main import main as merge_data
        merge_data()
        print("✓ 데이터 병합 완료")
    except Exception as e:
        print(f"✗ 데이터 병합 실패: {e}")
    
    print("\n" + "="*60)
    print("전체 워크플로우 완료!")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description='전체 워크플로우 실행')
    parser.add_argument('--skip-crawl', action='store_true',
                        help='크롤링 단계 건너뛰기')
    parser.add_argument('--skip-ocr', action='store_true',
                        help='OCR 단계 건너뛰기')
    
    args = parser.parse_args()
    
    start_time = datetime.now(ZoneInfo('Asia/Seoul'))
    print(f"워크플로우 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    run_full_workflow()
    
    end_time = datetime.now(ZoneInfo('Asia/Seoul'))
    elapsed = (end_time - start_time).total_seconds() / 60
    
    print(f"\n워크플로우 종료: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"총 소요 시간: {elapsed:.1f}분")

if __name__ == '__main__':
    main()