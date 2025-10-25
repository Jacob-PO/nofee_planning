import pandas as pd
import os
from pathlib import Path

def compare_bk_files():
    """비케이와 비케이2 파일 비교"""
    
    # OCR 결과 경로
    ocr_path = Path("/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/src/ocr/OCR/OCR_결과/20250715")
    
    # 파일들 읽기
    bk1_file = ocr_path / "250715_LG_비케이_tables_calculated.xlsx"
    bk2_file = ocr_path / "250715_LG_비케이2_tables_calculated.xlsx"
    
    print("=== 비케이 vs 비케이2 데이터 비교 ===\n")
    
    # 비케이1 데이터 읽기
    if bk1_file.exists():
        df_bk1 = pd.read_excel(bk1_file)
        print(f"비케이1 파일: {bk1_file.name}")
        print(f"  - 행 수: {len(df_bk1)}")
        print(f"  - 열 수: {len(df_bk1.columns)}")
        print(f"  - 컬럼: {list(df_bk1.columns[:10])}...")
        
        # 기기명 확인 (0열이 기기명)
        if len(df_bk1) > 3:
            devices_bk1 = []
            for idx in range(3, len(df_bk1)):
                device = df_bk1.iloc[idx, 0]
                if pd.notna(device) and device != '':
                    devices_bk1.append(str(device))
            print(f"  - 기기 수: {len(devices_bk1)}")
            print(f"  - 기기 목록: {devices_bk1[:10]}...")
    
    print("\n")
    
    # 비케이2 데이터 읽기
    if bk2_file.exists():
        df_bk2 = pd.read_excel(bk2_file)
        print(f"비케이2 파일: {bk2_file.name}")
        print(f"  - 행 수: {len(df_bk2)}")
        print(f"  - 열 수: {len(df_bk2.columns)}")
        print(f"  - 컬럼: {list(df_bk2.columns[:10])}...")
        
        # 기기명 확인
        if len(df_bk2) > 3:
            devices_bk2 = []
            for idx in range(3, len(df_bk2)):
                device = df_bk2.iloc[idx, 0]
                if pd.notna(device) and device != '':
                    devices_bk2.append(str(device))
            print(f"  - 기기 수: {len(devices_bk2)}")
            print(f"  - 기기 목록: {devices_bk2[:10]}...")
    
    # 두 파일의 차이점 분석
    if bk1_file.exists() and bk2_file.exists():
        print("\n=== 차이점 분석 ===")
        
        # 기기 목록 비교
        set_bk1 = set(devices_bk1)
        set_bk2 = set(devices_bk2)
        
        only_in_bk1 = set_bk1 - set_bk2
        only_in_bk2 = set_bk2 - set_bk1
        common = set_bk1 & set_bk2
        
        print(f"\n비케이1에만 있는 기기: {len(only_in_bk1)}개")
        if only_in_bk1:
            print(f"  {list(only_in_bk1)[:5]}...")
        
        print(f"\n비케이2에만 있는 기기: {len(only_in_bk2)}개")
        if only_in_bk2:
            print(f"  {list(only_in_bk2)[:5]}...")
        
        print(f"\n공통 기기: {len(common)}개")
        
        # 데이터 값 비교 (첫 번째 데이터 행 샘플)
        print("\n=== 데이터 값 비교 (샘플) ===")
        
        # 비케이1의 첫 데이터
        if len(df_bk1) > 3:
            print(f"\n비케이1 - 첫 번째 기기 데이터:")
            print(f"기기명: {df_bk1.iloc[3, 0]}")
            print(f"115K 번호이동: {df_bk1.iloc[3, 3] if len(df_bk1.columns) > 3 else 'N/A'}")
            print(f"115K 기기변경: {df_bk1.iloc[3, 4] if len(df_bk1.columns) > 4 else 'N/A'}")
        
        # 비케이2의 첫 데이터
        if len(df_bk2) > 3:
            print(f"\n비케이2 - 첫 번째 기기 데이터:")
            print(f"기기명: {df_bk2.iloc[3, 0]}")
            print(f"115K 번호이동: {df_bk2.iloc[3, 3] if len(df_bk2.columns) > 3 else 'N/A'}")
            print(f"115K 기기변경: {df_bk2.iloc[3, 4] if len(df_bk2.columns) > 4 else 'N/A'}")
    
    # 병합된 파일 확인
    print("\n=== 병합된 파일 분석 ===")
    merged_file = Path("/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/src/data_processing/results/lg_merged_data_20250715_144338.xlsx")
    
    if merged_file.exists():
        df_merged = pd.read_excel(merged_file)
        print(f"\n병합 파일: {merged_file.name}")
        print(f"전체 행 수: {len(df_merged)}")
        
        # dealer별 데이터 수
        if 'dealer' in df_merged.columns:
            dealer_counts = df_merged['dealer'].value_counts()
            print(f"\nDealer별 데이터:")
            print(dealer_counts)
            
            # 비케이 데이터 중복 확인
            bk_data = df_merged[df_merged['dealer'] == '비케이']
            if 'device_nm' in bk_data.columns:
                device_counts = bk_data['device_nm'].value_counts()
                duplicates = device_counts[device_counts > 1]
                
                print(f"\n비케이 데이터 중복 기기: {len(duplicates)}개")
                if len(duplicates) > 0:
                    print(duplicates)
                    
                    # 중복 기기의 상세 데이터 확인
                    print("\n중복 기기 상세 (갤럭시 S25 엣지 예시):")
                    if '갤럭시 S25 엣지' in duplicates.index:
                        edge_data = bk_data[bk_data['device_nm'] == '갤럭시 S25 엣지']
                        display_cols = ['device_nm', '번호이동_공시_115k', '기기변경_공시_115k']
                        print(edge_data[display_cols])

if __name__ == "__main__":
    compare_bk_files()