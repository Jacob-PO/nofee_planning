"""잘못된 매핑 제거하고 올바른 매핑 추가"""


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

def remove_and_add_correct_mapping():
    """잘못된 매핑 제거하고 올바른 매핑 추가"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("product_group_nm")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # 잘못 추가한 "플립 7 256GB" 제거
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
                
            if row[0] == "플립 7 256GB":
                print(f"❌ 행 {i+1}: 잘못된 매핑 '플립 7 256GB' 제거")
                worksheet.delete_rows(i+1)
                break
        
        # 대신 KT의 "플립 7"을 다른 product_group_nm으로 매핑
        # 예: "갤럭시 Z 플립 7 KT" 같은 구분자 추가
        print("\n=== 새로운 해결 방안 ===")
        print("KT와 SK가 같은 '플립 7' device_nm을 사용하지만 다른 storage가 필요합니다.")
        print("해결책: KT Support의 '플립 7'을 위한 별도 product_group_nm 사용")
        
        # 새로운 매핑 추가
        all_records = worksheet.get_all_records()
        last_row = len(all_records) + 2
        
        new_row = ["플립 7 (KT)", "갤럭시 Z 플립 7", "256GB"]
        worksheet.update(f'A{last_row}:C{last_row}', [new_row])
        print(f"\n✅ 행 {last_row}: '플립 7 (KT)' -> 갤럭시 Z 플립 7 (256GB) 추가")
        
        print("\n💡 참고: KT Support의 device_nm을 '플립 7'에서 '플립 7 (KT)'로 변경하거나,")
        print("   또는 Support 데이터 업로드 시 통신사별로 구분하는 로직이 필요합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("매핑 수정 작업...")
    remove_and_add_correct_mapping()
    print("\n완료!")