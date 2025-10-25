#!/usr/bin/env python3
"""
폴더명 변경에 따른 import 경로 수정

crawler → price_crawler
ocr → image_ocr
merge → data_merge
summary → price_summary
shared → shared_config
"""

import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """파일의 import 문을 수정"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Import 경로 수정
        replacements = [
            # shared → shared_config
            (r'\bfrom shared\.', 'from shared_config.'),
            (r'\bimport shared\.', 'import shared_config.'),

            # crawler → price_crawler
            (r'\bfrom crawler\.', 'from price_crawler.'),
            (r'\bimport crawler\.', 'import price_crawler.'),

            # ocr → image_ocr
            (r'\bfrom ocr\.', 'from image_ocr.'),
            (r'\bimport ocr\.', 'import image_ocr.'),

            # merge → data_merge
            (r'\bfrom merge\.', 'from data_merge.'),
            (r'\bimport merge\.', 'import data_merge.'),

            # summary → price_summary
            (r'\bfrom summary\.', 'from price_summary.'),
            (r'\bimport summary\.', 'import price_summary.'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, file_path.name

        return False, None

    except Exception as e:
        print(f"  ⚠️  {file_path.name}: {e}")
        return False, None

def main():
    """모든 Python 파일의 import 수정"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 70)
    print("폴더명 변경에 따른 import 경로 수정")
    print("=" * 70)
    print()

    # 수정할 폴더들
    folders_to_fix = [
        base_dir / "price_crawler",
        base_dir / "image_ocr",
        base_dir / "data_merge",
        base_dir / "price_summary",
        base_dir / "shared_config",
    ]

    modified_files = []

    for folder in folders_to_fix:
        if not folder.exists():
            continue

        print(f"🔍 {folder.name}/ 폴더 검사 중...")

        # 모든 .py 파일 찾기
        py_files = list(folder.glob("**/*.py"))

        for py_file in py_files:
            if py_file.name == "__pycache__":
                continue

            modified, filename = fix_imports_in_file(py_file)
            if modified:
                relative_path = py_file.relative_to(base_dir)
                modified_files.append(str(relative_path))
                print(f"  ✓ {relative_path}")

    print()
    print("=" * 70)
    print("Import 수정 완료")
    print("=" * 70)
    print(f"수정된 파일 수: {len(modified_files)}")
    print()

    if modified_files:
        print("수정된 파일 목록:")
        for file in modified_files:
            print(f"  • {file}")
    else:
        print("수정할 파일이 없습니다")

if __name__ == "__main__":
    main()
