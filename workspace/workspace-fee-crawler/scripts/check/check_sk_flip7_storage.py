"""SK 플립7 storage 확인"""

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
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)

def check_sk_flip7_storage():
    """SK 플립7 storage 확인"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Support 데이터 확인
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # SK의 모든 플립7 관련 데이터
        sk_flip7_all = support_df[
            (support_df['carrier'] == 'SK') & 
            (support_df['device_nm'].str.contains('플립.*7', case=False, na=False))
        ]
        
        print(f"=== SK 플립7 전체 데이터: {len(sk_flip7_all)}개 ===\n")
        
        # device_nm별 storage 분포
        print("device_nm별 storage 분포:")
        device_storage = sk_flip7_all.groupby(['device_nm', 'storage']).size()
        for (device, storage), count in device_storage.items():
            print(f"  '{device}' - {storage}: {count}개")
            
        # 109k 근처 요금제 확인 (100k-110k)
        print("\n100k-110k 요금제 데이터:")
        high_rate_plans = sk_flip7_all[
            sk_flip7_all['rate_plan_month_fee'].astype(str).astype(float) >= 100000
        ]
        
        if len(high_rate_plans) > 0:
            for _, row in high_rate_plans.head(5).iterrows():
                print(f"  device_nm: '{row['device_nm']}'")
                print(f"  rate_plan_month_fee: {row['rate_plan_month_fee']}")
                print(f"  storage: {row['storage']}")
                print(f"  support_type: {row.get('support_type', 'N/A')}")
                print("  ---")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_sk_flip7_storage()