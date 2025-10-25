#!/usr/bin/env python3
"""새 구조에서 import 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """주요 모듈 import 테스트"""
    print("=" * 70)
    print("새 구조 Import 테스트")
    print("=" * 70)
    print()

    tests_passed = 0
    tests_failed = 0

    # 1. Shared 모듈 테스트
    print("1️⃣  Shared 모듈 테스트")
    try:
        from shared_config.config.paths import PathManager, get_log_path, get_checkpoint_path
        pm = PathManager()

        assert pm.crawler_dir.exists(), "crawler_dir 없음"
        assert pm.ocr_dir.exists(), "ocr_dir 없음"
        assert pm.merge_dir.exists(), "merge_dir 없음"
        assert pm.summary_dir.exists(), "summary_dir 없음"

        print("  ✅ shared.config.paths import 성공")
        print(f"     - crawler: {pm.crawler_dir}")
        print(f"     - ocr: {pm.ocr_dir}")
        print(f"     - merge: {pm.merge_dir}")
        print(f"     - summary: {pm.summary_dir}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ shared.config.paths 실패: {e}")
        tests_failed += 1

    print()

    # 2. 크롤러 모듈 테스트
    print("2️⃣  크롤러 모듈 테스트")
    crawler_modules = [
        ("price_crawler.kt_crawler", "KT 크롤러"),
        ("price_crawler.sk_crawler", "SK 크롤러"),
        ("price_crawler.lg_crawler", "LG 크롤러"),
    ]

    for module_name, description in crawler_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {description} import 성공")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ {description} 실패: {e}")
            tests_failed += 1

    print()

    # 3. 병합 모듈 테스트
    print("3️⃣  병합 모듈 테스트")
    merge_modules = [
        ("data_merge.kt_merge", "KT 병합"),
        ("data_merge.sk_merge", "SK 병합"),
        ("data_merge.lg_merge", "LG 병합"),
        ("data_merge.data_merge_main", "병합 메인"),
        ("data_merge.rebate_calculator", "리베이트 계산기"),
    ]

    for module_name, description in merge_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {description} import 성공")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ {description} 실패: {e}")
            tests_failed += 1

    print()

    # 4. Summary 모듈 테스트
    print("4️⃣  Summary 모듈 테스트")
    try:
        from price_summary.create_summary_clean import CleanSummaryCreator
        print("  ✅ Summary 생성 import 성공")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Summary 생성 실패: {e}")
        tests_failed += 1

    print()

    # 5. OCR 모듈 테스트
    print("5️⃣  OCR 모듈 테스트")
    try:
        from image_ocr.clova_ocr import OCRTerminalUI
        print("  ✅ CLOVA OCR import 성공")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ CLOVA OCR 실패: {e}")
        tests_failed += 1

    print()

    # 6. Utils 테스트
    print("6️⃣  Utils 모듈 테스트")
    try:
        from shared_config.utils.google_sheets_upload import update_kt_sheet_with_colors
        print("  ✅ Google Sheets 업로드 import 성공")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Google Sheets 업로드 실패: {e}")
        tests_failed += 1

    print()

    # 결과 요약
    print("=" * 70)
    print("테스트 결과")
    print("=" * 70)
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
