"""SK '플립 7'의 storage를 512GB로 수정"""

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

def fix_sk_flip7_storage():
    """SK '플립 7'의 storage 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # SK의 "플립 7" 찾아서 수정
        updated_count = 0
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
            
            # SK의 "플립 7" (띄어쓰기 있음)
            if row[0] == "플립 7" and row[1] == "갤럭시 Z 플립 7":
                # 이미 KT용으로 256GB로 설정되어 있으므로 행 번호만 출력
                print(f"행 {i+1}: SK/KT 공용 '{row[0]}' -> {row[1]} ({row[2]})")
                print("주의: 이 매핑은 KT와 SK가 공유하고 있습니다.")
                print("KT는 256GB, SK는 512GB가 필요합니다.")
                
        # SK 전용 매핑이 필요한지 확인
        print("\n=== 해결 방안 ===")
        print("SK_price의 '플립 7'을 다른 이름으로 변경하거나,")
        print("별도의 SK 전용 매핑을 추가해야 합니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("SK '플립 7' storage 확인...")
    fix_sk_flip7_storage()
    print("\n완료!")