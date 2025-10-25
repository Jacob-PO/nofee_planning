"""
summary 워크시트에서 잘못된 지역명을 가진 데이터를 찾는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path
import re

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'


def is_valid_region(region):
    """지역명이 올바른 형식인지 검증"""
    if not region or region == '':
        return False

    # 올바른 지역명 패턴
    valid_patterns = [
        # 광역시/특별시 + 구
        r'^(서울|부산|대구|인천|광주|대전|울산)\s+[가-힣]+구$',
        # 세종
        r'^세종$',
        # 도 + 시
        r'^(경기|강원|충북|충남|전북|전남|경북|경남|제주)\s+[가-힣]+시$',
        # 도 + 군
        r'^(경기|강원|충북|충남|전북|전남|경북|경남)\s+[가-힣]+군$',
    ]

    for pattern in valid_patterns:
        if re.match(pattern, region):
            return True

    return False


def find_invalid_regions():
    """summary 워크시트에서 잘못된 지역명 찾기"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("잘못된 지역명 찾기")
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

        # 지역명 컬럼 찾기
        region_col = None
        location_col = None
        link_col = None

        for col in df.columns:
            if col == '지역명':
                region_col = col
            elif '지역명_매장명' in col:
                location_col = col
            elif '링크' in col:
                link_col = col

        if not region_col:
            print("❌ 지역명 컬럼을 찾을 수 없습니다.")
            return

        print(f"\n지역명 컬럼: {region_col}")

        # 잘못된 지역명 찾기
        print("\n" + "=" * 80)
        print("지역명 검증 중...")
        print("=" * 80)

        invalid_regions = []

        for idx, row in df.iterrows():
            region = row[region_col]
            location = row[location_col] if location_col else ''
            link = row[link_col] if link_col else ''

            if not is_valid_region(region):
                invalid_regions.append({
                    'index': idx,
                    'location': location,
                    'region': region,
                    'link': link
                })

        # 결과 출력
        print(f"\n검증 완료:")
        print(f"  - 전체: {len(df)}개")
        print(f"  - 올바른 지역명: {len(df) - len(invalid_regions)}개")
        print(f"  - 잘못된 지역명: {len(invalid_regions)}개")

        if invalid_regions:
            print("\n" + "=" * 80)
            print(f"잘못된 지역명 목록 (처음 20개)")
            print("=" * 80)

            for i, item in enumerate(invalid_regions[:20], 1):
                print(f"\n[{i}] 행 {item['index'] + 2}")  # +2는 헤더 포함 및 0-index 보정
                print(f"  지역명_매장명: {item['location']}")
                print(f"  지역명: {item['region']}")
                print(f"  링크: {item['link'][:80]}..." if len(item['link']) > 80 else f"  링크: {item['link']}")

            if len(invalid_regions) > 20:
                print(f"\n... 외 {len(invalid_regions) - 20}개 더 있습니다.")

            # CSV로 저장
            invalid_df = pd.DataFrame(invalid_regions)
            output_file = 'invalid_regions.csv'
            invalid_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n✓ 잘못된 지역명 목록을 '{output_file}'에 저장했습니다.")

        else:
            print("\n✅ 모든 지역명이 올바른 형식입니다!")

        print("\n" + "=" * 80)

        return invalid_regions

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    find_invalid_regions()
