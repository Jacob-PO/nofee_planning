"""SK와 KT 플립7이 모두 매칭되도록 product_group_nm 수정"""

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

def fix_flip7_for_both():
    """SK와 KT 플립7 매칭 문제 해결"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # 1. 현재 문제 분석
        print("=== 현재 상황 분석 ===")
        
        # Support 데이터 확인
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # KT Support 데이터
        kt_support = support_df[(support_df['carrier'] == 'KT') & (support_df['device_nm'] == '플립 7')]
        print(f"\nKT Support '플립 7': {len(kt_support)}개")
        if len(kt_support) > 0:
            print(f"  storage: {kt_support['storage'].iloc[0]}")
            
        # SK Support 데이터  
        sk_support = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'].str.contains('플립.*7.*512', case=False, na=False))]
        print(f"\nSK Support '갤럭시 Z 플립 7 512G': {len(sk_support)}개")
        if len(sk_support) > 0:
            print(f"  storage: {sk_support['storage'].iloc[0]}")
        
        # Price 데이터 확인
        kt_price_df = pd.DataFrame(sheet.worksheet("kt_price").get_all_records())
        sk_price_df = pd.DataFrame(sheet.worksheet("sk_price").get_all_records())
        
        kt_flip7 = kt_price_df[kt_price_df['device_nm'] == '플립7']
        sk_flip7 = sk_price_df[sk_price_df['device_nm'] == '플립 7']
        
        print(f"\nKT_price '플립7': {len(kt_flip7)}개")
        print(f"SK_price '플립 7': {len(sk_flip7)}개")
        
        # 2. product_group_nm 수정
        print("\n=== product_group_nm 수정 ===")
        worksheet = sheet.worksheet("product_group_nm")
        all_values = worksheet.get_all_values()
        
        # 필요한 매핑 찾기
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
                
            # KT의 "플립7"은 이미 256GB로 설정되어 있어야 함
            if row[0] == "플립7" and row[2] != "256GB":
                worksheet.update(f'C{i+1}', [["256GB"]])
                print(f"✅ 행 {i+1}: '플립7' storage를 256GB로 수정")
                
            # SK의 "플립 7"은 512GB로 설정되어 있어야 함
            elif row[0] == "플립 7" and row[1] == "갤럭시 Z 플립 7" and row[2] != "512GB":
                worksheet.update(f'C{i+1}', [["512GB"]])
                print(f"✅ 행 {i+1}: '플립 7' storage를 512GB로 수정")
        
        # 3. KT Support의 "플립 7"을 위한 매핑 추가 확인
        # KT Support에는 "플립 7" (띄어쓰기 있음)이 있는데 
        # KT_price에는 "플립7" (띄어쓰기 없음)이 있음
        # 이미 "플립7" -> 256GB 매핑이 있으므로 KT는 해결됨
        
        print("\n=== 매핑 완료 ===")
        print("KT: '플립7' -> 갤럭시 Z 플립 7 (256GB)")
        print("SK: '플립 7' -> 갤럭시 Z 플립 7 (512GB)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("SK와 KT 플립7 매칭 문제 해결...")
    fix_flip7_for_both()
    print("\n완료!")