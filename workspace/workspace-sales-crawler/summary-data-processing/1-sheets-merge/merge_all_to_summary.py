"""
daangn, naver, google 워크시트의 데이터를 summary 워크시트에 통합하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path
import re

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'


def process_sheet_data(df, sheet_name):
    """개별 시트 데이터 처리 함수"""
    print(f"\n[{sheet_name}] 데이터 처리 중...")

    if df is None or len(df) == 0:
        print(f"[{sheet_name}] 데이터가 없습니다.")
        return None

    # NaN 값을 빈 문자열로 변환
    df = df.fillna('')

    # 컬럼 찾기
    phone_col = None
    location_store_col = None
    store_name_col = None
    location_col = None
    link_col = None

    for col in df.columns:
        if '전화' in col or 'phone' in col.lower() or '연락처' in col:
            phone_col = col
        elif '지역명_매장명' in col or '지역_매장' in col:
            location_store_col = col
        elif col == '매장명' or ('매장' in col and '지역' not in col):
            store_name_col = col
        elif col == '지역명' or ('지역' in col and '매장' not in col):
            location_col = col
        elif '링크' in col or 'link' in col.lower() or 'url' in col.lower():
            link_col = col

    if not phone_col or not location_store_col:
        print(f"[{sheet_name}] ❌ 필수 컬럼을 찾을 수 없습니다.")
        return None

    # 전화번호가 있는 데이터만 필터링
    initial_count = len(df)
    df_filtered = df[df[phone_col] != ''].copy()
    filtered_count = initial_count - len(df_filtered)
    print(f"[{sheet_name}] 전화번호 없는 데이터 제거: {filtered_count}개 행")

    if len(df_filtered) == 0:
        print(f"[{sheet_name}] 처리할 데이터가 없습니다.")
        return None

    # 필요한 컬럼만 선택하고 표준 컬럼명으로 변경
    result_data = {
        '지역명_매장명': df_filtered[location_store_col].tolist(),
        '전화번호': df_filtered[phone_col].tolist()
    }

    if store_name_col and store_name_col in df_filtered.columns:
        result_data['매장명'] = df_filtered[store_name_col].tolist()
    else:
        result_data['매장명'] = [''] * len(df_filtered)

    if location_col and location_col in df_filtered.columns:
        result_data['지역명'] = df_filtered[location_col].tolist()
    else:
        result_data['지역명'] = [''] * len(df_filtered)

    if link_col and link_col in df_filtered.columns:
        result_data['링크'] = df_filtered[link_col].tolist()
    else:
        result_data['링크'] = [''] * len(df_filtered)

    # DataFrame 생성 (컬럼 순서: 지역명_매장명, 매장명, 지역명, 전화번호, 링크)
    result_df = pd.DataFrame({
        '지역명_매장명': result_data['지역명_매장명'],
        '매장명': result_data['매장명'],
        '지역명': result_data['지역명'],
        '전화번호': result_data['전화번호'],
        '링크': result_data['링크']
    })

    print(f"[{sheet_name}] 처리 완료: {len(result_df)}개 행")
    return result_df


def merge_all_sheets_to_summary():
    """daangn, naver, google 워크시트 데이터를 통합하여 summary에 업로드"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    sheet_names = ['daangn', 'naver', 'google']
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("Google Sheets API 연결 중...")
        print("=" * 80)

        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = service_account.Credentials.from_service_account_file(
            str(api_key_file), scopes=scope)
        client = gspread.authorize(creds)

        print("✓ Google Sheets API 연결 성공\n")

        spreadsheet = client.open_by_key(spreadsheet_id)

        # 각 시트에서 데이터 읽기
        all_dfs = []

        for sheet_name in sheet_names:
            try:
                print(f"'{sheet_name}' 워크시트 읽는 중...")
                worksheet = spreadsheet.worksheet(sheet_name)

                # 먼저 모든 값을 가져와서 직접 DataFrame 생성 (헤더 중복 문제 회피)
                all_values = worksheet.get_all_values()

                if all_values and len(all_values) > 1:
                    # 첫 행을 헤더로, 나머지를 데이터로
                    headers = all_values[0]
                    data_rows = all_values[1:]
                    df = pd.DataFrame(data_rows, columns=headers)
                    print(f"✓ {len(df)}개 행 읽음")

                    # 데이터 처리
                    processed_df = process_sheet_data(df, sheet_name)
                    if processed_df is not None:
                        all_dfs.append(processed_df)
                else:
                    print(f"'{sheet_name}' 워크시트가 비어있습니다.")

            except gspread.WorksheetNotFound:
                print(f"❌ '{sheet_name}' 워크시트를 찾을 수 없습니다.")
            except Exception as e:
                print(f"❌ '{sheet_name}' 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()

        if not all_dfs:
            print("\n처리할 데이터가 없습니다.")
            return

        # 모든 데이터 통합
        print("\n" + "=" * 80)
        print("데이터 통합 중...")
        print("=" * 80)

        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"통합 전 총 데이터: {len(combined_df)}개 행")

        # 지역명_매장명 + 전화번호 기준 중복 제거
        print("\n중복 제거 중 (지역명_매장명 + 전화번호 기준)...")
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['지역명_매장명', '전화번호'], keep='first')
        removed = before_dedup - len(combined_df)
        print(f"✓ {removed}개 중복 행 제거")
        print(f"✓ 남은 데이터: {len(combined_df)}개 행")

        # 같은 전화번호가 여러 매장을 가진 경우 넘버링
        print("\n전화번호 중복 체크 및 넘버링 중...")
        phone_counts = combined_df['전화번호'].value_counts()
        phones_with_multiple = phone_counts[phone_counts > 1].index.tolist()
        phones_with_multiple = [p for p in phones_with_multiple if p != '']

        if phones_with_multiple:
            print(f"✓ {len(phones_with_multiple)}개의 전화번호가 여러 매장을 가지고 있습니다.")

            for phone in phones_with_multiple:
                mask = combined_df['전화번호'] == phone
                indices = combined_df[mask].index.tolist()

                for idx, row_idx in enumerate(indices, 1):
                    original_name = combined_df.loc[row_idx, '지역명_매장명']
                    name_without_number = re.sub(r'_\d+$', '', original_name)
                    new_name = f"{name_without_number}_{idx}"
                    combined_df.loc[row_idx, '지역명_매장명'] = new_name

            print(f"✓ 넘버링 완료")
        else:
            print("✓ 중복된 전화번호가 없습니다.")

        # 지역명_매장명 기준 오름차순 정렬
        print("\n지역명_매장명 기준 오름차순 정렬 중...")
        combined_df = combined_df.sort_values(by='지역명_매장명', ascending=True)
        combined_df = combined_df.reset_index(drop=True)
        print("✓ 정렬 완료")

        # summary 워크시트 준비
        print(f"\n'{summary_sheet_name}' 워크시트 준비 중...")
        try:
            summary_worksheet = spreadsheet.worksheet(summary_sheet_name)
            print(f"✓ '{summary_sheet_name}' 워크시트 찾음")
        except gspread.WorksheetNotFound:
            summary_worksheet = spreadsheet.add_worksheet(
                title=summary_sheet_name,
                rows=2000,
                cols=10
            )
            print(f"✓ '{summary_sheet_name}' 워크시트 생성 완료")

        # summary 워크시트에 데이터 쓰기
        print(f"\n'{summary_sheet_name}' 워크시트에 데이터 쓰는 중...")

        # 시트 초기화
        summary_worksheet.clear()

        # 헤더 + 데이터 준비
        headers = combined_df.columns.tolist()
        data_rows = combined_df.values.tolist()
        all_data = [headers] + data_rows

        # 데이터 업로드
        summary_worksheet.update(values=all_data, range_name='A1')

        print("\n" + "=" * 80)
        print("✅ 작업 완료!")
        print("=" * 80)
        print(f"총 {len(combined_df)}개 행이 '{summary_sheet_name}' 워크시트에 업로드되었습니다.")
        print(f"\n컬럼 순서:")
        for i, col in enumerate(headers, 1):
            print(f"  {i}. {col}")
        print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 80)
    print("daangn + naver + google → summary 데이터 통합 스크립트")
    print("=" * 80)
    print()

    merge_all_sheets_to_summary()
