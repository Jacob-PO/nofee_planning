#!/usr/bin/env python3
"""
통신사별 데이터 병합 및 Google Sheets 업데이트 통합 실행 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime

def run_merge():
    """모든 통신사 데이터 병합 실행"""
    print("="*60)
    print(f"데이터 병합 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # SK 데이터 병합
    print("\n1. SK 데이터 병합 중...")
    try:
        from data_merge.sk_merge import merge_sk_files
        sk_df = merge_sk_files()
        if sk_df is not None:
            print("✅ SK 데이터 병합 완료")
    except Exception as e:
        print(f"❌ SK 데이터 병합 실패: {e}")
    
    # KT 데이터 병합 (색상 포함)
    print("\n2. KT 데이터 병합 중...")
    try:
        from data_merge.kt_merge import merge_kt_files_with_colors
        kt_df = merge_kt_files_with_colors()
        if kt_df is not None:
            print("✅ KT 데이터 병합 완료 (색상 포함)")
    except Exception as e:
        print(f"❌ KT 데이터 병합 실패: {e}")
    
    # LG 데이터 병합
    print("\n3. LG 데이터 병합 중...")
    try:
        from data_merge.lg_merge import merge_lg_files
        lg_df = merge_lg_files()
        if lg_df is not None:
            print("✅ LG 데이터 병합 완료")
    except Exception as e:
        print(f"❌ LG 데이터 병합 실패: {e}")
    
    print("\n" + "="*60)
    print("병합 완료!")
    print("추출된 데이터는 extracted_data/ 폴더에 저장되었습니다.")

def expand_iphone_products():
    """iPhone 용량별 상품 확장 - 비활성화됨"""
    print("\n" + "="*60)
    print("❌ iPhone 용량별 상품 확장 기능이 비활성화되었습니다.")
    print("이 기능은 더 이상 사용되지 않습니다.")
    print("="*60)
    return
    
    # 아래 코드는 실행되지 않음
    # try:
    #     from data_merge.expand_iphone_storage import iPhoneStorageExpander
    #     expander = iPhoneStorageExpander()
    #     expander.process_all_carriers()
    #     print("\n✅ iPhone 용량별 상품 확장 완료")
    # except Exception as e:
    #     print(f"❌ iPhone 용량별 상품 확장 실패: {e}")

def apply_rebates():
    """병합된 데이터에 리베이트 적용"""
    print("\n" + "="*60)
    print("리베이트 적용 시작")
    print("="*60)

    try:
        from data_merge.rebate_calculator import RebateCalculator
        from shared_config.config.paths import PathManager
        from pathlib import Path
        import pandas as pd

        rebate_calc = RebateCalculator()
        pm = PathManager()

        # 각 통신사별 latest 파일 사용
        files = {
            'sk': pm.merged_latest_dir / 'sk_merged_latest.xlsx',
            'kt': pm.merged_latest_dir / 'kt_merged_with_colors_latest.xlsx',
            'lg': pm.merged_latest_dir / 'lg_merged_latest.xlsx'
        }
        
        for carrier, latest_file in files.items():
            if latest_file.exists():
                print(f"\n{carrier.upper()} 리베이트 적용 중: {latest_file.name}")
                
                # Excel 파일 읽기
                df = pd.read_excel(latest_file)
                
                # 각 행에 대해 리베이트 계산
                applied_count = 0
                debug_info = []
                for idx, row in df.iterrows():
                    if 'dealer' in row and 'device_name' in row:
                        dealer = row['dealer']
                        model = row['device_name']
                        
                        # 각 요금제별, 가입유형별, 지원타입별로 리베이트 적용
                        # 컬럼명 형식: 가입유형_지원타입_요금제
                        for col in df.columns:
                            if '_' in col and col not in ['date', 'carrier', 'dealer', 'device_name', 'additional_support', 'rebate_description']:
                                parts = col.split('_')
                                if len(parts) == 3:
                                    join_type = parts[0]  # 신규가입, 번호이동, 기기변경
                                    support_type = parts[1]  # 공시, 선약
                                    rate_str = parts[2]  # 43k, 50k, 69k, 79k, 100k, 109k
                                    
                                    # 요금제 숫자 추출
                                    rate_plan = int(rate_str.replace('k', ''))
                                    
                                    # 해당 셀에 값이 있는 경우만 처리
                                    try:
                                        cell_value = float(row[col])
                                        if pd.notna(cell_value) and cell_value > 0:
                                            # 리베이트 계산
                                            original_value = 0
                                            new_value, desc = rebate_calc.apply_dealer_rebate(
                                                dealer, model, rate_plan, original_value, 
                                                '선택약정' if support_type == '선약' else '공시', 
                                                join_type
                                            )
                                            
                                            if desc and new_value > 0:
                                                # 리베이트를 원본 금액에 더하기
                                                rebate_amount = new_value  # 이미 원 단위로 변환되어 있음
                                                df.at[idx, col] = cell_value + rebate_amount  # 원본 금액에 리베이트 추가
                                                
                                                applied_count += 1
                                                debug_info.append(f"{dealer} - {model} - {col}: {int(cell_value):,}원 → {int(cell_value + rebate_amount):,}원 (+{int(rebate_amount):,}원)")
                                    except (ValueError, TypeError):
                                        # 숫자로 변환할 수 없는 값은 무시
                                        continue
                
                print(f"  → {applied_count}개 셀에 리베이트 적용")
                if debug_info:
                    print("  리베이트 적용 내역:")
                    for info in debug_info[:10]:  # 처음 10개만 출력
                        print(f"    - {info}")
                    if len(debug_info) > 10:
                        print(f"    ... 외 {len(debug_info) - 10}개")
                
                # 리베이트 적용된 파일 저장
                with_colors = 'with_colors' in latest_file.name
                archive_path, rebated_latest_path = pm.get_merged_output_path(carrier, is_rebated=True, with_colors=with_colors)
                df.to_excel(archive_path, index=False)

                # latest 파일로 복사
                pm.save_with_archive(archive_path, archive_path, rebated_latest_path)
                print(f"✅ 리베이트 적용 완료")
                print(f"   📁 Archive: {archive_path}")
                print(f"   📁 Latest: {rebated_latest_path}")
                
    except Exception as e:
        print(f"❌ 리베이트 적용 실패: {e}")
        import traceback
        traceback.print_exc()

def update_google_sheets():
    """Google Sheets 업데이트 (latest 파일 사용)"""
    print("\n" + "="*60)
    print("Google Sheets 업데이트 시작")
    print("="*60)

    try:
        from shared_config.utils.google_sheets_upload import (
            update_kt_sheet_with_colors,
            update_sk_sheet_with_colors,
            update_lg_sheet_with_colors
        )
        from shared_config.config.paths import PathManager

        pm = PathManager()

        # rebated latest 파일 우선 사용, 없으면 merged latest 파일 사용
        for carrier in ['kt', 'sk', 'lg']:
            with_colors = (carrier == 'kt')
            rebated_file = pm.merged_latest_dir / f'{carrier}_rebated{"_with_colors" if with_colors else ""}_latest.xlsx'
            merged_file = pm.merged_latest_dir / f'{carrier}_merged{"_with_colors" if with_colors else ""}_latest.xlsx'

            if rebated_file.exists():
                print(f"\n{carrier.upper()} rebated 파일 사용: {rebated_file.name}")
            elif merged_file.exists():
                print(f"\n{carrier.upper()} merged 파일 사용 (rebated 없음): {merged_file.name}")
            else:
                print(f"\n⚠️ {carrier.upper()} 파일을 찾을 수 없습니다")
        
        if False:
            print("\n확장된 iPhone 데이터를 포함하여 업데이트합니다.")
            
        print("\n1. KT 시트 업데이트 중...")
        update_kt_sheet_with_colors()
        
        print("\n2. SK 시트 업데이트 중...")
        update_sk_sheet_with_colors()
        
        print("\n3. LG 시트 업데이트 중...")
        update_lg_sheet_with_colors()
        
        print("\n✅ Google Sheets 업데이트 완료")
        
    except Exception as e:
        print(f"❌ Google Sheets 업데이트 실패: {e}")

def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "merge":
            run_merge()
        elif sys.argv[1] == "rebate":
            apply_rebates()
        elif sys.argv[1] == "expand":
            expand_iphone_products()
        elif sys.argv[1] == "upload":
            update_google_sheets()
        elif sys.argv[1] == "all":
            run_merge()
            apply_rebates()  # 리베이트 적용 추가
            # expand_iphone_products()  # 아이폰 용량 확장 제거
            update_google_sheets()
        else:
            print("사용법:")
            print("  python run_all_merge.py merge   - 데이터 병합만 실행")
            print("  python run_all_merge.py rebate  - 리베이트 적용만 실행")
            print("  python run_all_merge.py expand  - iPhone 용량별 확장만 실행")
            print("  python run_all_merge.py upload  - Google Sheets 업로드만 실행")
            print("  python run_all_merge.py all     - 병합 + 리베이트 + 업로드 실행")
    else:
        # 인자가 없으면 병합, 리베이트, 업로드 실행
        run_merge()
        apply_rebates()  # 리베이트 적용 추가
        # expand_iphone_products()  # 아이폰 용량 확장 제거
        update_google_sheets()

if __name__ == "__main__":
    main()