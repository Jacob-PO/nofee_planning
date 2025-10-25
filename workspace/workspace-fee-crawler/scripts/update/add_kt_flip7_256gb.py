"""KT 플립7 (띄어쓰기 없음) 256GB 매핑 추가"""


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

def check_and_update_kt_flip7():
    """KT 플립7 매핑 확인 및 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # "플립7" (띄어쓰기 없음) 확인
        found = False
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
            
            if row[0] == "플립7":
                print(f"찾음 - 행 {i+1}: '{row[0]}' -> {row[1]} ({row[2]})")
                
                # storage가 256GB인지 확인
                if row[2] != "256GB":
                    worksheet.update(f'C{i+1}', [["256GB"]])
                    print(f"✅ storage를 {row[2]}에서 256GB로 수정했습니다.")
                else:
                    print("이미 256GB입니다.")
                found = True
                break
                
        if not found:
            print("'플립7' 매핑이 없으므로 추가합니다.")
            # 마지막 행에 추가
            last_row = len(all_values) + 1
            new_row = ["플립7", "갤럭시 Z 플립 7", "256GB"]
            worksheet.update(f'A{last_row}:C{last_row}', [new_row])
            print(f"✅ 행 {last_row}: '플립7' -> 갤럭시 Z 플립 7 (256GB) 추가완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("KT 플립7 (띄어쓰기 없음) 매핑 확인 및 수정...")
    check_and_update_kt_flip7()
    print("\n완료!")