"""KT 플립7의 모든 요금제 확인"""

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

def check_kt_flip7_rates():
    """KT 플립7 요금제 확인"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Support 데이터 가져오기
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # KT 플립 7 데이터 필터링
        kt_flip7 = support_df[
            (support_df['carrier'] == 'KT') & 
            (support_df['device_nm'] == '플립 7')
        ]
        
        print(f"=== KT '플립 7' Support 데이터: {len(kt_flip7)}개 ===\n")
        
        for idx, row in kt_flip7.iterrows():
            print(f"데이터 {idx+1}:")
            print(f"  device_nm: '{row['device_nm']}'")
            print(f"  rate_plan: {row['rate_plan']}")
            print(f"  rate_plan_month_fee: {row['rate_plan_month_fee']}")
            print(f"  storage: {row['storage']}")
            print(f"  support_type: {row.get('support_type', 'N/A')}")
            print(f"  total_support_fee: {row.get('total_support_fee', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_kt_flip7_rates()