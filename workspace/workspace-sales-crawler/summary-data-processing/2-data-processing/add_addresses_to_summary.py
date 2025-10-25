"""
summary 워크시트의 모든 매장에 대해 주소 정보를 크롤링하여
전화번호 칼럼 오른쪽에 '주소' 칼럼을 추가
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd
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
        return None

# summary 워크시트 읽기
print("\nsummary 워크시트 데이터 읽는 중...")
summary_sheet = spreadsheet.worksheet('summary')
all_data = summary_sheet.get_all_values()

if not all_data or len(all_data) <= 1:
    print("❌ summary 시트가 비어있습니다.")
    sys.exit(1)

headers = all_data[0]
data_rows = all_data[1:]

print(f"총 데이터 행 수: {len(data_rows)}")
print(f"기존 컬럼: {headers}")

# DataFrame 생성
df = pd.DataFrame(data_rows, columns=headers)

# 새로운 컬럼 추가
if '주소' not in df.columns:
    df['주소'] = ''

link_col = '링크'

print(f"\n총 {len(data_rows)}개 매장의 주소를 크롤링합니다...")
print("=" * 50)

success_count = 0
fail_count = 0

for idx, row in df.iterrows():
    link = row[link_col]
    store_name = row['매장명']

    print(f"\n[{idx+1}/{len(data_rows)}] 매장: {store_name}")

    if not link or not link.startswith('http'):
        print(f"  ❌ 유효하지 않은 링크")
        df.at[idx, '주소'] = ''
        fail_count += 1
        continue

    # 주소 크롤링
    address = extract_address_from_daangn(link)

    if not address:
        print(f"  ❌ 주소를 찾을 수 없습니다")
        df.at[idx, '주소'] = ''
        fail_count += 1
    else:
        print(f"  ✓ 주소: {address}")
        df.at[idx, '주소'] = address
        success_count += 1

    # 진행률 표시
    if (idx + 1) % 50 == 0:
        print(f"\n진행률: {idx + 1}/{len(data_rows)} ({(idx + 1) / len(data_rows) * 100:.1f}%)")
        print(f"성공: {success_count}, 실패: {fail_count}")

    time.sleep(0.3)  # 서버 부하 방지

print("\n" + "=" * 50)
print(f"\n크롤링 완료!")
print(f"✓ 성공: {success_count}개")
print(f"❌ 실패: {fail_count}개")

# 컬럼 순서 재정렬: 지역명_매장명, 매장명, 지역명, 전화번호, 주소, 링크
new_column_order = ['지역명_매장명', '매장명', '지역명', '전화번호', '주소', '링크']
df = df[new_column_order]

print(f"\nsummary 워크시트 업데이트 중...")
summary_sheet.clear()
summary_sheet.update(values=[new_column_order] + df.values.tolist(), range_name='A1')

print("✓ summary 시트 업데이트 완료!")

print(f"\n전체 작업 완료!")
print(f"- 총 행 수: {len(df)}")
print(f"- 주소 수집 성공: {success_count}개 ({success_count / len(df) * 100:.1f}%)")
print(f"- 주소 수집 실패: {fail_count}개 ({fail_count / len(df) * 100:.1f}%)")
