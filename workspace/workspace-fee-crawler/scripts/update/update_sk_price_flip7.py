"""SK_price의 플립 7을 플립 7 SK로 수정"""


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

def update_sk_price_flip7():
    """SK_price의 플립 7을 플립 7 SK로 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("sk_price")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # "플립 7" 찾아서 수정
        updated_count = 0
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
            
            # device_nm 컬럼 찾기 (보통 4번째 컬럼)
            if len(row) > 3 and row[3] == "플립 7":
                print(f"행 {i+1}: '{row[3]}' 발견")
                
                # "플립 7 SK"로 수정
                worksheet.update(f'D{i+1}', [["플립 7 SK"]])
                print(f"✅ '{row[3]}'을 '플립 7 SK'로 수정했습니다.")
                updated_count += 1
        
        if updated_count > 0:
            print(f"\n총 {updated_count}개 행을 수정했습니다.")
        else:
            print("\n수정할 '플립 7'을 찾지 못했습니다.")
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("SK_price의 '플립 7'을 '플립 7 SK'로 수정...")
    update_sk_price_flip7()
    print("\n완료!")