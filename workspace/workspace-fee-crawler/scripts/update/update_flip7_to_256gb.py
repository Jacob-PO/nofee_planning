"""플립 7의 storage를 256GB로 수정"""


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

def update_flip7_to_256gb():
    """플립 7 storage를 256GB로 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # "플립 7" 찾아서 수정
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
            
            if row[0] == "플립 7" and row[1] == "갤럭시 Z 플립 7":
                print(f"행 {i+1}: '{row[0]}' -> {row[1]} ({row[2]})")
                
                # storage를 256GB로 수정
                if row[2] != "256GB":
                    worksheet.update(f'C{i+1}', [["256GB"]])
                    print(f"✅ storage를 {row[2]}에서 256GB로 수정했습니다.")
                else:
                    print("이미 256GB입니다.")
                break
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("플립 7 storage를 256GB로 수정...")
    update_flip7_to_256gb()
    print("\n완료!")