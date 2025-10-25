#!/usr/bin/env python3
"""import 테스트 스크립트 - 새 PathManager가 모든 모듈에서 정상 작동하는지 확인"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """주요 모듈 import 및 PathManager 테스트"""
    print("=" * 60)
    print("Import 테스트 시작")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # 1. PathManager 테스트
    print("1️⃣ PathManager 테스트")
    try:
        from src.config.paths import PathManager, get_log_path, get_checkpoint_path
        pm = PathManager()

        # 주요 경로 확인
        assert pm.crawler_dir.exists(), "crawler_dir 없음"
        assert pm.ocr_dir.exists(), "ocr_dir 없음"
        assert pm.merge_dir.exists(), "merge_dir 없음"
        assert pm.summary_dir.exists(), "summary_dir 없음"

        print("  ✅ PathManager import 성공")
        print(f"     - crawler: {pm.crawler_dir}")
        print(f"     - ocr: {pm.ocr_dir}")
        print(f"     - merge: {pm.merge_dir}")
        print(f"     - summary: {pm.summary_dir}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ PathManager 실패: {e}")
        tests_failed += 1

    print()

    # 2. 데이터 처리 모듈 테스트
    print("2️⃣ 데이터 처리 모듈 테스트")
    modules_to_test = [
        ("src.data_processing.kt_merge", "KT 병합"),
        ("src.data_processing.sk_merge", "SK 병합"),
        ("src.data_processing.lg_merge", "LG 병합"),
        ("src.data_processing.data_merge_main", "병합 메인"),
        ("src.data_processing.create_summary_clean", "Summary 생성"),
    ]

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {description} import 성공")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ {description} 실패: {e}")
            tests_failed += 1

    print()

    # 3. 유틸리티 모듈 테스트
    print("3️⃣ 유틸리티 모듈 테스트")
    try:
        from src.utils.google_sheets_upload import update_kt_sheet_with_colors
        print("  ✅ Google Sheets 업로드 import 성공")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Google Sheets 업로드 실패: {e}")
        tests_failed += 1

    print()

    # 4. OCR 모듈 테스트
    print("4️⃣ OCR 모듈 테스트")
    try:
        from src.ocr.clova_ocr import OCRTerminalUI
        print("  ✅ CLOVA OCR import 성공")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ CLOVA OCR 실패: {e}")
        tests_failed += 1

    print()

    # 결과 요약
    print("=" * 60)
    print("테스트 결과")
    print("=" * 60)
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print(f"합계: {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("⚠️  일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
