#!/usr/bin/env python3
"""
모든 Python 파일의 import 경로를 새 구조에 맞게 수정

변경 사항:
- from src.config.paths → from shared.config.paths
- from src.utils → from shared.utils
- from src.data_processing.rebate_calculator → from merge.rebate_calculator
- from src.crawlers → from crawler
- from src.ocr → from ocr
- from src.data_processing → from merge / from summary
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
            # src.config → shared.config
            (r'from src\.config\.paths', 'from shared.config.paths'),
            (r'from src\.config', 'from shared.config'),
            (r'import src\.config\.paths', 'import shared.config.paths'),

            # src.utils → shared.utils
            (r'from src\.utils', 'from shared.utils'),
            (r'import src\.utils', 'import shared.utils'),

            # src.data_processing.rebate_calculator → merge.rebate_calculator
            (r'from src\.data_processing\.rebate_calculator', 'from merge.rebate_calculator'),

            # src.data_processing (일반) → merge 또는 summary (컨텍스트에 따라)
            (r'from src\.data_processing', 'from merge'),

            # src.crawlers → crawler
            (r'from src\.crawlers', 'from crawler'),
            (r'import src\.crawlers', 'import crawler'),

            # src.ocr → ocr
            (r'from src\.ocr', 'from ocr'),
            (r'import src\.ocr', 'import ocr'),
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
    print("모든 Python 파일의 import 경로 수정")
    print("=" * 70)
    print()

    # 수정할 폴더들
    folders_to_fix = [
        base_dir / "crawler",
        base_dir / "ocr",
        base_dir / "merge",
        base_dir / "summary",
        base_dir / "shared",
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
        print("수정할 파일이 없습니다 (모든 import가 이미 정확함)")

if __name__ == "__main__":
    main()
