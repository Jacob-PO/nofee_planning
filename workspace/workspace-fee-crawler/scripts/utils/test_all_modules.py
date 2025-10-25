#!/usr/bin/env python3
"""
모든 모듈 실행 가능 여부 테스트
각 모듈을 import하고 기본 구조를 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_module(module_name, description):
    """모듈 import 및 실행 가능 여부 테스트"""
    try:
        print(f"\n{'='*70}")
        print(f"테스트: {description}")
        print(f"모듈: {module_name}")
        print('='*70)

        # 모듈 import
        module = __import__(module_name, fromlist=[''])
        print(f"✅ Import 성공")

        # 주요 클래스나 함수 확인
        if hasattr(module, '__all__'):
            print(f"📦 Export: {module.__all__}")

        # 모듈 속성 확인
        module_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
        if module_attrs:
            print(f"📋 주요 속성: {', '.join(module_attrs[:5])}{'...' if len(module_attrs) > 5 else ''}")

        return True, None

    except Exception as e:
        print(f"❌ 실패: {e}")
        return False, str(e)

def main():
    """모든 모듈 테스트 실행"""
    print("="*70)
    print("모든 모듈 실행 가능 여부 테스트")
    print("="*70)

    tests = [
        # 크롤러 모듈
        ("price_crawler.kt_crawler", "KT 크롤러"),
        ("price_crawler.sk_crawler", "SK 크롤러"),
        ("price_crawler.lg_crawler", "LG 크롤러"),

        # OCR 모듈
        ("image_ocr.clova_ocr", "CLOVA OCR"),
        ("image_ocr.extract_text_colors", "텍스트 색상 추출"),
        ("image_ocr.policy_calculator", "요금 정책 계산"),
        ("image_ocr.upload_calculated_to_sheets", "OCR 결과 업로드"),

        # 병합 모듈
        ("data_merge.kt_merge", "KT 병합"),
        ("data_merge.sk_merge", "SK 병합"),
        ("data_merge.lg_merge", "LG 병합"),
        ("data_merge.data_merge_main", "전체 병합"),
        ("data_merge.rebate_calculator", "리베이트 계산기"),
        ("data_merge.merge_and_upload", "병합 & 업로드"),

        # Summary 모듈
        ("price_summary.create_summary_clean", "Summary 생성"),
        ("price_summary.clean_support_sheet", "공시지원금 정제"),

        # 공통 모듈
        ("shared_config.config.paths", "PathManager"),
        ("shared_config.utils.google_sheets_upload", "Google Sheets 업로드"),
    ]

    results = []
    passed = 0
    failed = 0

    for module_name, description in tests:
        success, error = test_module(module_name, description)
        results.append((description, module_name, success, error))
        if success:
            passed += 1
        else:
            failed += 1

    # 결과 요약
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)

    print(f"\n✅ 성공: {passed}/{len(tests)}")
    print(f"❌ 실패: {failed}/{len(tests)}")

    if failed > 0:
        print("\n실패한 모듈:")
        for desc, mod, success, error in results:
            if not success:
                print(f"  ❌ {desc} ({mod})")
                print(f"     오류: {error}")

    print("\n성공한 모듈:")
    for desc, mod, success, error in results:
        if success:
            print(f"  ✅ {desc}")

    print("\n" + "="*70)
    if failed == 0:
        print("🎉 모든 모듈이 정상적으로 import 가능합니다!")
        return True
    else:
        print(f"⚠️  {failed}개 모듈에서 문제가 발견되었습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
