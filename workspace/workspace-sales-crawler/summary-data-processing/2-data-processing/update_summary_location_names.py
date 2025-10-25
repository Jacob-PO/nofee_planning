"""
summary 워크시트의 모든 지역명_매장명을 현재 지역명 기준으로 업데이트하고
전화번호 중복에 대한 넘버링을 재적용한 후 정렬
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd
import re
import sys

# 실시간 출력을 위한 설정
sys.stdout.reconfigure(line_buffering=True)

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'

# Google Sheets API 인증
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = config_dir / 'google_api_key.json'

print(f"인증 파일 경로: {SERVICE_ACCOUNT_FILE}")

if not SERVICE_ACCOUNT_FILE.exists():
    print(f"❌ 인증 파일을 찾을 수 없습니다: {SERVICE_ACCOUNT_FILE}")
    sys.exit(1)

creds = Credentials.from_service_account_file(
    str(SERVICE_ACCOUNT_FILE), scopes=SCOPES)
client = gspread.authorize(creds)

# 스프레드시트 열기
SPREADSHEET_ID = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
spreadsheet = client.open_by_key(SPREADSHEET_ID)

print("\n스프레드시트 연결 성공")

# summary 워크시트 읽기
summary_sheet = spreadsheet.worksheet('summary')
all_data = summary_sheet.get_all_values()

if not all_data or len(all_data) <= 1:
    print("❌ summary 시트가 비어있습니다.")
    sys.exit(1)

headers = all_data[0]
data_rows = all_data[1:]

print(f"\n총 데이터 행 수: {len(data_rows)}")
print(f"컬럼: {headers}")

# DataFrame 생성
df = pd.DataFrame(data_rows, columns=headers)

location_store_col = '지역명_매장명'
store_name_col = '매장명'
region_col = '지역명'
phone_col = '전화번호'

# 1단계: 지역명_매장명을 현재 지역명 기준으로 재구성
print("\n1단계: 지역명_매장명 업데이트 중...")
updated_count = 0

for idx, row in df.iterrows():
    region = row[region_col]
    store_name = row[store_name_col]
    current_location_store = row[location_store_col]

    # 기존 넘버링 제거 후 새로운 지역명으로 재구성
    new_location_store_base = f"{region}_{store_name}"

    # 현재와 다르면 업데이트
    if not current_location_store.startswith(new_location_store_base):
        df.at[idx, location_store_col] = new_location_store_base
        updated_count += 1

print(f"✓ {updated_count}개의 지역명_매장명 업데이트됨")

# 2단계: 전화번호로 그룹화하여 넘버링 재적용
print("\n2단계: 전화번호 중복 넘버링 적용 중...")
phone_groups = df.groupby(phone_col)

updated_rows = []
duplicate_phone_count = 0

for phone, group in phone_groups:
    if len(group) > 1:
        # 같은 전화번호가 여러 개면 넘버링
        duplicate_phone_count += 1
        for i, (idx, row) in enumerate(group.iterrows(), 1):
            location_store = row[location_store_col]
            # 기존 넘버링 제거
            location_store = re.sub(r'_\d+$', '', location_store)
            # 새 넘버링 추가
            row[location_store_col] = f"{location_store}_{i}"
            updated_rows.append(row.tolist())
    else:
        # 단일 전화번호면 넘버링 제거
        for idx, row in group.iterrows():
            location_store = row[location_store_col]
            # 기존 넘버링 제거
            location_store = re.sub(r'_\d+$', '', location_store)
            row[location_store_col] = location_store
            updated_rows.append(row.tolist())

print(f"✓ {duplicate_phone_count}개의 중복 전화번호에 넘버링 적용됨")

# 3단계: 지역명_매장명으로 정렬
print("\n3단계: 지역명_매장명 기준 정렬 중...")
sorted_df = pd.DataFrame(updated_rows, columns=headers)
sorted_df = sorted_df.sort_values(by=location_store_col)

print("✓ 정렬 완료")

# 4단계: summary 시트 업데이트
print(f"\n4단계: summary 시트 업데이트 중...")
summary_sheet.clear()
summary_sheet.update(values=[headers] + sorted_df.values.tolist(), range_name='A1')

print("✓ summary 시트 업데이트 완료!")

print(f"\n전체 작업 완료!")
print(f"- 총 행 수: {len(sorted_df)}")
print(f"- 지역명_매장명 업데이트: {updated_count}개")
print(f"- 중복 전화번호: {duplicate_phone_count}개")
