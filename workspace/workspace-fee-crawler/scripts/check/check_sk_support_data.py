"""SK Support 시트에서 플립7/폴드7 데이터 확인"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import glob

# Google Sheets 인증 설정
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 스프레드시트 ID
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"

def get_credentials():
    """Google Sheets 인증 파일 찾기"""
    credentials_dir = "src/config"
    json_files = glob.glob(os.path.join(credentials_dir, "*.json"))
    
    if not json_files:
        raise FileNotFoundError("Google Sheets API 키 파일을 찾을 수 없습니다.")
    
    credentials_file = json_files[0]
    print(f"사용할 credentials 파일: {credentials_file}")
    
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)

def check_sk_support_data():
    """SK Support 데이터 확인"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        support_worksheet = sheet.worksheet("support")
        
        # Support 데이터 가져오기
        all_values = support_worksheet.get_all_values()
        headers = all_values[0]
        data = all_values[1:]
        support_df = pd.DataFrame(data, columns=headers)
        
        # SK 데이터만 필터링
        sk_df = support_df[support_df['carrier'] == 'SK'].copy()
        
        # 플립7/폴드7 관련 데이터 찾기
        print("\n=== SK Support 시트에서 플립7/폴드7 검색 ===")
        
        # device_nm에서 플립7/폴드7 찾기
        flip7_mask = sk_df['device_nm'].str.contains('플립.*7|Flip.*7', case=False, na=False)
        fold7_mask = sk_df['device_nm'].str.contains('폴드.*7|Fold.*7', case=False, na=False)
        
        flip7_devices = sk_df[flip7_mask]
        fold7_devices = sk_df[fold7_mask]
        
        print(f"\n플립7 관련 기기: {len(flip7_devices)}개")
        if len(flip7_devices) > 0:
            unique_devices = flip7_devices['device_nm'].unique()
            for device in unique_devices[:10]:  # 최대 10개만 표시
                print(f"  - {device}")
            if len(unique_devices) > 10:
                print(f"  ... 외 {len(unique_devices) - 10}개")
                
        print(f"\n폴드7 관련 기기: {len(fold7_devices)}개")
        if len(fold7_devices) > 0:
            unique_devices = fold7_devices['device_nm'].unique()
            for device in unique_devices[:10]:  # 최대 10개만 표시
                print(f"  - {device}")
            if len(unique_devices) > 10:
                print(f"  ... 외 {len(unique_devices) - 10}개")
        
        # 109k 요금제 데이터 확인
        print("\n=== SK 109k 요금제 데이터 확인 ===")
        sk_109k = sk_df[sk_df['rate_plan_month_fee'] == '109000']
        print(f"SK 109k 요금제 데이터: {len(sk_109k)}개")
        
        # 109k 요금제 중 플립7/폴드7 확인
        flip7_109k = sk_109k[sk_109k['device_nm'].str.contains('플립.*7|Flip.*7', case=False, na=False)]
        fold7_109k = sk_109k[sk_109k['device_nm'].str.contains('폴드.*7|Fold.*7', case=False, na=False)]
        
        print(f"\n109k 요금제 중 플립7: {len(flip7_109k)}개")
        if len(flip7_109k) > 0:
            print("샘플 데이터:")
            for idx, row in flip7_109k.head(3).iterrows():
                print(f"  device_nm: {row['device_nm']}")
                print(f"  rate_plan: {row['rate_plan']}")
                print(f"  storage: {row.get('storage', 'N/A')}")
                print(f"  support_type: {row.get('support_type', 'N/A')}")
                print("  ---")
                
        print(f"\n109k 요금제 중 폴드7: {len(fold7_109k)}개")
        if len(fold7_109k) > 0:
            print("샘플 데이터:")
            for idx, row in fold7_109k.head(3).iterrows():
                print(f"  device_nm: {row['device_nm']}")
                print(f"  rate_plan: {row['rate_plan']}")
                print(f"  storage: {row.get('storage', 'N/A')}")
                print(f"  support_type: {row.get('support_type', 'N/A')}")
                print("  ---")
        
        # product_group_nm 매핑 확인
        print("\n=== Product_group_nm 매핑 확인 ===")
        pg_worksheet = sheet.worksheet("product_group_nm")
        pg_data = pg_worksheet.get_all_records()
        pg_df = pd.DataFrame(pg_data)
        
        # 플립7/폴드7 매핑 확인
        flip7_mappings = pg_df[pg_df['device_nm'].str.contains('플립.*7|Flip.*7', case=False, na=False)]
        fold7_mappings = pg_df[pg_df['device_nm'].str.contains('폴드.*7|Fold.*7', case=False, na=False)]
        
        print(f"\n플립7 매핑: {len(flip7_mappings)}개")
        for _, row in flip7_mappings.iterrows():
            print(f"  {row['device_nm']} -> {row['product_group_nm']} ({row['storage']})")
            
        print(f"\n폴드7 매핑: {len(fold7_mappings)}개")
        for _, row in fold7_mappings.iterrows():
            print(f"  {row['device_nm']} -> {row['product_group_nm']} ({row['storage']})")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_sk_support_data()