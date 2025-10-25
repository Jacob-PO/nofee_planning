"""
Support 시트의 폴드7/플립7 데이터 확인
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from pathlib import Path

# Google Sheets 설정
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"
CREDENTIALS_DIR = "/Users/jacob_athometrip/Desktop/dev/nofee/workspace_nofee/config"

# Google Sheets 연결
credentials_path = Path(CREDENTIALS_DIR) / 'google_api_key.json'
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(str(credentials_path), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)

# Support 시트 데이터 가져오기
support_worksheet = sheet.worksheet("support")
all_values = support_worksheet.get_all_values()

if len(all_values) > 1:
    headers = all_values[0]
    data = all_values[1:]
    support_data = [dict(zip(headers, row)) for row in data]
    support_df = pd.DataFrame(support_data)
else:
    support_df = pd.DataFrame()

print("=== Support 시트 전체 데이터 ===")
print(f"총 {len(support_df)}개 행")
print("\n컬럼 목록:")
for i, col in enumerate(support_df.columns):
    print(f"{i+1}. {col}")

# 폴드7/플립7 관련 검색
search_terms = ["폴드7", "플립7", "폴드 7", "플립 7", "fold7", "flip7", "fold 7", "flip 7"]

print("\n=== 폴드7/플립7 관련 데이터 검색 ===")
all_matches = []

for term in search_terms:
    # device_nm 컬럼에서 검색
    device_matches = support_df[support_df['device_nm'].str.contains(term, na=False, case=False)]
    
    # 다른 컬럼들에서도 검색 (product_group_nm, manufacturer 등)
    for col in support_df.columns:
        if col != 'device_nm':
            col_matches = support_df[support_df[col].str.contains(term, na=False, case=False)]
            device_matches = pd.concat([device_matches, col_matches]).drop_duplicates()
    
    if len(device_matches) > 0:
        print(f"\n'{term}' 검색 결과: {len(device_matches)}개")
        all_matches.append(device_matches)

if all_matches:
    combined_matches = pd.concat(all_matches).drop_duplicates()
    print(f"\n총 {len(combined_matches)}개 고유 매칭 발견")
    
    for idx, row in combined_matches.iterrows():
        print(f"\n{idx+1}. {row['device_nm']} ({row.get('carrier', 'N/A')})")
        print(f"   - 제조사: {row.get('manufacturer', 'N/A')}")
        print(f"   - 요금제: {row.get('rate_plan', 'N/A')}")
        print(f"   - 월요금: {row.get('rate_plan_month_fee', 'N/A')}")
        print(f"   - 출고가: {row.get('release_price', 'N/A')}")
        print(f"   - 총지원금: {row.get('total_support_fee', 'N/A')}")
        print(f"   - 지원유형: {row.get('support_type', 'N/A')}")
        print(f"   - 저장용량: {row.get('storage', 'N/A')}")
else:
    print("폴드7/플립7 관련 데이터를 찾을 수 없습니다.")

# 샘플 데이터 확인 (처음 5개 행)
print("\n=== 샘플 데이터 (처음 5개 행) ===")
for idx in range(min(5, len(support_df))):
    row = support_df.iloc[idx]
    print(f"\n{idx+1}. {row['device_nm']} ({row.get('carrier', 'N/A')})")
    print(f"   - 제조사: {row.get('manufacturer', 'N/A')}")
    print(f"   - 요금제: {row.get('rate_plan', 'N/A')}")
    print(f"   - 월요금: {row.get('rate_plan_month_fee', 'N/A')}")
    print(f"   - 출고가: {row.get('release_price', 'N/A')}")
    print(f"   - 총지원금: {row.get('total_support_fee', 'N/A')}")
    print(f"   - 지원유형: {row.get('support_type', 'N/A')}")
    print(f"   - 저장용량: {row.get('storage', 'N/A')}")