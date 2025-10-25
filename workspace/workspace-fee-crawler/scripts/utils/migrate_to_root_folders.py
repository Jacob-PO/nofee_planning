#!/usr/bin/env python3
"""
루트 레벨 기능별 폴더 구조로 마이그레이션 스크립트

기존: data/crawler/, data/ocr/, data/merge/, data/summary/
새로운: crawler/, ocr/, merge/, summary/ (루트 레벨)
"""

import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def migrate_to_root():
    """data/* 하위의 기능 폴더들을 루트 레벨로 이동"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 60)
    print("루트 레벨 기능별 폴더 구조로 마이그레이션")
    print("=" * 60)
    print()

    # 백업 생성
    timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
    backup_name = f"data_backup_before_root_migration_{timestamp}"
    backup_dir = base_dir / backup_name

    print(f"📦 백업 생성 중: {backup_name}")
    if (base_dir / "data").exists():
        shutil.copytree(base_dir / "data", backup_dir / "data", dirs_exist_ok=True)
    print(f"✅ 백업 완료: {backup_dir}")
    print()

    migrations = []

    # 1. 크롤러 데이터 이동
    print("🔄 크롤러 폴더를 루트로 이동")
    old_crawler = base_dir / "data" / "crawler"
    new_crawler = base_dir / "crawler"
    if old_crawler.exists():
        if new_crawler.exists():
            # 이미 존재하면 병합
            for item in old_crawler.iterdir():
                dest = new_crawler / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(old_crawler)
        else:
            shutil.move(str(old_crawler), str(new_crawler))
        migrations.append(f"  ✓ data/crawler → crawler/")

        # data 경로를 raw로 변경 (더 명확하게)
        old_data = new_crawler / "raw"
        new_data = new_crawler / "data"
        if old_data.exists() and not new_data.exists():
            shutil.move(str(old_data), str(new_data))
            migrations.append(f"  ✓ crawler/raw → crawler/data")

    # 2. OCR 데이터 이동
    print("🔄 OCR 폴더를 루트로 이동")
    old_ocr = base_dir / "data" / "ocr"
    new_ocr = base_dir / "ocr"
    if old_ocr.exists():
        if new_ocr.exists():
            for item in old_ocr.iterdir():
                dest = new_ocr / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(old_ocr)
        else:
            shutil.move(str(old_ocr), str(new_ocr))
        migrations.append(f"  ✓ data/ocr → ocr/")

    # 3. 병합 데이터 이동
    print("🔄 병합 폴더를 루트로 이동")
    old_merge = base_dir / "data" / "merge"
    new_merge = base_dir / "merge"
    if old_merge.exists():
        if new_merge.exists():
            for item in old_merge.iterdir():
                dest = new_merge / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(old_merge)
        else:
            shutil.move(str(old_merge), str(new_merge))
        migrations.append(f"  ✓ data/merge → merge/")

    # 4. Summary 데이터 이동
    print("🔄 Summary 폴더를 루트로 이동")
    old_summary = base_dir / "data" / "summary"
    new_summary = base_dir / "summary"
    if old_summary.exists():
        if new_summary.exists():
            for item in old_summary.iterdir():
                dest = new_summary / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(old_summary)
        else:
            shutil.move(str(old_summary), str(new_summary))
        migrations.append(f"  ✓ data/summary → summary/")

    # 5. 분석 데이터 이동 (루트로)
    print("🔄 분석 폴더를 루트로 이동")
    old_analysis = base_dir / "data" / "analysis"
    new_analysis = base_dir / "analysis"
    if old_analysis.exists():
        if new_analysis.exists():
            for item in old_analysis.iterdir():
                dest = new_analysis / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
            shutil.rmtree(old_analysis)
        else:
            shutil.move(str(old_analysis), str(new_analysis))
        migrations.append(f"  ✓ data/analysis → analysis/")

    print()
    print("=" * 60)
    print("마이그레이션 완료")
    print("=" * 60)
    for migration in migrations:
        print(migration)
    print()

    # data 폴더 정리
    print("🧹 빈 폴더 정리")
    data_dir = base_dir / "data"
    if data_dir.exists():
        # data/outputs, data/temp 등 남은 것들 확인
        remaining = list(data_dir.iterdir())
        if remaining:
            print(f"  ⚠️  data/ 폴더에 남은 항목: {[r.name for r in remaining]}")
        else:
            data_dir.rmdir()
            print(f"  ✓ data/ 폴더 제거 (비어있음)")

    print()
    print("✅ 마이그레이션 완료!")
    print(f"📦 백업 위치: {backup_dir}")
    print()
    print("새 폴더 구조 (루트 레벨):")
    print("workspace-fee-crawler/")
    print("├── crawler/      # 🔍 크롤러 기능")
    print("├── ocr/          # 📊 OCR 기능")
    print("├── merge/        # 🔀 병합 기능")
    print("├── summary/      # 📋 Summary 기능")
    print("├── analysis/     # 📈 분석 결과")
    print("├── src/          # 소스 코드")
    print("└── temp/         # 임시 파일")

if __name__ == "__main__":
    migrate_to_root()
