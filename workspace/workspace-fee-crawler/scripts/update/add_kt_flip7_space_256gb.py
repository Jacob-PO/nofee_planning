"""KT를 위한 플립 7 (띄어쓰기 있음) 256GB 매핑 추가"""


import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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

def add_kt_flip7_space_256gb():
    """KT를 위한 플립 7 256GB 매핑 추가"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 현재 데이터 확인
        all_records = worksheet.get_all_records()
        pg_df = pd.DataFrame(all_records)
        
        # 현재 "플립 7" 매핑 확인
        flip7_space = pg_df[pg_df['device_nm'] == '플립 7']
        
        print("=== 현재 '플립 7' (띄어쓰기 있음) 매핑 ===")
        if len(flip7_space) > 0:
            for _, row in flip7_space.iterrows():
                print(f"  '{row['device_nm']}' -> {row['product_group_nm']} ({row['storage']})")
                
            # 512GB만 있고 256GB가 없다면 추가
            if not any(row['storage'] == '256GB' for _, row in flip7_space.iterrows()):
                print("\n256GB 매핑이 없으므로 추가합니다.")
                
                # 새로운 행 추가
                last_row = len(pg_df) + 2  # 헤더 포함
                new_row = ["플립 7 256GB", "갤럭시 Z 플립 7", "256GB"]
                worksheet.update(f'A{last_row}:C{last_row}', [new_row])
                print(f"✅ 행 {last_row}: '플립 7 256GB' -> 갤럭시 Z 플립 7 (256GB) 추가완료")
            else:
                print("\n이미 256GB 매핑이 있습니다.")
        else:
            print("'플립 7' 매핑이 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("KT를 위한 플립 7 256GB 매핑 추가...")
    add_kt_flip7_space_256gb()
    print("\n완료!")