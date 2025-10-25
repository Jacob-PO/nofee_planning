"""플립7 관련 storage 확인 및 수정"""

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

def check_and_fix_flip7_storage():
    """플립7 관련 storage 확인 및 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # 현재 매핑 상태 확인
        print("=== 1. 현재 product_group_nm 매핑 상태 ===")
        pg_df = pd.DataFrame(sheet.worksheet("product_group_nm").get_all_records())
        
        flip7_mappings = pg_df[pg_df['device_nm'].str.contains('플립.*7|플립7', case=False, na=False)]
        print(f"\n플립7 관련 매핑 {len(flip7_mappings)}개:")
        for _, row in flip7_mappings.iterrows():
            print(f"  '{row['device_nm']}' -> {row['product_group_nm']} ({row['storage']})")
        
        # Support 데이터 확인
        print("\n=== 2. Support 시트 데이터 확인 ===")
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # KT 플립 7 확인
        kt_flip7 = support_df[(support_df['carrier'] == 'KT') & (support_df['device_nm'] == '플립 7')]
        print(f"\nKT '플립 7' Support 데이터:")
        if len(kt_flip7) > 0:
            storages = kt_flip7['storage'].value_counts()
            for storage, count in storages.items():
                print(f"  {storage}: {count}개")
        
        # SK 플립7 확인
        sk_flip7 = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'].str.contains('플립.*7', case=False, na=False))]
        print(f"\nSK 플립7 Support 데이터:")
        if len(sk_flip7) > 0:
            device_storages = sk_flip7.groupby(['device_nm', 'storage']).size()
            for (device, storage), count in device_storages.items():
                print(f"  '{device}' - {storage}: {count}개")
        
        # 수정 제안
        print("\n=== 3. 수정 제안 ===")
        worksheet = sheet.worksheet("product_group_nm")
        all_values = worksheet.get_all_values()
        
        updates_needed = []
        
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
                
            device_nm = row[0]
            product_group_nm = row[1]
            current_storage = row[2]
            
            # KT 플립7 (띄어쓰기 없음) -> 256GB 확인
            if device_nm == "플립7" and current_storage != "256GB":
                updates_needed.append((i+1, device_nm, "256GB", f"현재: {current_storage}"))
                
            # SK 플립 7 (띄어쓰기 있음) -> 512GB 확인
            elif device_nm == "플립 7" and product_group_nm == "갤럭시 Z 플립 7" and current_storage != "512GB":
                updates_needed.append((i+1, device_nm, "512GB", f"현재: {current_storage}"))
        
        if updates_needed:
            print("\n필요한 수정:")
            for row_num, device, new_storage, note in updates_needed:
                print(f"  행 {row_num}: '{device}' -> {new_storage} ({note})")
                
            # 수정 실행
            response = input("\n수정을 진행하시겠습니까? (y/n): ")
            if response.lower() == 'y':
                for row_num, device, new_storage, _ in updates_needed:
                    worksheet.update(f'C{row_num}', [[new_storage]])
                    print(f"✅ 행 {row_num} 수정 완료")
        else:
            print("\n수정이 필요한 항목이 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_and_fix_flip7_storage()