"""플립 7 SK 매핑 추가 및 플립 7 storage 수정"""

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

def add_flip7_sk_mapping():
    """플립 7 SK 매핑 추가 및 기존 플립 7 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 1. 플립 7 SK 매핑 추가
        all_records = worksheet.get_all_records()
        existing_df = pd.DataFrame(all_records)
        
        if "플립 7 SK" not in existing_df['device_nm'].values:
            last_row = len(existing_df) + 2
            new_row = ["플립 7 SK", "갤럭시 Z 플립 7", "512GB"]
            worksheet.update(f'A{last_row}:C{last_row}', [new_row])
            print(f"✅ 행 {last_row}: '플립 7 SK' -> 갤럭시 Z 플립 7 (512GB) 추가")
        else:
            print("'플립 7 SK' 매핑이 이미 있습니다.")
            
        # 2. 플립 7 storage를 256GB로 수정 (KT용)
        all_values = worksheet.get_all_values()
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
                
            if row[0] == "플립 7" and row[1] == "갤럭시 Z 플립 7":
                if row[2] != "256GB":
                    worksheet.update(f'C{i+1}', [["256GB"]])
                    print(f"✅ 행 {i+1}: '플립 7' storage를 256GB로 수정")
                else:
                    print(f"행 {i+1}: '플립 7'은 이미 256GB")
                break
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("플립 7 매핑 설정...")
    add_flip7_sk_mapping()
    print("\n완료!")