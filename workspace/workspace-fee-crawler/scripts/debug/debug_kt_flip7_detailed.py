"""KT 플립7 매칭 상세 디버깅"""

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

def debug_kt_flip7_detailed():
    """KT 플립7 매칭 상세 디버깅"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # 데이터 로드
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        pg_df = pd.DataFrame(sheet.worksheet("product_group_nm").get_all_records())
        kt_price_df = pd.DataFrame(sheet.worksheet("kt_price").get_all_records())
        
        print("=== 1. KT Support 시트의 '플립 7' 데이터 ===")
        kt_flip7_support = support_df[
            (support_df['carrier'] == 'KT') & 
            (support_df['device_nm'] == '플립 7')
        ]
        print(f"총 {len(kt_flip7_support)}개 데이터")
        for _, row in kt_flip7_support.iterrows():
            print(f"  - rate: {row['rate_plan_month_fee']}, support_type: {row['support_type']}")
        
        print("\n=== 2. Product_group_nm 매핑 체크 ===")
        # '플립 7' 매핑 확인
        flip7_space_mapping = pg_df[pg_df['device_nm'] == '플립 7']
        if len(flip7_space_mapping) > 0:
            m = flip7_space_mapping.iloc[0]
            print(f"'플립 7' 매핑: {m['device_nm']} -> {m['product_group_nm']} ({m['storage']})")
        else:
            print("'플립 7' 매핑이 없습니다!")
            
        # '플립7' 매핑 확인
        flip7_no_space_mapping = pg_df[pg_df['device_nm'] == '플립7']
        if len(flip7_no_space_mapping) > 0:
            m = flip7_no_space_mapping.iloc[0]
            print(f"'플립7' 매핑: {m['device_nm']} -> {m['product_group_nm']} ({m['storage']})")
        else:
            print("'플립7' 매핑이 없습니다!")
            
        print("\n=== 3. 매칭 시뮬레이션 ===")
        # Price의 '플립7'이 Support의 '플립 7'과 매칭되는지 확인
        
        # Step 1: '플립7' -> product_group_nm 매핑
        if len(flip7_no_space_mapping) > 0:
            target_pg = flip7_no_space_mapping.iloc[0]['product_group_nm']
            target_storage = flip7_no_space_mapping.iloc[0]['storage']
            print(f"Price '플립7' -> '{target_pg}' ({target_storage})")
            
            # Step 2: Support에서 같은 product_group_nm을 가진 데이터 찾기
            # '플립 7'이 같은 product_group_nm으로 매핑되는지 확인
            if len(flip7_space_mapping) > 0:
                support_pg = flip7_space_mapping.iloc[0]['product_group_nm']
                support_storage = flip7_space_mapping.iloc[0]['storage']
                print(f"Support '플립 7' -> '{support_pg}' ({support_storage})")
                
                if target_pg == support_pg:
                    print("✅ product_group_nm이 일치합니다!")
                    
                    # Storage 체크
                    if target_storage == support_storage:
                        print("✅ storage도 일치합니다!")
                    else:
                        print(f"❌ storage 불일치: Price({target_storage}) != Support({support_storage})")
                else:
                    print(f"❌ product_group_nm 불일치: Price({target_pg}) != Support({support_pg})")
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    debug_kt_flip7_detailed()