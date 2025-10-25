"""
summary 워크시트에서 지역명이 잘못된 데이터를 찾아서:
1. invalid_regions 워크시트에 복사
2. summary 워크시트에서 삭제

지역명 유효성 검증 규칙:
- 광역시/특별시: 서울, 부산, 대구, 인천, 광주, 대전, 울산 + 구
- 세종: 세종
- 도 지역: 경기, 강원, 충북, 충남, 전북, 전남, 경북, 경남, 제주 + 시/군
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

if not all_data:
    print("❌ summary 시트가 비어있습니다.")
    sys.exit(1)

headers = all_data[0]
data_rows = all_data[1:]

print(f"\n총 데이터 행 수: {len(data_rows)}")
print(f"컬럼: {headers}")

# DataFrame 생성
df = pd.DataFrame(data_rows, columns=headers)

# 지역명 유효성 검증 함수
def is_valid_region(region):
    if not region or not isinstance(region, str):
        return False

    region = region.strip()

    # 유효한 지역명 패턴들
    valid_patterns = [
        r'^(서울|부산|대구|인천|광주|대전|울산)\s+[가-힣]+구$',  # 광역시/특별시 + 구
        r'^세종$',  # 세종특별자치시
        r'^(경기|강원|충북|충남|전북|전남|경북|경남|제주)\s+[가-힣]+시$',  # 도 + 시
        r'^(경기|강원|충북|충남|전북|전남|경북|경남)\s+[가-힣]+군$',  # 도 + 군
    ]

    for pattern in valid_patterns:
        if re.match(pattern, region):
            return True

    return False

# 유효한 행과 무효한 행 분리
region_col = '지역명'
valid_rows = []
invalid_rows = []

for idx, row in df.iterrows():
    region = row[region_col]
    if is_valid_region(region):
        valid_rows.append(row.tolist())
    else:
        invalid_rows.append(row.tolist())

print(f"\n유효한 지역명: {len(valid_rows)}개")
print(f"무효한 지역명: {len(invalid_rows)}개")

if len(invalid_rows) == 0:
    print("\n무효한 지역명이 없습니다. 작업을 종료합니다.")
    sys.exit(0)

# invalid_regions 워크시트 생성 또는 기존 시트 사용
try:
    invalid_sheet = spreadsheet.worksheet('invalid_regions')
    print("\n기존 invalid_regions 워크시트를 덮어씁니다.")
except gspread.exceptions.WorksheetNotFound:
    invalid_sheet = spreadsheet.add_worksheet(title='invalid_regions', rows=1000, cols=20)
    print("\ninvalid_regions 워크시트를 생성했습니다.")

# invalid_regions 시트에 데이터 쓰기
print(f"\n무효한 지역명 데이터 {len(invalid_rows)}개를 invalid_regions 워크시트에 복사 중...")
invalid_sheet.clear()
invalid_sheet.update('A1', [headers] + invalid_rows)
print(f"복사 완료!")

# summary 시트에서 유효한 데이터만 남기기
print(f"\nsummary 워크시트를 유효한 데이터 {len(valid_rows)}개로 업데이트 중...")
summary_sheet.clear()
summary_sheet.update('A1', [headers] + valid_rows)
print(f"업데이트 완료!")

print(f"\n작업 완료!")
print(f"- summary 시트: {len(valid_rows)}개 행 (유효한 데이터만)")
print(f"- invalid_regions 시트: {len(invalid_rows)}개 행 (무효한 데이터)")
