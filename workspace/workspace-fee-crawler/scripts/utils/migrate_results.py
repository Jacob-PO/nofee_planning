#!/usr/bin/env python3
"""
기존 src/data_processing/results 폴더의 파일들을
새로운 data/outputs 구조로 마이그레이션

672MB, 855개 파일을 날짜별로 정리하여 이동
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict

def parse_filename_date(filename):
    """파일명에서 날짜 추출 (YYYYMMDD_HHMMSS)"""
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        return date_str
    return None

def migrate_results():
    """results 폴더 마이그레이션"""

    # 경로 설정
    old_results_dir = Path("src/data_processing/results")
    new_merged_archive = Path("data/outputs/merged/archive")
    new_summary_archive = Path("data/outputs/summary/archive")

    if not old_results_dir.exists():
        print("❌ src/data_processing/results 폴더가 없습니다")
        return

    # 통계
    stats = {
        'total': 0,
        'migrated': 0,
        'skipped': 0,
        'by_date': defaultdict(int),
        'by_type': defaultdict(int)
    }

    print("="*60)
    print("📦 Results 폴더 마이그레이션 시작")
    print("="*60)
    print(f"Source: {old_results_dir}")
    print(f"Target: {new_merged_archive}")
    print("")

    # 모든 파일 스캔
    all_files = list(old_results_dir.glob("*.xlsx")) + list(old_results_dir.glob("*.csv"))
    stats['total'] = len(all_files)

    print(f"총 {stats['total']}개 파일 발견")
    print("")

    # 파일별로 처리
    for file_path in all_files:
        filename = file_path.name

        # 날짜 추출
        date_str = parse_filename_date(filename)

        if date_str is None:
            print(f"⚠️  날짜 파싱 실패 (건너뜀): {filename}")
            stats['skipped'] += 1
            continue

        # 파일 유형 판별
        if 'summary' in filename.lower():
            # Summary 파일
            target_dir = new_summary_archive / date_str
            file_type = 'summary'
        elif any(carrier in filename.lower() for carrier in ['kt_', 'sk_', 'lg_']):
            # Merged 파일
            target_dir = new_merged_archive / date_str
            file_type = 'merged'
        else:
            print(f"⚠️  알 수 없는 파일 유형 (건너뜀): {filename}")
            stats['skipped'] += 1
            continue

        # 디렉토리 생성
        target_dir.mkdir(parents=True, exist_ok=True)

        # 파일 이동
        target_path = target_dir / filename

        # 중복 파일 확인
        if target_path.exists():
            print(f"   ⏭️  이미 존재 (건너뜀): {filename}")
            stats['skipped'] += 1
            continue

        try:
            shutil.copy2(file_path, target_path)
            stats['migrated'] += 1
            stats['by_date'][date_str] += 1
            stats['by_type'][file_type] += 1

            # 진행 상황 표시 (100개마다)
            if stats['migrated'] % 100 == 0:
                print(f"   진행 중... {stats['migrated']}/{stats['total']} 파일 마이그레이션 완료")

        except Exception as e:
            print(f"❌ 복사 실패: {filename} - {e}")
            stats['skipped'] += 1

    # 결과 출력
    print("")
    print("="*60)
    print("📊 마이그레이션 결과")
    print("="*60)
    print(f"✅ 성공: {stats['migrated']}개 파일")
    print(f"⏭️  건너뜀: {stats['skipped']}개 파일")
    print(f"📁 총 파일: {stats['total']}개")
    print("")

    print("파일 유형별:")
    for file_type, count in stats['by_type'].items():
        print(f"  - {file_type}: {count}개")
    print("")

    print("날짜별 파일 수 (상위 10개):")
    sorted_dates = sorted(stats['by_date'].items(), key=lambda x: x[1], reverse=True)
    for date_str, count in sorted_dates[:10]:
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        print(f"  - {formatted_date}: {count}개")

    if len(sorted_dates) > 10:
        print(f"  ... 외 {len(sorted_dates) - 10}개 날짜")

    print("")
    print("="*60)
    print("💡 원본 파일은 그대로 유지됩니다")
    print("   삭제하려면: rm -rf src/data_processing/results/*.xlsx")
    print("="*60)

def clean_old_results():
    """마이그레이션 후 원본 파일 정리 (선택사항)"""
    old_results_dir = Path("src/data_processing/results")

    print("")
    print("⚠️  원본 파일 정리를 시작합니다")
    print("   이 작업은 되돌릴 수 없습니다!")

    response = input("\n계속하시겠습니까? (yes/no): ")

    if response.lower() == 'yes':
        # Excel 파일만 삭제 (폴더는 유지)
        xlsx_files = list(old_results_dir.glob("*.xlsx"))
        csv_files = list(old_results_dir.glob("*.csv"))

        total = len(xlsx_files) + len(csv_files)

        for file_path in xlsx_files + csv_files:
            file_path.unlink()

        print(f"✅ {total}개 파일 삭제 완료")
        print(f"📁 {old_results_dir} 폴더는 유지됨")
    else:
        print("❌ 취소됨")

if __name__ == "__main__":
    import sys

    # 마이그레이션 실행
    migrate_results()

    # 정리 옵션
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_old_results()
