"""SK_price 시트의 플립7/폴드7 매핑 추가"""

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

def add_sk_price_mappings():
    """SK_price의 플립7/폴드7 매핑 추가"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 기존 데이터 가져오기
        all_records = worksheet.get_all_records()
        existing_df = pd.DataFrame(all_records)
        
        # 추가할 SK_price 매핑
        new_mappings = [
            # SK_price의 단순화된 이름들
            ("플립 7", "갤럭시 Z 플립 7", "512GB"),
            ("폴드 7", "갤럭시 Z 폴드 7", "512GB"),
        ]
        
        # 새로운 행 생성
        new_rows = []
        for device_nm, product_group_nm, storage in new_mappings:
            # 이미 존재하는지 확인
            if device_nm not in existing_df['device_nm'].values:
                new_rows.append([device_nm, product_group_nm, storage])
                print(f"추가: {device_nm} -> {product_group_nm} ({storage})")
            else:
                print(f"이미 존재: {device_nm}")
        
        # 새로운 행이 있으면 추가
        if new_rows:
            # 현재 마지막 행 찾기
            last_row = len(existing_df) + 2  # 헤더 포함
            
            # 새로운 데이터 추가
            for i, row in enumerate(new_rows):
                row_number = last_row + i
                worksheet.update(f'A{row_number}:C{row_number}', [row])
            
            print(f"\n✅ {len(new_rows)}개의 새로운 매핑이 추가되었습니다.")
        else:
            print("\n추가할 새로운 매핑이 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("SK_price 플립7/폴드7 매핑 추가 시작...")
    add_sk_price_mappings()
    print("\n완료!")