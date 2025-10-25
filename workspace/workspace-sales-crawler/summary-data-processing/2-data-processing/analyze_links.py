"""
summary 워크시트의 링크를 분석하여 어떤 소스(daangn, naver, google)인지 확인하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path
from urllib.parse import urlparse

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'


def analyze_summary_links():
    """summary 워크시트의 링크 분석"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("Summary 워크시트 링크 분석")
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

        print(f"\n링크 컬럼: {link_col}")

        # 링크 분석
        print("\n" + "=" * 80)
        print("링크 소스 분석")
        print("=" * 80)

        link_sources = {}
        for idx, link in enumerate(df[link_col]):
            if link:
                parsed = urlparse(link)
                domain = parsed.netloc

                if 'daangn' in domain:
                    source = 'daangn'
                elif 'naver' in domain:
                    source = 'naver'
                elif 'google' in domain:
                    source = 'google'
                else:
                    source = 'unknown'

                link_sources[source] = link_sources.get(source, 0) + 1

        print("\n링크 소스별 개수:")
        for source, count in sorted(link_sources.items()):
            print(f"  - {source}: {count}개")

        # 각 소스별 샘플 링크 출력
        print("\n" + "=" * 80)
        print("소스별 샘플 링크 (처음 3개)")
        print("=" * 80)

        samples_by_source = {}
        for idx, link in enumerate(df[link_col]):
            if link:
                parsed = urlparse(link)
                domain = parsed.netloc

                if 'daangn' in domain:
                    source = 'daangn'
                elif 'naver' in domain:
                    source = 'naver'
                elif 'google' in domain:
                    source = 'google'
                else:
                    source = 'unknown'

                if source not in samples_by_source:
                    samples_by_source[source] = []

                if len(samples_by_source[source]) < 3:
                    samples_by_source[source].append({
                        'index': idx,
                        'link': link,
                        'location': df.iloc[idx]['지역명_매장명'] if '지역명_매장명' in df.columns else '',
                        'region': df.iloc[idx]['지역명'] if '지역명' in df.columns else ''
                    })

        for source, samples in sorted(samples_by_source.items()):
            print(f"\n[{source.upper()}]")
            for sample in samples:
                print(f"  행 {sample['index']}:")
                print(f"    지역명_매장명: {sample['location']}")
                print(f"    지역명: {sample['region']}")
                print(f"    링크: {sample['link']}")

        print("\n" + "=" * 80)
        print("분석 완료")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_summary_links()
