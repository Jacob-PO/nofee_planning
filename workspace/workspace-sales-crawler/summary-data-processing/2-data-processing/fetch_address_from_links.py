"""
summary 워크시트의 링크에서 주소 정보를 크롤링하여 지역명을 정제하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'


def extract_address_from_daangn(url):
    """당근마켓 페이지에서 주소 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # XPath: /html/body/main/div[1]/article/aside/section/div/ul/li[4]/div/span/button/span
        # BeautifulSoup로 변환하여 찾기

        # 방법 1: 특정 위치의 버튼 내 span 찾기
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
                            lis = ul.find_all('li')
                            if len(lis) >= 4:
                                # 4번째 li (인덱스 3)
                                li_4 = lis[3]
                                button = li_4.find('button')
                                if button:
                                    span = button.find('span')
                                    if span:
                                        address = span.get_text(strip=True)
                                        if address:
                                            return address

        # 방법 2: 주소 패턴으로 검색 (백업)
        address_patterns = [
            r'([가-힣]+시|[가-힣]+도)\s+([가-힣]+구|[가-힣]+군)',
            r'([가-힣]+특별시|[가-힣]+광역시)\s+([가-힣]+구)',
        ]

        # 모든 button > span 요소에서 주소 패턴 찾기
        buttons = soup.find_all('button')
        for button in buttons:
            spans = button.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)
                for pattern in address_patterns:
                    if re.search(pattern, text):
                        return text

        return None

    except Exception as e:
        print(f"  ⚠️  주소 추출 실패: {e}")
        return None


def extract_region_from_address(address):
    """주소에서 '시/도 구/군' 형태의 지역명 추출"""
    if not address:
        return None

    # 주소 예시:
    # "대구광역시 달성군 논공읍 논공로 733" → "대구 달성군"
    # "경기도 남양주시 중앙로7번길 15 (호평동)" → "경기 남양주시"
    # "서울특별시 성동구 천호대로 450 (용답동)" → "서울 성동구"

    # 도로명주소에서 지역명만 추출
    # 패턴: 시/도 + 구/군/시
    patterns = [
        # "서울특별시 강남구" → "서울 강남구"
        (r'서울특별시\s+([가-힣]+구)', '서울'),
        (r'부산광역시\s+([가-힣]+구)', '부산'),
        (r'대구광역시\s+([가-힣]+구|[가-힣]+군)', '대구'),
        (r'인천광역시\s+([가-힣]+구)', '인천'),
        (r'광주광역시\s+([가-힣]+구)', '광주'),
        (r'대전광역시\s+([가-힣]+구)', '대전'),
        (r'울산광역시\s+([가-힣]+구)', '울산'),
        (r'세종특별자치시', '세종'),
        # "경기도 수원시" → "경기 수원시"
        (r'경기도\s+([가-힣]+시)', '경기'),
        (r'강원도\s+([가-힣]+시|[가-힣]+군)', '강원'),
        (r'충청북도\s+([가-힣]+시|[가-힣]+군)', '충북'),
        (r'충청남도\s+([가-힣]+시|[가-힣]+군)', '충남'),
        (r'전라북도\s+([가-힣]+시|[가-힣]+군)', '전북'),
        (r'전라남도\s+([가-힣]+시|[가-힣]+군)', '전남'),
        (r'경상북도\s+([가-힣]+시|[가-힣]+군)', '경북'),
        (r'경상남도\s+([가-힣]+시|[가-힣]+군)', '경남'),
        (r'제주특별자치도\s+([가-힣]+시)', '제주'),
    ]

    for pattern, prefix in patterns:
        match = re.search(pattern, address)
        if match:
            if len(match.groups()) > 0:
                return f"{prefix} {match.group(1)}"
            else:
                return prefix

    # 패턴에 매칭되지 않으면 원본 주소 반환
    return address


def fetch_addresses_from_summary():
    """summary 워크시트에서 링크를 읽고 주소를 크롤링"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("Summary 링크에서 주소 크롤링")
        print("=" * 80)

        # Google Sheets API 연결
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = service_account.Credentials.from_service_account_file(
            str(api_key_file), scopes=scope)
        client = gspread.authorize(creds)

        print("\n✓ Google Sheets API 연결 성공")

        # 스프레드시트 열기
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(summary_sheet_name)

        # 데이터 읽기
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        df = pd.DataFrame(data_rows, columns=headers)

        print(f"\n총 {len(df)}개 행 읽음")

        # 링크 컬럼 찾기
        link_col = None
        for col in df.columns:
            if '링크' in col or 'link' in col.lower() or 'url' in col.lower():
                link_col = col
                break

        if not link_col:
            print("❌ 링크 컬럼을 찾을 수 없습니다.")
            return

        # 테스트: 처음 10개만 크롤링
        print("\n" + "=" * 80)
        print("주소 크롤링 시작 (테스트: 처음 10개)")
        print("=" * 80)

        results = []

        for idx in range(min(10, len(df))):
            link = df.iloc[idx][link_col]
            current_region = df.iloc[idx]['지역명'] if '지역명' in df.columns else ''
            location_name = df.iloc[idx]['지역명_매장명'] if '지역명_매장명' in df.columns else ''

            if not link or link == '링크':
                continue

            print(f"\n[{idx + 1}/10] {location_name}")
            print(f"  현재 지역명: {current_region}")
            print(f"  링크: {link}")

            # 당근 링크인 경우만 크롤링
            parsed = urlparse(link)
            if 'daangn' in parsed.netloc:
                address = extract_address_from_daangn(link)
                if address:
                    region = extract_region_from_address(address)
                    print(f"  ✓ 추출된 주소: {address}")
                    print(f"  ✓ 정제된 지역명: {region}")

                    results.append({
                        'index': idx,
                        'location_name': location_name,
                        'old_region': current_region,
                        'new_region': region,
                        'address': address,
                        'link': link
                    })
                else:
                    print(f"  ✗ 주소를 찾을 수 없습니다.")

            # 요청 간격 (서버 부하 방지)
            time.sleep(1)

        # 결과 요약
        print("\n" + "=" * 80)
        print("크롤링 결과 요약")
        print("=" * 80)

        if results:
            print(f"\n총 {len(results)}개의 주소를 찾았습니다.")
            print("\n변경 사항:")
            for result in results:
                if result['old_region'] != result['new_region']:
                    print(f"\n  {result['location_name']}")
                    print(f"    이전: {result['old_region']}")
                    print(f"    이후: {result['new_region']}")
        else:
            print("\n주소를 찾지 못했습니다.")

        print("\n" + "=" * 80)
        print("테스트 완료")
        print("=" * 80)
        print("\n⚠️  이것은 테스트 실행입니다. 실제 업데이트는 하지 않았습니다.")
        print("전체 데이터를 처리하려면 스크립트를 수정하세요.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fetch_addresses_from_summary()
