"""
invalid_regions 워크시트의 데이터를 개선:
1. 링크에서 주소를 크롤링
2. 주소에서 올바른 지역명 추출
3. 지역명_매장명 업데이트
4. invalid_regions 시트 업데이트
5. 성공한 데이터는 summary 시트로 이동
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd
import re
import sys
import requests
from bs4 import BeautifulSoup
import time

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

# 주소에서 지역명 추출 함수
def extract_region_from_address(address):
    """주소에서 '시/도 + 시/군/구' 형태의 지역명 추출"""
    if not address:
        return None

    patterns = [
        # 서울특별시
        (r'서울특별시\s+([가-힣]+구)', '서울'),
        (r'서울\s+([가-힣]+구)', '서울'),
        # 부산광역시
        (r'부산광역시\s+([가-힣]+구|[가-힣]+군)', '부산'),
        (r'부산\s+([가-힣]+구|[가-힣]+군)', '부산'),
        # 대구광역시
        (r'대구광역시\s+([가-힣]+구|[가-힣]+군)', '대구'),
        (r'대구\s+([가-힣]+구|[가-힣]+군)', '대구'),
        # 인천광역시
        (r'인천광역시\s+([가-힣]+구|[가-힣]+군)', '인천'),
        (r'인천\s+([가-힣]+구|[가-힣]+군)', '인천'),
        # 광주광역시
        (r'광주광역시\s+([가-힣]+구)', '광주'),
        (r'광주\s+([가-힣]+구)', '광주'),
        # 대전광역시
        (r'대전광역시\s+([가-힣]+구)', '대전'),
        (r'대전\s+([가-힣]+구)', '대전'),
        # 울산광역시
        (r'울산광역시\s+([가-힣]+구|[가-힣]+군)', '울산'),
        (r'울산\s+([가-힣]+구|[가-힣]+군)', '울산'),
        # 세종특별자치시
        (r'세종특별자치시', '세종'),
        (r'세종시', '세종'),
        # 경기도
        (r'경기도\s+([가-힣]+시)', '경기'),
        (r'경기\s+([가-힣]+시)', '경기'),
        # 강원도
        (r'강원[특별자치]*도\s+([가-힣]+시|[가-힣]+군)', '강원'),
        (r'강원[특별자치]*\s+([가-힣]+시|[가-힣]+군)', '강원'),
        # 충청북도
        (r'충청북도\s+([가-힣]+시|[가-힣]+군)', '충북'),
        (r'충북\s+([가-힣]+시|[가-힣]+군)', '충북'),
        # 충청남도
        (r'충청남도\s+([가-힣]+시|[가-힣]+군)', '충남'),
        (r'충남\s+([가-힣]+시|[가-힣]+군)', '충남'),
        # 전북특별자치도
        (r'전북특별자치도\s+([가-힣]+시|[가-힣]+군)', '전북'),
        (r'전라북도\s+([가-힣]+시|[가-힣]+군)', '전북'),
        (r'전북\s+([가-힣]+시|[가-힣]+군)', '전북'),
        # 전라남도
        (r'전라남도\s+([가-힣]+시|[가-힣]+군)', '전남'),
        (r'전남\s+([가-힣]+시|[가-힣]+군)', '전남'),
        # 경상북도
        (r'경상북도\s+([가-힣]+시|[가-힣]+군)', '경북'),
        (r'경북\s+([가-힣]+시|[가-힣]+군)', '경북'),
        # 경상남도
        (r'경상남도\s+([가-힣]+시|[가-힣]+군)', '경남'),
        (r'경남\s+([가-힣]+시|[가-힣]+군)', '경남'),
        # 제주특별자치도
        (r'제주특별자치도\s+([가-힣]+시)', '제주'),
        (r'제주도\s+([가-힣]+시)', '제주'),
        (r'제주\s+([가-힣]+시)', '제주'),
    ]

    for pattern, province in patterns:
        match = re.search(pattern, address)
        if match:
            if province == '세종':
                return '세종'
            else:
                district = match.group(1)
                return f"{province} {district}"

    return None

# 당근마켓 링크에서 주소 추출
def extract_address_from_daangn(url):
    """당근마켓 URL에서 주소 정보 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # 패턴 1: main > div[1] > article > section > section > div > ul > li[N] > div > span > button > span
        # li 인덱스가 다를 수 있으므로 모든 li 요소를 순회
        main = soup.find('main')
        if main:
            divs = main.find_all('div', recursive=False)
            if len(divs) >= 1:
                article = divs[0].find('article')
                if article:
                    sections = article.find_all('section', recursive=False)
                    if len(sections) >= 1:
                        section = sections[0]
                        inner_sections = section.find_all('section', recursive=False)

                        # 모든 inner section 순회
                        for inner_section in inner_sections:
                            div = inner_section.find('div')
                            if div:
                                ul = div.find('ul')
                                if ul:
                                    li_elements = ul.find_all('li', recursive=False)
                                    # 모든 li 요소를 순회하면서 주소 찾기
                                    for li in li_elements:
                                        div_inner = li.find('div')
                                        if div_inner:
                                            span_outer = div_inner.find('span')
                                            if span_outer:
                                                button = span_outer.find('button')
                                                if button:
                                                    span = button.find('span')
                                                    if span:
                                                        text = span.get_text(strip=True)
                                                        # 주소처럼 보이는지 확인 (시/도/군/구 포함)
                                                        if text and any(keyword in text for keyword in ['시', '도', '군', '구', '동', '읍', '면']):
                                                            return text

        # 패턴 2 (기존): main > article > aside > section > ul > li[4] > button > span
        main = soup.find('main')
        if main:
            article = main.find('article')
            if article:
                aside = article.find('aside')
                if aside:
                    section = aside.find('section')
                    if section:
                        ul = section.find('ul')
                        if ul:
                            li_elements = ul.find_all('li', recursive=False)
                            if len(li_elements) >= 4:
                                fourth_li = li_elements[3]
                                button = fourth_li.find('button')
                                if button:
                                    span = button.find('span')
                                    if span:
                                        address = span.get_text(strip=True)
                                        return address

        return None

    except Exception as e:
        print(f"  ⚠ 주소 추출 실패: {e}")
        return None

# invalid_regions 워크시트 읽기
print("\ninvalid_regions 워크시트 데이터 읽는 중...")
invalid_sheet = spreadsheet.worksheet('invalid_regions')
all_data = invalid_sheet.get_all_values()

if not all_data or len(all_data) <= 1:
    print("❌ invalid_regions 시트가 비어있습니다.")
    sys.exit(1)

headers = all_data[0]
data_rows = all_data[1:]

print(f"총 데이터 행 수: {len(data_rows)}")

# DataFrame 생성
df = pd.DataFrame(data_rows, columns=headers)

# 결과 저장용 리스트
fixed_rows = []  # 수정 성공한 행들
still_invalid_rows = []  # 여전히 수정 실패한 행들

location_store_col = '지역명_매장명'
store_name_col = '매장명'
region_col = '지역명'
phone_col = '전화번호'
link_col = '링크'

print(f"\n총 {len(data_rows)}개 데이터의 주소를 크롤링합니다...")
print("=" * 50)

success_count = 0
fail_count = 0

for idx, row in df.iterrows():
    link = row[link_col]
    store_name = row[store_name_col]
    old_region = row[region_col]
    phone = row[phone_col]

    print(f"\n[{idx+1}/{len(data_rows)}] 매장: {store_name}")
    print(f"  기존 지역명: {old_region}")
    print(f"  링크: {link}")

    if not link or not link.startswith('http'):
        print(f"  ❌ 유효하지 않은 링크")
        still_invalid_rows.append(row.tolist())
        fail_count += 1
        continue

    # 주소 크롤링
    address = extract_address_from_daangn(link)

    if not address:
        print(f"  ❌ 주소를 찾을 수 없습니다")
        still_invalid_rows.append(row.tolist())
        fail_count += 1
        time.sleep(0.5)
        continue

    print(f"  추출된 주소: {address}")

    # 지역명 추출
    new_region = extract_region_from_address(address)

    if not new_region:
        print(f"  ❌ 주소에서 지역명을 추출할 수 없습니다")
        still_invalid_rows.append(row.tolist())
        fail_count += 1
        time.sleep(0.5)
        continue

    print(f"  ✓ 새 지역명: {new_region}")

    # 데이터 업데이트
    row[region_col] = new_region
    row[location_store_col] = f"{new_region}_{store_name}"

    fixed_rows.append(row.tolist())
    success_count += 1

    time.sleep(0.5)  # 서버 부하 방지

print("\n" + "=" * 50)
print(f"\n크롤링 완료!")
print(f"✓ 성공: {success_count}개")
print(f"❌ 실패: {fail_count}개")

# invalid_regions 시트 업데이트 (실패한 것만 남김)
if still_invalid_rows:
    print(f"\ninvalid_regions 워크시트를 {len(still_invalid_rows)}개 행으로 업데이트 중...")
    invalid_sheet.clear()
    invalid_sheet.update(values=[headers] + still_invalid_rows, range_name='A1')
    print("업데이트 완료!")
else:
    print("\n모든 데이터가 수정되었습니다. invalid_regions 시트를 비웁니다.")
    invalid_sheet.clear()
    invalid_sheet.update(values=[headers], range_name='A1')

# 수정된 데이터를 summary 시트에 추가
if fixed_rows:
    print(f"\n수정된 {len(fixed_rows)}개 데이터를 summary 시트 최하단에 추가 중...")

    summary_sheet = spreadsheet.worksheet('summary')
    existing_data = summary_sheet.get_all_values()

    # 수정된 데이터를 기존 데이터 최하단에 추가
    next_row = len(existing_data) + 1
    summary_sheet.append_rows(fixed_rows)

    print(f"추가 완료! (행 {next_row}부터)")

    # 전체 데이터를 다시 읽어서 지역명_매장명 업데이트 및 재정렬
    print("\n전체 summary 시트의 지역명_매장명 업데이트 및 재정렬 중...")
    all_data = summary_sheet.get_all_values()
    headers = all_data[0]
    data_rows = all_data[1:]

    summary_df = pd.DataFrame(data_rows, columns=headers)

    # 전화번호로 그룹화하여 넘버링
    phone_groups = summary_df.groupby(phone_col)

    updated_rows = []
    for phone, group in phone_groups:
        if len(group) > 1:
            # 같은 전화번호가 여러 개면 넘버링
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
                location_store = re.sub(r'_\d+$', '', location_store)
                row[location_store_col] = location_store
                updated_rows.append(row.tolist())

    # 지역명_매장명으로 정렬
    sorted_df = pd.DataFrame(updated_rows, columns=headers)
    sorted_df = sorted_df.sort_values(by=location_store_col)

    # summary 시트 전체 업데이트
    summary_sheet.clear()
    summary_sheet.update(values=[headers] + sorted_df.values.tolist(), range_name='A1')

    print("summary 시트 업데이트 완료!")

    final_count = len(sorted_df)
else:
    final_count = 0

print("\n전체 작업 완료!")
if fixed_rows:
    print(f"- summary 시트: {final_count}개 행")
else:
    summary_sheet = spreadsheet.worksheet('summary')
    existing_data = summary_sheet.get_all_values()
    print(f"- summary 시트: {len(existing_data) - 1}개 행 (변경 없음)")
print(f"- invalid_regions 시트: {len(still_invalid_rows)}개 행")
