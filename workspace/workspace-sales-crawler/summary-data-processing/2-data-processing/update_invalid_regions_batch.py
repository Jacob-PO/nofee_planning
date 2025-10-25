"""
잘못된 지역명을 5개씩 배치로 크롤링하고 시트를 업데이트하는 스크립트
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
import sys

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'

# 출력 버퍼링 비활성화
sys.stdout.reconfigure(line_buffering=True)


def is_valid_region(region):
    """지역명이 올바른 형식인지 검증"""
    if not region or region == '':
        return False

    valid_patterns = [
        r'^(서울|부산|대구|인천|광주|대전|울산)\s+[가-힣]+구$',
        r'^세종$',
        r'^(경기|강원|충북|충남|전북|전남|경북|경남|제주)\s+[가-힣]+시$',
        r'^(경기|강원|충북|충남|전북|전남|경북|경남)\s+[가-힣]+군$',
    ]

    for pattern in valid_patterns:
        if re.match(pattern, region):
            return True

    return False


def extract_address_from_daangn(url):
    """당근마켓 페이지에서 주소 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

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
                                li_4 = lis[3]
                                button = li_4.find('button')
                                if button:
                                    span = button.find('span')
                                    if span:
                                        address = span.get_text(strip=True)
                                        if address:
                                            return address

        return None

    except Exception as e:
        return None


def extract_region_from_address(address):
    """주소에서 '시/도 구/군' 형태의 지역명 추출"""
    if not address:
        return None

    patterns = [
        (r'서울특별시\s+([가-힣]+구)', '서울'),
        (r'부산광역시\s+([가-힣]+구)', '부산'),
        (r'대구광역시\s+([가-힣]+구|[가-힣]+군)', '대구'),
        (r'인천광역시\s+([가-힣]+구)', '인천'),
        (r'광주광역시\s+([가-힣]+구)', '광주'),
        (r'대전광역시\s+([가-힣]+구)', '대전'),
        (r'울산광역시\s+([가-힣]+구)', '울산'),
        (r'세종특별자치시', '세종'),
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

    return address


def update_invalid_regions_batch():
    """잘못된 지역명을 5개씩 배치로 크롤링하고 업데이트"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'
    BATCH_SIZE = 5

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print(f"잘못된 지역명을 {BATCH_SIZE}개씩 배치로 크롤링하여 업데이트")
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

        # 컬럼 찾기
        link_col = region_col = location_col = None

        for col in df.columns:
            if '링크' in col:
                link_col = col
            elif col == '지역명':
                region_col = col
            elif '지역명_매장명' in col:
                location_col = col

        if not link_col or not region_col:
            print("❌ 필수 컬럼을 찾을 수 없습니다.")
            return

        # 잘못된 지역명 찾기
        print("\n지역명 검증 중...")
        invalid_indices = []

        for idx, row in df.iterrows():
            region = row[region_col]
            if not is_valid_region(region):
                invalid_indices.append(idx)

        print(f"✓ 잘못된 지역명: {len(invalid_indices)}개 발견")

        if len(invalid_indices) == 0:
            print("\n✅ 모든 지역명이 올바른 형식입니다!")
            return

        # 배치 처리
        print("\n" + "=" * 80)
        print(f"배치 크롤링 시작 ({len(invalid_indices)}개, {BATCH_SIZE}개씩)")
        print("=" * 80)

        total_updated = 0
        total_failed = 0
        batch_num = 0

        for i in range(0, len(invalid_indices), BATCH_SIZE):
            batch_indices = invalid_indices[i:i + BATCH_SIZE]
            batch_num += 1

            print(f"\n[배치 {batch_num}] 처리 중... ({i+1}-{min(i+BATCH_SIZE, len(invalid_indices))}/{len(invalid_indices)})")

            batch_updated = 0

            for idx in batch_indices:
                link = df.iloc[idx][link_col]
                current_region = df.iloc[idx][region_col]
                location_name = df.iloc[idx][location_col] if location_col else ''

                if not link or link == '링크':
                    continue

                parsed = urlparse(link)
                if 'daangn' not in parsed.netloc:
                    continue

                print(f"  크롤링: {location_name[:30]}...")

                address = extract_address_from_daangn(link)
                if address:
                    region = extract_region_from_address(address)
                    if region:
                        df.at[idx, region_col] = region
                        batch_updated += 1
                        total_updated += 1
                        print(f"    ✓ {current_region} → {region}")
                    else:
                        total_failed += 1
                        print(f"    ✗ 지역명 추출 실패")
                else:
                    total_failed += 1
                    print(f"    ✗ 주소 찾기 실패")

                time.sleep(1)  # 서버 부하 방지

            # 배치 업데이트
            if batch_updated > 0:
                print(f"\n  시트 업데이트 중... ({batch_updated}개 변경)")

                # 시트 초기화
                worksheet.clear()

                # 헤더 + 데이터 업로드
                all_data = [df.columns.tolist()] + df.values.tolist()
                worksheet.update(values=all_data, range_name='A1')

                print(f"  ✓ 배치 업데이트 완료")
                print(f"  현재까지 총 업데이트: {total_updated}개, 실패: {total_failed}개")

        # 최종 결과
        print("\n" + "=" * 80)
        print("✅ 전체 작업 완료!")
        print("=" * 80)
        print(f"처리 대상: {len(invalid_indices)}개")
        print(f"  - 업데이트 성공: {total_updated}개")
        print(f"  - 실패: {total_failed}개")
        print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_invalid_regions_batch()
