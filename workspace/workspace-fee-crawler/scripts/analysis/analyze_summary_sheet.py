"""
summary 시트의 현재 데이터 분석
(create_summary_clean.py 실행 후 상태)
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
print("summary 시트 데이터 분석 (create_summary_clean.py 실행 후)")
print("=" * 80)

# summary 시트 다운로드
print("\nsummary 시트 다운로드 중...")
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='summary!A:ZZ'
).execute()
values = result.get('values', [])
df = pd.DataFrame(values[1:], columns=values[0])

print(f"\n✅ 총 데이터: {len(df)} 행, {len(df.columns)} 칼럼")

# 칼럼 구조
print("\n" + "=" * 80)
print("칼럼 구조")
print("=" * 80)
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

# 리베이트 분석
print("\n" + "=" * 80)
print("리베이트 분석")
print("=" * 80)

if 'rebate' in df.columns:
    df['rebate_num'] = pd.to_numeric(df['rebate'], errors='coerce').fillna(0)

    rebate_applied = df[df['rebate_num'] != 0]
    rebate_not_applied = df[df['rebate_num'] == 0]

    print(f"\n✅ 리베이트 적용된 행: {len(rebate_applied):,} 행 ({len(rebate_applied)/len(df)*100:.1f}%)")
    print(f"❌ 리베이트 미적용 행: {len(rebate_not_applied):,} 행 ({len(rebate_not_applied)/len(df)*100:.1f}%)")

    if len(rebate_applied) > 0:
        print(f"\n리베이트 통계:")
        print(f"  • 최소: {rebate_applied['rebate_num'].min():,.0f}원")
        print(f"  • 최대: {rebate_applied['rebate_num'].max():,.0f}원")
        print(f"  • 평균: {rebate_applied['rebate_num'].mean():,.0f}원")
        print(f"  • 총액: {rebate_applied['rebate_num'].sum():,.0f}원")

        print(f"\n리베이트 값 분포:")
        rebate_dist = rebate_applied['rebate_num'].value_counts().sort_index()
        for rebate_value, count in rebate_dist.head(20).items():
            print(f"  • {rebate_value:>10,.0f}원: {count:>5,}건")
else:
    print("\n⚠️  'rebate' 칼럼이 없습니다.")

# 대리점별 분석
print("\n" + "=" * 80)
print("대리점별 데이터 분포")
print("=" * 80)

if 'shop_name' in df.columns:
    shop_counts = df['shop_name'].value_counts()
    print(f"\n총 대리점 수: {len(shop_counts)}개\n")
    for shop, count in shop_counts.head(15).items():
        print(f"  • {shop}: {count:,}건")
    if len(shop_counts) > 15:
        print(f"  ... 외 {len(shop_counts) - 15}개 대리점")
else:
    print("\n⚠️  'shop_name' 칼럼이 없습니다.")

# 통신사별 분석
print("\n" + "=" * 80)
print("통신사별 데이터 분포")
print("=" * 80)

if 'carrier' in df.columns:
    carrier_counts = df['carrier'].value_counts()
    print()
    for carrier, count in carrier_counts.items():
        print(f"  • {carrier}: {count:,}건 ({count/len(df)*100:.1f}%)")
else:
    print("\n⚠️  'carrier' 칼럼이 없습니다.")

# 가입유형별 분석
print("\n" + "=" * 80)
print("가입유형별 데이터 분포")
print("=" * 80)

if 'scrb_type_name' in df.columns:
    scrb_counts = df['scrb_type_name'].value_counts()
    print()
    for scrb_type, count in scrb_counts.items():
        print(f"  • {scrb_type}: {count:,}건 ({count/len(df)*100:.1f}%)")
else:
    print("\n⚠️  'scrb_type_name' 칼럼이 없습니다.")

# 요금제별 분석
print("\n" + "=" * 80)
print("요금제 월요금대별 데이터 분포")
print("=" * 80)

if 'rate_plan_month_fee' in df.columns:
    df['rate_plan_month_fee_num'] = pd.to_numeric(df['rate_plan_month_fee'], errors='coerce').fillna(0)
    fee_counts = df['rate_plan_month_fee_num'].value_counts().sort_index()
    print()
    for fee, count in fee_counts.head(20).items():
        print(f"  • {fee:>10,.0f}원: {count:>5,}건")
    if len(fee_counts) > 20:
        print(f"  ... 외 {len(fee_counts) - 20}개 요금제")
else:
    print("\n⚠️  'rate_plan_month_fee' 칼럼이 없습니다.")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
