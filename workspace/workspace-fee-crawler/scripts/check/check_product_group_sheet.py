"""
Check product_group_nm sheet in Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd

# Google Sheets 설정
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"
CREDENTIALS_DIR = "/Users/jacob_athometrip/Desktop/dev/nofee/workspace_nofee/config"

# Google Sheets 연결 설정
possible_paths = [
    Path(CREDENTIALS_DIR) / 'google_api_key.json',
    Path(CREDENTIALS_DIR) / 'google-sheets-key.json',
    Path(CREDENTIALS_DIR) / 'service_account_key.json',
]

# 존재하는 첫 번째 파일 사용
credentials_path = None
for path in possible_paths:
    if path.exists():
        credentials_path = str(path)
        print(f"사용할 credentials 파일: {credentials_path}")
        break

if not credentials_path:
    raise FileNotFoundError(f"Google Sheets credentials 파일을 찾을 수 없습니다.")

# Google Sheets 연결
scope = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)

# product_group_nm 시트 데이터 가져오기
print("\n=== product_group_nm 시트 정보 ===")
worksheet = sheet.worksheet("product_group_nm")
all_data = worksheet.get_all_values()

print(f"\n1. 시트 위치:")
print(f"   - Spreadsheet ID: {SPREADSHEET_ID}")
print(f"   - Sheet name: product_group_nm")
print(f"   - URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")

print(f"\n2. 데이터 구조:")
if len(all_data) > 0:
    headers = all_data[0]
    print(f"   - 컬럼명: {headers}")
    print(f"   - 총 행 수: {len(all_data)} (헤더 포함)")
    print(f"   - 데이터 행 수: {len(all_data) - 1}")
else:
    print("   - 시트가 비어있습니다.")

# 데이터를 DataFrame으로 변환
if len(all_data) > 1:
    df = pd.DataFrame(all_data[1:], columns=all_data[0])
    
    print(f"\n3. 아이폰 관련 데이터 예시 (최대 20개):")
    iphone_data = df[df['product_group_nm'].str.contains('아이폰', na=False)]
    
    if len(iphone_data) > 0:
        for idx, row in iphone_data.head(20).iterrows():
            print(f"   - device_nm: {row['device_nm']}")
            print(f"     product_group_nm: {row['product_group_nm']}")
            print(f"     storage: {row['storage']}")
            print()
    else:
        print("   아이폰 관련 데이터가 없습니다.")
    
    # 통계 정보
    print(f"\n4. 통계 정보:")
    print(f"   - 전체 기기 수: {len(df)}")
    print(f"   - 아이폰 기기 수: {len(iphone_data)}")
    
    # product_group_nm 별 통계
    print(f"\n   - product_group_nm 별 기기 수:")
    group_counts = df['product_group_nm'].value_counts()
    for group, count in group_counts.head(10).items():
        print(f"     {group}: {count}개")

print(f"\n5. 데이터 추가 방법:")
print("   - worksheet.append_row([device_nm, product_group_nm, storage])")
print("   - 예: worksheet.append_row(['IP16PM_256GB', '아이폰 16 프로 맥스', '256GB'])")