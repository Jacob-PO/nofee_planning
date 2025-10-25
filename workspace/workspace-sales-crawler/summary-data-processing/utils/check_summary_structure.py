"""
summary 워크시트의 구조를 확인하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent
config_dir = project_root / 'config'

def check_summary_structure():
    """summary 워크시트의 구조 확인"""

    # Google Sheets 정보
    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'
    daangn_sheet_name = 'daangn'

    # 인증 파일 경로
    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("Google Sheets API 연결 중...")

        # 인증 설정
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = service_account.Credentials.from_service_account_file(
            str(api_key_file), scopes=scope)
        client = gspread.authorize(creds)

        print("✓ Google Sheets API 연결 성공\n")

        # 스프레드시트 열기
        spreadsheet = client.open_by_key(spreadsheet_id)

        # summary 워크시트 확인
        print("=" * 80)
        print(f"[ {summary_sheet_name} 워크시트 구조 ]")
        print("=" * 80)
        try:
            summary_worksheet = spreadsheet.worksheet(summary_sheet_name)
            summary_data = summary_worksheet.get_all_values()

            if summary_data:
                df_summary = pd.DataFrame(summary_data[1:], columns=summary_data[0])
                print(f"\n총 {len(df_summary)}개 행")
                print(f"\n컬럼 목록 ({len(df_summary.columns)}개):")
                for i, col in enumerate(df_summary.columns, 1):
                    print(f"  {i}. {col}")

                print(f"\n데이터 샘플 (처음 5개 행):")
                print(df_summary.head(5).to_string())

                # 데이터 타입 확인
                print(f"\n각 컬럼의 샘플 데이터:")
                for col in df_summary.columns:
                    non_empty = df_summary[col][df_summary[col] != ''].head(3).tolist()
                    print(f"  - {col}: {non_empty}")

            else:
                print(f"'{summary_sheet_name}' 워크시트가 비어있습니다.")

        except gspread.WorksheetNotFound:
            print(f"'{summary_sheet_name}' 워크시트가 존재하지 않습니다.")

        # daangn 워크시트 확인
        print("\n" + "=" * 80)
        print(f"[ {daangn_sheet_name} 워크시트 구조 ]")
        print("=" * 80)
        try:
            daangn_worksheet = spreadsheet.worksheet(daangn_sheet_name)
            daangn_data = daangn_worksheet.get_all_values()

            if daangn_data:
                df_daangn = pd.DataFrame(daangn_data[1:], columns=daangn_data[0])
                print(f"\n총 {len(df_daangn)}개 행")
                print(f"\n컬럼 목록 ({len(df_daangn.columns)}개):")
                for i, col in enumerate(df_daangn.columns, 1):
                    print(f"  {i}. {col}")

                print(f"\n데이터 샘플 (처음 5개 행):")
                print(df_daangn.head(5).to_string())

                # 데이터 타입 확인
                print(f"\n각 컬럼의 샘플 데이터:")
                for col in df_daangn.columns:
                    non_empty = df_daangn[col][df_daangn[col] != ''].head(3).tolist()
                    print(f"  - {col}: {non_empty}")

            else:
                print(f"'{daangn_sheet_name}' 워크시트가 비어있습니다.")

        except gspread.WorksheetNotFound:
            print(f"'{daangn_sheet_name}' 워크시트가 존재하지 않습니다.")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_summary_structure()
