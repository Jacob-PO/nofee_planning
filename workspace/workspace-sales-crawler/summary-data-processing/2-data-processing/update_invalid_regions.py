"""
잘못된 지역명만 크롤링하여 업데이트하는 스크립트
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # XPath: /html/body/main/div[1]/article/aside/section/div/ul/li[4]/div/span/button/span
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

        # 백업: 주소 패턴으로 검색
        address_patterns = [
            r'([가-힣]+시|[가-힣]+도)\s+([가-힣]+구|[가-힣]+군)',
            r'([가-힣]+특별시|[가-힣]+광역시)\s+([가-힣]+구)',
        ]

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


def update_invalid_regions():
    """잘못된 지역명만 크롤링하여 업데이트"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("잘못된 지역명만 크롤링하여 업데이트")
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
        link_col = None
        region_col = None
        location_col = None

        for col in df.columns:
            if '링크' in col or 'link' in col.lower():
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

        # 잘못된 지역명만 크롤링
        print("\n" + "=" * 80)
        print(f"주소 크롤링 시작 ({len(invalid_indices)}개)")
        print("=" * 80)

        updated_count = 0
        failed_count = 0
        skipped_count = 0

        for i, idx in enumerate(invalid_indices, 1):
            link = df.iloc[idx][link_col]
            current_region = df.iloc[idx][region_col]
            location_name = df.iloc[idx][location_col] if location_col else ''

            if not link or link == '링크':
                skipped_count += 1
                continue

            # 당근 링크만 크롤링
            parsed = urlparse(link)
            if 'daangn' not in parsed.netloc:
                skipped_count += 1
                continue

            # 진행 상황 출력 (50개마다)
            if i % 50 == 0:
                print(f"\n진행: {i}/{len(invalid_indices)} ({i/len(invalid_indices)*100:.1f}%)")
                print(f"  업데이트: {updated_count}, 실패: {failed_count}, 건너뜀: {skipped_count}")

            address = extract_address_from_daangn(link)
            if address:
                region = extract_region_from_address(address)
                if region:
                    df.at[idx, region_col] = region
                    updated_count += 1

                    # 처음 20개는 상세 로그 출력
                    if updated_count <= 20:
                        print(f"\n[{i}/{len(invalid_indices)}] {location_name}")
                        print(f"  이전: {current_region}")
                        print(f"  이후: {region}")
                        print(f"  주소: {address}")
            else:
                failed_count += 1
                if failed_count <= 10:  # 처음 10개 실패만 출력
                    print(f"\n✗ [{i}] 주소 찾기 실패: {location_name}")

            # 요청 간격 (서버 부하 방지: 1초)
            time.sleep(1)

        # 결과 요약
        print("\n" + "=" * 80)
        print("크롤링 완료")
        print("=" * 80)
        print(f"처리 대상: {len(invalid_indices)}개")
        print(f"  - 업데이트 성공: {updated_count}개")
        print(f"  - 실패: {failed_count}개")
        print(f"  - 건너뜀: {skipped_count}개")

        if updated_count > 0:
            # Summary 시트에 업데이트
            print(f"\n'{summary_sheet_name}' 워크시트에 데이터 쓰는 중...")

            # 시트 초기화
            worksheet.clear()

            # 헤더 + 데이터 준비
            all_data = [df.columns.tolist()] + df.values.tolist()

            # 데이터 업로드
            worksheet.update(values=all_data, range_name='A1')

            print(f"\n✅ 작업 완료!")
            print(f"   - {updated_count}개 지역명 업데이트됨")
            print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        else:
            print("\n⚠️  업데이트할 데이터가 없습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  이 스크립트는 잘못된 지역명(약 504개)만 크롤링하여 업데이트합니다.")
    print(f"⚠️  예상 소요 시간: 약 8-10분\n")

    # 자동 실행
    update_invalid_regions()
