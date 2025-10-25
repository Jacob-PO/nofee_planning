"""SK 사전예약 플립 7 데이터 확인"""

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

def check_sk_preorder():
    """SK 사전예약 데이터 확인"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # SK_price 데이터 확인
        print("=== 1. SK_price 시트 확인 ===")
        sk_price_df = pd.DataFrame(sheet.worksheet("sk_price").get_all_records())
        sk_price_df['carrier'] = 'SK'
        
        # 사전예약 딜러의 플립 7 데이터
        preorder_flip7 = sk_price_df[
            (sk_price_df['dealer'] == '사전예약') & 
            (sk_price_df['device_nm'] == '플립 7')
        ]
        
        print(f"\nSK 사전예약 '플립 7' 데이터: {len(preorder_flip7)}개")
        if len(preorder_flip7) > 0:
            print("\n109k 요금제 관련 컬럼 값:")
            for col in preorder_flip7.columns:
                if '109k' in col:
                    values = preorder_flip7[col].dropna()
                    if len(values) > 0:
                        print(f"  {col}: {values.iloc[0]}")
                        
        # Support 데이터 확인
        print("\n=== 2. SK Support 시트 확인 ===")
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # SK 플립7 109k 데이터
        sk_flip7_109k = support_df[
            (support_df['carrier'] == 'SK') & 
            (support_df['device_nm'].str.contains('플립.*7', case=False, na=False)) &
            (support_df['rate_plan_month_fee'] == '109000')
        ]
        
        print(f"\nSK 플립7 109k Support 데이터: {len(sk_flip7_109k)}개")
        if len(sk_flip7_109k) > 0:
            unique_devices = sk_flip7_109k['device_nm'].unique()
            for device in unique_devices[:5]:
                matching = sk_flip7_109k[sk_flip7_109k['device_nm'] == device]
                storage_list = matching['storage'].unique()
                support_types = matching['support_type'].unique()
                print(f"  - device_nm: '{device}'")
                print(f"    storage: {list(storage_list)}")
                print(f"    support_type: {list(support_types)}")
                
        # Product_group_nm 매핑 확인
        print("\n=== 3. Product_group_nm 매핑 확인 ===")
        pg_df = pd.DataFrame(sheet.worksheet("product_group_nm").get_all_records())
        
        # '플립 7' 매핑 확인
        flip7_mapping = pg_df[pg_df['device_nm'] == '플립 7']
        if len(flip7_mapping) > 0:
            m = flip7_mapping.iloc[0]
            print(f"'플립 7' 매핑: {m['device_nm']} -> {m['product_group_nm']} ({m['storage']})")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_sk_preorder()