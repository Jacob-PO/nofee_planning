#!/usr/bin/env python3
"""
불필요한 폴더 및 파일 정리 스크립트

유지할 폴더:
- crawler/, ocr/, merge/, summary/, shared/
- analysis/, scripts/, temp/
- run.sh, .gitignore, README.md

삭제할 폴더:
- src/ (코드 이미 이동됨)
- data/ (데이터 이미 기능 폴더로 이동됨)
- logs/ (로그 이미 기능 폴더로 이동됨)
- output/ (출력 이미 기능 폴더로 이동됨)
- assets/, docs/, tests/ (사용하지 않음)
- 백업 폴더들 (별도 보관)
"""

import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def cleanup():
    """불필요한 폴더 정리"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 70)
    print("불필요한 폴더 및 파일 정리")
    print("=" * 70)
    print()

    # 삭제할 폴더 목록
    folders_to_remove = [
        "src",          # 코드 이미 기능 폴더로 이동
        "data",         # 데이터 이미 기능 폴더로 이동
        "logs",         # 로그 이미 기능 폴더로 이동
        "output",       # 출력 이미 기능 폴더로 이동
        "assets",       # 사용하지 않음
        "docs",         # 사용하지 않음
        "tests",        # 사용하지 않음
    ]

    # 백업 폴더 (별도 압축 후 삭제)
    backup_folders = [
        "data_backup_before_feature_migration_20251015_120439",
        "data_backup_before_root_migration_20251015_131416",
        "src_backup_before_feature_code_20251015_132239",
        "workspace-fee-crawler_backup_20251015_113713",
    ]

    removed = []
    backed_up = []

    # 1. 백업 폴더 압축
    print("📦 백업 폴더 처리 중...")
    backup_archive = base_dir / "backups"
    backup_archive.mkdir(exist_ok=True)

    for folder_name in backup_folders:
        folder_path = base_dir / folder_name
        if folder_path.exists():
            print(f"  🗜️  {folder_name} 압축 및 이동 중...")
            # 백업 폴더로 이동
            dest = backup_archive / folder_name
            if not dest.exists():
                shutil.move(str(folder_path), str(dest))
                backed_up.append(folder_name)
            else:
                shutil.rmtree(folder_path)
                backed_up.append(f"{folder_name} (중복 제거)")

    print()

    # 2. 불필요한 폴더 삭제
    print("🗑️  불필요한 폴더 삭제 중...")
    for folder_name in folders_to_remove:
        folder_path = base_dir / folder_name
        if folder_path.exists():
            print(f"  ❌ {folder_name}/ 삭제 중...")
            shutil.rmtree(folder_path)
            removed.append(folder_name)

    print()

    # 3. data/outputs 폴더 처리 (남아있을 수 있음)
    data_outputs = base_dir / "data" / "outputs"
    if data_outputs.exists():
        print("🗑️  data/outputs 잔여 폴더 삭제...")
        shutil.rmtree(data_outputs)
        removed.append("data/outputs")

    print()
    print("=" * 70)
    print("정리 완료")
    print("=" * 70)
    print()

    if backed_up:
        print("📦 백업 폴더 처리:")
        for item in backed_up:
            print(f"  ✓ {item} → backups/")
    print()

    if removed:
        print("🗑️  삭제된 폴더:")
        for folder in removed:
            print(f"  ✓ {folder}/")
    print()

    # 4. 최종 구조 확인
    print("=" * 70)
    print("최종 폴더 구조")
    print("=" * 70)
    print()

    essential_folders = [
        "crawler",
        "ocr",
        "merge",
        "summary",
        "shared",
        "analysis",
        "scripts",
        "temp",
        "backups",
    ]

    print("workspace-fee-crawler/")
    for folder in sorted(essential_folders):
        folder_path = base_dir / folder
        if folder_path.exists():
            size_mb = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file()) / (1024 * 1024)
            print(f"├── {folder}/ ({size_mb:.1f} MB)")

    print("├── run.sh")
    print("├── .gitignore")
    print("└── README.md")
    print()

    print("✅ 정리 완료!")
    print(f"📁 백업 위치: {backup_archive}")

if __name__ == "__main__":
    cleanup()
