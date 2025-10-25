"""
Get unique mappings for Galaxy Fold and Flip 7 devices
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd

# Google Sheets 설정
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"
CREDENTIALS_DIR = "/Users/jacob_athometrip/Desktop/dev/nofee/workspace_nofee/config"

# 검색할 기기명들
SEARCH_TERMS = ["폴드7", "플립7", "폴드 7", "플립 7"]

# Google Sheets 연결
credentials_path = Path(CREDENTIALS_DIR) / 'google_api_key.json'
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(str(credentials_path), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)

# product_group_nm 시트 데이터 가져오기
worksheet = sheet.worksheet("product_group_nm")
all_data = worksheet.get_all_values()
df = pd.DataFrame(all_data[1:], columns=all_data[0])

print("=== Galaxy Fold/Flip 7 기기 고유 매핑 ===")

# 모든 검색어로 찾은 기기들을 수집
all_found = []
for search_term in SEARCH_TERMS:
    device_matches = df[df['device_nm'].str.contains(search_term, na=False, case=False)]
    product_matches = df[df['product_group_nm'].str.contains(search_term, na=False, case=False)]
    matches = pd.concat([device_matches, product_matches]).drop_duplicates()
    
    for idx, row in matches.iterrows():
        all_found.append({
            'device_nm': row['device_nm'],
            'product_group_nm': row['product_group_nm'],
            'storage': row.get('storage', 'N/A')
        })

# 중복 제거 (device_nm 기준)
unique_mappings = {}
for item in all_found:
    key = item['device_nm']
    if key not in unique_mappings:
        unique_mappings[key] = item

# 결과 출력
print(f"총 {len(unique_mappings)}개의 고유 기기 매핑:")
print("\n갤럭시 Z 폴드 7 관련:")
fold_count = 0
for device_nm, mapping in unique_mappings.items():
    if '폴드' in mapping['product_group_nm']:
        fold_count += 1
        print(f"  {fold_count}. {device_nm} → {mapping['product_group_nm']} ({mapping['storage']})")

print("\n갤럭시 Z 플립 7 관련:")
flip_count = 0
for device_nm, mapping in unique_mappings.items():
    if '플립' in mapping['product_group_nm']:
        flip_count += 1
        print(f"  {flip_count}. {device_nm} → {mapping['product_group_nm']} ({mapping['storage']})")

print(f"\n요약:")
print(f"- 폴드 7 기기: {fold_count}개")
print(f"- 플립 7 기기: {flip_count}개")
print(f"- 총합: {len(unique_mappings)}개")