#!/usr/bin/env python3
"""
기능별 폴더 구조로 마이그레이션 스크립트

기존 통합 구조:
  data/outputs/merged/, data/outputs/summary/, logs/

새로운 기능별 구조:
  data/crawler/, data/ocr/, data/merge/, data/summary/
"""

import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def migrate_data():
    """기존 데이터를 새 구조로 마이그레이션"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 60)
    print("기능별 폴더 구조 마이그레이션")
    print("=" * 60)
    print()

    # 백업 생성
    timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
    backup_name = f"data_backup_before_feature_migration_{timestamp}"
    backup_dir = base_dir / backup_name

    print(f"📦 백업 생성 중: {backup_name}")
    if (base_dir / "data").exists():
        shutil.copytree(base_dir / "data", backup_dir / "data", dirs_exist_ok=True)
    if (base_dir / "logs").exists():
        shutil.copytree(base_dir / "logs", backup_dir / "logs", dirs_exist_ok=True)
    print(f"✅ 백업 완료: {backup_dir}")
    print()

    migrations = []

    # 1. 크롤러 데이터 마이그레이션
    print("🔄 크롤러 데이터 마이그레이션")
    old_raw = base_dir / "data" / "raw"
    new_raw = base_dir / "data" / "crawler" / "raw"
    if old_raw.exists():
        new_raw.parent.mkdir(parents=True, exist_ok=True)
        if not new_raw.exists():
            shutil.move(str(old_raw), str(new_raw))
            migrations.append(f"  ✓ data/raw → data/crawler/raw")

    old_checkpoints = base_dir / "data" / "checkpoints"
    new_checkpoints = base_dir / "data" / "crawler" / "checkpoints"
    if old_checkpoints.exists():
        new_checkpoints.parent.mkdir(parents=True, exist_ok=True)
        if not new_checkpoints.exists():
            shutil.move(str(old_checkpoints), str(new_checkpoints))
            migrations.append(f"  ✓ data/checkpoints → data/crawler/checkpoints")

    old_crawler_logs = base_dir / "logs" / "crawler"
    new_crawler_logs = base_dir / "data" / "crawler" / "logs"
    if old_crawler_logs.exists():
        new_crawler_logs.parent.mkdir(parents=True, exist_ok=True)
        if not new_crawler_logs.exists():
            shutil.move(str(old_crawler_logs), str(new_crawler_logs))
            migrations.append(f"  ✓ logs/crawler → data/crawler/logs")

    # 2. OCR 데이터 마이그레이션
    print("🔄 OCR 데이터 마이그레이션")
    old_ocr = base_dir / "data" / "ocr"
    new_ocr = base_dir / "data" / "ocr"
    # OCR은 이미 data/ocr에 있으므로 logs만 이동

    old_ocr_logs = base_dir / "logs" / "ocr"
    new_ocr_logs = base_dir / "data" / "ocr" / "logs"
    if old_ocr_logs.exists():
        new_ocr_logs.parent.mkdir(parents=True, exist_ok=True)
        if not new_ocr_logs.exists():
            shutil.move(str(old_ocr_logs), str(new_ocr_logs))
            migrations.append(f"  ✓ logs/ocr → data/ocr/logs")

    # 3. 병합 데이터 마이그레이션
    print("🔄 병합 데이터 마이그레이션")
    old_merged = base_dir / "data" / "outputs" / "merged"
    new_merged = base_dir / "data" / "merge" / "output"
    if old_merged.exists():
        new_merged.parent.mkdir(parents=True, exist_ok=True)
        if not new_merged.exists():
            shutil.move(str(old_merged), str(new_merged))
            migrations.append(f"  ✓ data/outputs/merged → data/merge/output")

    old_merge_logs = base_dir / "logs" / "merge"
    new_merge_logs = base_dir / "data" / "merge" / "logs"
    if old_merge_logs.exists():
        new_merge_logs.parent.mkdir(parents=True, exist_ok=True)
        if not new_merge_logs.exists():
            shutil.move(str(old_merge_logs), str(new_merge_logs))
            migrations.append(f"  ✓ logs/merge → data/merge/logs")

    # 4. Summary 데이터 마이그레이션
    print("🔄 Summary 데이터 마이그레이션")
    old_summary = base_dir / "data" / "outputs" / "summary"
    new_summary = base_dir / "data" / "summary" / "output"
    if old_summary.exists():
        new_summary.parent.mkdir(parents=True, exist_ok=True)
        if not new_summary.exists():
            shutil.move(str(old_summary), str(new_summary))
            migrations.append(f"  ✓ data/outputs/summary → data/summary/output")

    old_general_logs = base_dir / "logs" / "general"
    new_summary_logs = base_dir / "data" / "summary" / "logs"
    if old_general_logs.exists():
        new_summary_logs.parent.mkdir(parents=True, exist_ok=True)
        if not new_summary_logs.exists():
            shutil.move(str(old_general_logs), str(new_summary_logs))
            migrations.append(f"  ✓ logs/general → data/summary/logs")

    # 5. 분석 데이터 (그대로 유지)
    print("🔄 분석 데이터 (위치 유지)")
    old_analysis = base_dir / "data" / "analysis"
    if old_analysis.exists():
        migrations.append(f"  ✓ data/analysis (유지)")

    print()
    print("=" * 60)
    print("마이그레이션 완료")
    print("=" * 60)
    for migration in migrations:
        print(migration)
    print()

    # 빈 폴더 정리
    print("🧹 빈 폴더 정리")
    old_outputs = base_dir / "data" / "outputs"
    if old_outputs.exists() and not list(old_outputs.iterdir()):
        old_outputs.rmdir()
        print(f"  ✓ data/outputs 폴더 제거")

    old_logs = base_dir / "logs"
    if old_logs.exists() and not list(old_logs.iterdir()):
        old_logs.rmdir()
        print(f"  ✓ logs 폴더 제거")

    print()
    print("✅ 마이그레이션 완료!")
    print(f"📦 백업 위치: {backup_dir}")
    print()
    print("새 폴더 구조:")
    print("data/")
    print("├── crawler/      # 크롤러 기능")
    print("├── ocr/          # OCR 기능")
    print("├── merge/        # 병합 기능")
    print("├── summary/      # Summary 기능")
    print("└── analysis/     # 분석 결과")

if __name__ == "__main__":
    migrate_data()
