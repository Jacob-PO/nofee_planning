"""
summary 시트와 summary_clean 시트의 데이터 차이 분석
"""
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 설정
SPREADSHEET_ID = '1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4'
SERVICE_ACCOUNT_FILE = './src/config/google_api_key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# 인증
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

print("=" * 80)
print("시트 데이터 비교 분석")
print("=" * 80)

# 1. summary 시트 다운로드
print("\n1. summary 시트 다운로드 중...")
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='summary!A:ZZ'
).execute()
summary_values = result.get('values', [])
summary_df = pd.DataFrame(summary_values[1:], columns=summary_values[0])
print(f"   - summary 시트: {len(summary_df)} 행, {len(summary_df.columns)} 칼럼")

# 2. summary_clean 시트 다운로드
print("\n2. summary_clean 시트 다운로드 중...")
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='summary_clean!A:ZZ'
).execute()
summary_clean_values = result.get('values', [])
summary_clean_df = pd.DataFrame(summary_clean_values[1:], columns=summary_clean_values[0])
print(f"   - summary_clean 시트: {len(summary_clean_df)} 행, {len(summary_clean_df.columns)} 칼럼")

# 3. 기본 통계 비교
print("\n" + "=" * 80)
print("기본 통계 비교")
print("=" * 80)
print(f"행 수 차이: {len(summary_clean_df)} - {len(summary_df)} = {len(summary_clean_df) - len(summary_df)} 행")
print(f"칼럼 수: summary ({len(summary_df.columns)}개) vs summary_clean ({len(summary_clean_df.columns)}개)")

# 4. 칼럼 비교
print("\n" + "=" * 80)
print("칼럼 구조 비교")
print("=" * 80)

summary_cols = set(summary_df.columns)
summary_clean_cols = set(summary_clean_df.columns)

print("\n[summary 시트의 칼럼]")
for col in summary_df.columns:
    print(f"  - {col}")

print("\n[summary_clean 시트의 칼럼]")
for col in summary_clean_df.columns:
    print(f"  - {col}")

# 칼럼 차이
added_cols = summary_clean_cols - summary_cols
removed_cols = summary_cols - summary_clean_cols

if added_cols:
    print(f"\n✅ summary_clean에 추가된 칼럼: {added_cols}")
if removed_cols:
    print(f"\n❌ summary_clean에서 제거된 칼럼: {removed_cols}")

# 5. 리베이트 칼럼 확인
print("\n" + "=" * 80)
print("리베이트 관련 칼럼 분석")
print("=" * 80)

if 'rebate' in summary_clean_df.columns:
    # 숫자로 변환
    summary_clean_df['rebate_num'] = pd.to_numeric(summary_clean_df['rebate'], errors='coerce').fillna(0)

    rebate_applied = summary_clean_df[summary_clean_df['rebate_num'] != 0]
    print(f"\n리베이트가 적용된 행: {len(rebate_applied)} 행")
    print(f"리베이트가 적용되지 않은 행: {len(summary_clean_df) - len(rebate_applied)} 행")

    if len(rebate_applied) > 0:
        print(f"\n리베이트 통계:")
        print(f"  - 최소: {rebate_applied['rebate_num'].min():,.0f}원")
        print(f"  - 최대: {rebate_applied['rebate_num'].max():,.0f}원")
        print(f"  - 평균: {rebate_applied['rebate_num'].mean():,.0f}원")
        print(f"  - 총합: {rebate_applied['rebate_num'].sum():,.0f}원")

        # 리베이트 분포
        print(f"\n리베이트 분포:")
        rebate_dist = rebate_applied['rebate_num'].value_counts().sort_index()
        for rebate_value, count in rebate_dist.items():
            print(f"  - {rebate_value:,.0f}원: {count}건")

# 6. 대리점별 분석
print("\n" + "=" * 80)
print("대리점별 데이터 분석")
print("=" * 80)

if 'shop_name' in summary_clean_df.columns:
    shop_counts = summary_clean_df['shop_name'].value_counts()
    print(f"\n대리점별 데이터 개수:")
    for shop, count in shop_counts.items():
        print(f"  - {shop}: {count}건")

# 7. 통신사별 분석
print("\n" + "=" * 80)
print("통신사별 데이터 분석")
print("=" * 80)

if 'carrier' in summary_clean_df.columns:
    carrier_counts = summary_clean_df['carrier'].value_counts()
    print(f"\n통신사별 데이터 개수:")
    for carrier, count in carrier_counts.items():
        print(f"  - {carrier}: {count}건")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
