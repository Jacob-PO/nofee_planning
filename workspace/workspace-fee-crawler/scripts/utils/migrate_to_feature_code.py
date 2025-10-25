#!/usr/bin/env python3
"""
기능별 폴더에 코드 포함 구조로 마이그레이션

목표 구조:
- crawler/ : 크롤러 코드 + 데이터
- ocr/ : OCR 코드 + 데이터
- merge/ : 병합 코드 + 데이터
- summary/ : Summary 코드 + 데이터
- shared/ : 공통 코드 (config, utils)
"""

import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def migrate_to_feature_code():
    """소스 코드를 각 기능 폴더로 이동"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 70)
    print("기능별 폴더에 코드 포함 구조로 마이그레이션")
    print("=" * 70)
    print()

    # 백업 생성
    timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
    backup_name = f"src_backup_before_feature_code_{timestamp}"
    backup_dir = base_dir / backup_name

    print(f"📦 src 폴더 백업 생성 중: {backup_name}")
    if (base_dir / "src").exists():
        shutil.copytree(base_dir / "src", backup_dir / "src", dirs_exist_ok=True)
    print(f"✅ 백업 완료: {backup_dir}")
    print()

    migrations = []

    # 1. 크롤러 코드 이동
    print("🔄 크롤러 코드 이동")
    crawler_files = [
        "kt_crawler.py",
        "sk_crawler.py",
        "lg_crawler.py",
        "__init__.py"
    ]

    src_crawlers = base_dir / "src" / "crawlers"
    dest_crawler = base_dir / "crawler"

    if src_crawlers.exists():
        for file in crawler_files:
            src_file = src_crawlers / file
            if src_file.exists():
                shutil.copy2(src_file, dest_crawler / file)
                migrations.append(f"  ✓ src/crawlers/{file} → crawler/{file}")

    # 2. OCR 코드 이동
    print("🔄 OCR 코드 이동")
    ocr_files = [
        "clova_ocr.py",
        "extract_text_colors.py",
        "policy_calculator.py",
        "upload_calculated_to_sheets.py",
        "policy_config.yaml",
        "__init__.py"
    ]

    src_ocr = base_dir / "src" / "ocr"
    dest_ocr = base_dir / "ocr"

    if src_ocr.exists():
        for file in ocr_files:
            src_file = src_ocr / file
            if src_file.exists():
                shutil.copy2(src_file, dest_ocr / file)
                migrations.append(f"  ✓ src/ocr/{file} → ocr/{file}")

    # 3. 병합 코드 이동
    print("🔄 병합 코드 이동")
    merge_files = [
        "kt_merge.py",
        "sk_merge.py",
        "lg_merge.py",
        "data_merge_main.py",
        "merge_and_upload.py",
        "rebate_calculator.py",
        "__init__.py"
    ]

    src_data_processing = base_dir / "src" / "data_processing"
    dest_merge = base_dir / "merge"

    # __init__.py 생성
    (dest_merge / "__init__.py").touch()

    if src_data_processing.exists():
        for file in merge_files:
            src_file = src_data_processing / file
            if src_file.exists():
                shutil.copy2(src_file, dest_merge / file)
                migrations.append(f"  ✓ src/data_processing/{file} → merge/{file}")

    # 4. Summary 코드 이동
    print("🔄 Summary 코드 이동")
    summary_files = [
        "create_summary_clean.py",
        "clean_support_sheet.py",
        "__init__.py"
    ]

    dest_summary = base_dir / "summary"

    # __init__.py 생성
    (dest_summary / "__init__.py").touch()

    if src_data_processing.exists():
        for file in summary_files:
            src_file = src_data_processing / file
            if src_file.exists():
                shutil.copy2(src_file, dest_summary / file)
                migrations.append(f"  ✓ src/data_processing/{file} → summary/{file}")

    # 5. 공통 코드는 shared 폴더로
    print("🔄 공통 코드를 shared 폴더로 이동")
    shared_dir = base_dir / "shared"
    shared_dir.mkdir(exist_ok=True)

    # config 이동
    src_config = base_dir / "src" / "config"
    dest_config = shared_dir / "config"
    if src_config.exists():
        shutil.copytree(src_config, dest_config, dirs_exist_ok=True)
        migrations.append(f"  ✓ src/config → shared/config")

    # utils 이동
    src_utils = base_dir / "src" / "utils"
    dest_utils = shared_dir / "utils"
    if src_utils.exists():
        shutil.copytree(src_utils, dest_utils, dirs_exist_ok=True)
        migrations.append(f"  ✓ src/utils → shared/utils")

    # __init__.py 생성
    (shared_dir / "__init__.py").touch()
    (dest_config / "__init__.py").touch() if dest_config.exists() else None
    (dest_utils / "__init__.py").touch() if dest_utils.exists() else None

    print()
    print("=" * 70)
    print("마이그레이션 완료")
    print("=" * 70)
    for migration in migrations:
        print(migration)
    print()

    print("✅ 코드 마이그레이션 완료!")
    print(f"📦 백업 위치: {backup_dir}")
    print()
    print("새 폴더 구조:")
    print("workspace-fee-crawler/")
    print("├── crawler/      # 크롤러 코드 + 데이터")
    print("├── ocr/          # OCR 코드 + 데이터")
    print("├── merge/        # 병합 코드 + 데이터")
    print("├── summary/      # Summary 코드 + 데이터")
    print("├── shared/       # 공통 코드 (config, utils)")
    print("└── scripts/      # 유틸리티 스크립트")

if __name__ == "__main__":
    migrate_to_feature_code()
