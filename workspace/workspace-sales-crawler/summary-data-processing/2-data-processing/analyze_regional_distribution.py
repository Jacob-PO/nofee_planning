"""
summary 워크시트의 지역 분포 분석
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd
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
    print(f"인증 파일을 찾을 수 없습니다: {SERVICE_ACCOUNT_FILE}")
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
    print("summary 시트가 비어있습니다.")
    sys.exit(1)

headers = all_data[0]
data_rows = all_data[1:]

print(f"\n총 데이터 행 수: {len(data_rows)}")

# DataFrame 생성
df = pd.DataFrame(data_rows, columns=headers)

region_col = '지역명'

# 지역별 카운트
region_counts = df[region_col].value_counts()

print("\n" + "=" * 60)
print("지역별 매장 분포")
print("=" * 60)

# 광역시/특별시와 도 지역 분리
metro_regions = []
province_regions = []

for region, count in region_counts.items():
    percentage = (count / len(df)) * 100
    
    # 광역시/특별시 (서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종)
    if any(metro in region for metro in ['서울', '부산', '대구', '인천', '광주', '대전', '울산']) or region == '세종':
        metro_regions.append((region, count, percentage))
    else:
        province_regions.append((region, count, percentage))

# 광역시/특별시 출력
print("\n[광역시/특별시/세종]")
metro_regions.sort(key=lambda x: x[1], reverse=True)
for region, count, percentage in metro_regions:
    print(f"  {region:20s}: {count:4d}개 ({percentage:5.2f}%)")

metro_total = sum(count for _, count, _ in metro_regions)
metro_percentage = (metro_total / len(df)) * 100
print(f"\n  소계: {metro_total}개 ({metro_percentage:.2f}%)")

# 도 지역 출력
print("\n[도 지역]")
province_regions.sort(key=lambda x: x[1], reverse=True)
for region, count, percentage in province_regions:
    print(f"  {region:20s}: {count:4d}개 ({percentage:5.2f}%)")

province_total = sum(count for _, count, _ in province_regions)
province_percentage = (province_total / len(df)) * 100
print(f"\n  소계: {province_total}개 ({province_percentage:.2f}%)")

# 상위 10개 지역
print("\n" + "=" * 60)
print("매장 수 상위 10개 지역")
print("=" * 60)
for i, (region, count) in enumerate(region_counts.head(10).items(), 1):
    percentage = (count / len(df)) * 100
    print(f"{i:2d}. {region:20s}: {count:4d}개 ({percentage:5.2f}%)")

# 하위 10개 지역
print("\n" + "=" * 60)
print("매장 수 하위 10개 지역")
print("=" * 60)
for i, (region, count) in enumerate(region_counts.tail(10).items(), 1):
    percentage = (count / len(df)) * 100
    print(f"{i:2d}. {region:20s}: {count:4d}개 ({percentage:5.2f}%)")

# 통계 요약
print("\n" + "=" * 60)
print("통계 요약")
print("=" * 60)
print(f"총 매장 수: {len(df)}개")
print(f"총 지역 수: {len(region_counts)}개")
print(f"평균 매장 수/지역: {len(df) / len(region_counts):.1f}개")
print(f"중앙값 매장 수/지역: {region_counts.median():.0f}개")
print(f"최대 매장 수: {region_counts.max()}개 ({region_counts.idxmax()})")
print(f"최소 매장 수: {region_counts.min()}개 ({region_counts.idxmin()})")

# 분포 균형 분석
std_dev = region_counts.std()
mean = region_counts.mean()
cv = (std_dev / mean) * 100  # 변동계수 (Coefficient of Variation)

print("\n" + "=" * 60)
print("분포 균형 분석")
print("=" * 60)
print(f"표준편차: {std_dev:.2f}")
print(f"변동계수: {cv:.2f}%")

if cv < 50:
    balance_status = "매우 균등"
elif cv < 100:
    balance_status = "비교적 균등"
elif cv < 150:
    balance_status = "불균등"
else:
    balance_status = "매우 불균등"

print(f"분포 균형도: {balance_status}")

# 지역 그룹별 분석
print("\n" + "=" * 60)
print("지역 대분류별 분포")
print("=" * 60)

# 대분류 매핑
def classify_major_region(region):
    if '서울' in region:
        return '서울'
    elif '부산' in region:
        return '부산'
    elif '대구' in region:
        return '대구'
    elif '인천' in region:
        return '인천'
    elif '광주' in region:
        return '광주'
    elif '대전' in region:
        return '대전'
    elif '울산' in region:
        return '울산'
    elif region == '세종':
        return '세종'
    elif '경기' in region:
        return '경기'
    elif '강원' in region:
        return '강원'
    elif '충북' in region:
        return '충북'
    elif '충남' in region:
        return '충남'
    elif '전북' in region:
        return '전북'
    elif '전남' in region:
        return '전남'
    elif '경북' in region:
        return '경북'
    elif '경남' in region:
        return '경남'
    elif '제주' in region:
        return '제주'
    else:
        return '기타'

df['대분류'] = df[region_col].apply(classify_major_region)
major_region_counts = df['대분류'].value_counts()

for major_region, count in major_region_counts.items():
    percentage = (count / len(df)) * 100
    print(f"{major_region:10s}: {count:4d}개 ({percentage:5.2f}%)")

print("\n분석 완료!")
