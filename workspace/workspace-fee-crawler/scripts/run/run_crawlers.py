#!/usr/bin/env python3
"""
크롤러 실행 스크립트
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

def run_kt_crawler():
    """KT 크롤러 실행"""
    from src.crawlers.kt_crawler import KTCrawler
    
    print("\n=== KT 크롤러 실행 ===")
    config = {
        'max_workers': 3,
        'headless': True,
        'use_rich': True
    }
    
    crawler = KTCrawler(config)
    return crawler.run()

def run_lg_crawler():
    """LG 크롤러 실행"""
    from src.crawlers.lg_crawler import LGUPlusCrawler
    
    print("\n=== LG U+ 크롤러 실행 ===")
    config = {
        'max_workers': 3,
        'headless': True,
        'use_rich': True
    }
    
    crawler = LGUPlusCrawler(config)
    return crawler.run()

def run_sk_crawler():
    """SK 크롤러 실행"""
    from src.crawlers.sk_crawler import SKTelecomCrawler
    
    print("\n=== SK 크롤러 실행 ===")
    config = {
        'max_workers': 3,
        'headless': True,
        'use_rich': True
    }
    
    crawler = SKTelecomCrawler(config)
    return crawler.run()

def main():
    parser = argparse.ArgumentParser(description='통신사 크롤러 실행')
    parser.add_argument('carrier', choices=['kt', 'lg', 'sk', 'all'], 
                        help='실행할 크롤러 선택')
    parser.add_argument('--workers', type=int, default=3,
                        help='워커 수 (기본: 3)')
    parser.add_argument('--show-browser', action='store_true',
                        help='브라우저 표시')
    
    args = parser.parse_args()
    
    start_time = datetime.now(ZoneInfo('Asia/Seoul'))
    print(f"크롤링 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    if args.carrier == 'all':
        # 모든 크롤러 실행
        results.extend(run_kt_crawler() or [])
        results.extend(run_lg_crawler() or [])
        results.extend(run_sk_crawler() or [])
    elif args.carrier == 'kt':
        results.extend(run_kt_crawler() or [])
    elif args.carrier == 'lg':
        results.extend(run_lg_crawler() or [])
    elif args.carrier == 'sk':
        results.extend(run_sk_crawler() or [])
    
    end_time = datetime.now(ZoneInfo('Asia/Seoul'))
    elapsed = (end_time - start_time).total_seconds() / 60
    
    print(f"\n크롤링 완료: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"소요 시간: {elapsed:.1f}분")
    print(f"생성된 파일: {len(results)}개")
    
    for file in results:
        print(f"  - {file}")

if __name__ == '__main__':
    main()