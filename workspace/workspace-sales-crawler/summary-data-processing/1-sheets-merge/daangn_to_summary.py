"""
daangn, naver, google 워크시트의 데이터를 summary 워크시트에 정리하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent
config_dir = project_root / 'config'

def process_sheet_data(df, sheet_name):
    """개별 시트 데이터 처리 함수"""
    print(f"\n[{sheet_name}] 데이터 처리 중...")

    # NaN 값을 빈 문자열로 변환
    df = df.fillna('')

    # 컬럼 찾기
    phone_col = None
    location_store_col = None
    store_name_col = None
    location_col = None
    link_col = None

    # 전화번호 컬럼 찾기
    for col in df.columns:
        if '전화' in col or 'phone' in col.lower() or '연락처' in col:
            phone_col = col
            break

    # 지역명_매장명 컬럼 찾기
    for col in df.columns:
        if '지역명_매장명' in col or '지역_매장' in col:
            location_store_col = col
            break

    # 매장명 컬럼 찾기
    for col in df.columns:
        if col == '매장명' or 'store' in col.lower():
            store_name_col = col
            break

    # 지역명 컬럼 찾기
    for col in df.columns:
        if col == '지역명' or 'location' in col.lower() or 'region' in col.lower():
            location_col = col
            break

    # 링크 컬럼 찾기
    for col in df.columns:
        if '링크' in col or 'link' in col.lower() or 'url' in col.lower():
            link_col = col
            break

    if not phone_col or not location_store_col:
        print(f"[{sheet_name}] ❌ 필수 컬럼을 찾을 수 없습니다.")
        if not phone_col:
            print(f"   - 전화번호 컬럼을 찾을 수 없습니다.")
        if not location_store_col:
            print(f"   - 지역명_매장명 컬럼을 찾을 수 없습니다.")
        return None

    # 전화번호가 없는 데이터 필터링
    initial_count = len(df)
    df_filtered = df[df[phone_col] != ''].copy()
    filtered_count = initial_count - len(df_filtered)
    print(f"[{sheet_name}] 전화번호 없는 데이터 제거: {filtered_count}개 행")
    print(f"[{sheet_name}] 남은 데이터: {len(df_filtered)}개 행")

    if len(df_filtered) == 0:
        print(f"[{sheet_name}] 처리할 데이터가 없습니다.")
        return None

    # 필요한 컬럼만 선택
    available_cols = [location_store_col, phone_col]
    col_names = ['지역명_매장명', '전화번호']

    if store_name_col:
        available_cols.insert(1, store_name_col)
        col_names.insert(1, '매장명')
    if location_col:
        available_cols.insert(2 if store_name_col else 1, location_col)
        col_names.insert(2 if store_name_col else 1, '지역명')
    if link_col:
        available_cols.append(link_col)
        col_names.append('링크')

    result_df = df_filtered[available_cols].copy()
    result_df.columns = col_names

    print(f"[{sheet_name}] 선택된 컬럼: {', '.join(col_names)}")
    print(f"[{sheet_name}] 처리 완료: {len(result_df)}개 행")

    return result_df

def process_all_sheets_to_summary():
    """daangn, naver, google 워크시트 데이터를 읽어서 summary 워크시트에 정리"""

    # Google Sheets 정보
    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    sheet_names = ['daangn', 'naver', 'google']
    summary_sheet_name = 'summary'

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

        print("✓ Google Sheets API 연결 성공")

        # 스프레드시트 열기
        spreadsheet = client.open_by_key(spreadsheet_id)

        # daangn 워크시트에서 데이터 읽기
        print(f"\n'{daangn_sheet_name}' 워크시트에서 데이터 읽는 중...")
        daangn_worksheet = spreadsheet.worksheet(daangn_sheet_name)
        daangn_data = daangn_worksheet.get_all_records()

        if not daangn_data:
            print(f"❌ '{daangn_sheet_name}' 워크시트에 데이터가 없습니다.")
            return

        df = pd.DataFrame(daangn_data)
        print(f"✓ {len(df)}개의 데이터를 읽었습니다.")
        print(f"\n컬럼 목록:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        # 데이터 미리보기
        print(f"\n데이터 미리보기 (처음 3개 행):")
        print(df.head(3).to_string())

        # summary 워크시트 준비
        print(f"\n'{summary_sheet_name}' 워크시트 준비 중...")
        try:
            summary_worksheet = spreadsheet.worksheet(summary_sheet_name)
            print(f"✓ '{summary_sheet_name}' 워크시트 찾음")
        except gspread.WorksheetNotFound:
            summary_worksheet = spreadsheet.add_worksheet(
                title=summary_sheet_name,
                rows=1000,
                cols=20
            )
            print(f"✓ '{summary_sheet_name}' 워크시트 생성 완료")

        # 데이터 가공
        print("\n데이터 가공 중...")

        # NaN 값을 빈 문자열로 변환
        df = df.fillna('')

        # 컬럼 찾기
        phone_col = None
        location_store_col = None
        store_name_col = None
        location_col = None
        link_col = None

        # 전화번호 컬럼 찾기
        for col in df.columns:
            if '전화' in col or 'phone' in col.lower() or '연락처' in col:
                phone_col = col
                break

        # 지역명_매장명 컬럼 찾기
        for col in df.columns:
            if '지역명_매장명' in col or '지역_매장' in col:
                location_store_col = col
                break

        # 매장명 컬럼 찾기
        for col in df.columns:
            if col == '매장명' or 'store' in col.lower():
                store_name_col = col
                break

        # 지역명 컬럼 찾기
        for col in df.columns:
            if col == '지역명' or 'location' in col.lower() or 'region' in col.lower():
                location_col = col
                break

        # 링크 컬럼 찾기
        for col in df.columns:
            if '링크' in col or 'link' in col.lower() or 'url' in col.lower():
                link_col = col
                break

        if not phone_col or not location_store_col or not store_name_col or not location_col or not link_col:
            print("❌ 필요한 컬럼을 찾을 수 없습니다.")
            if not phone_col:
                print("   - 전화번호 컬럼을 찾을 수 없습니다.")
            if not location_store_col:
                print("   - 지역명_매장명 컬럼을 찾을 수 없습니다.")
            if not store_name_col:
                print("   - 매장명 컬럼을 찾을 수 없습니다.")
            if not location_col:
                print("   - 지역명 컬럼을 찾을 수 없습니다.")
            if not link_col:
                print("   - 링크 컬럼을 찾을 수 없습니다.")
            return

        # 1. 전화번호가 없는 데이터 필터링
        print(f"1. 전화번호 필터링 중...")
        initial_count = len(df)

        # 전화번호가 있는 데이터만 선택
        df_filtered = df[df[phone_col] != ''].copy()

        filtered_count = initial_count - len(df_filtered)
        print(f"   - 전화번호 없는 데이터 제거: {filtered_count}개 행")
        print(f"   - 남은 데이터: {len(df_filtered)}개 행")

        # 2. 지역명_매장명 + 전화번호 기준으로 중복 제거
        print(f"\n2. 지역명_매장명 + 전화번호 기준 중복 제거 중...")
        before_dedup = len(df_filtered)

        # 두 컬럼 모두를 기준으로 중복 제거 (첫 번째 항목 유지)
        summary_df = df_filtered.drop_duplicates(subset=[location_store_col, phone_col], keep='first')

        removed_count = before_dedup - len(summary_df)
        print(f"   - 중복 제거: {removed_count}개 행 제거됨")
        print(f"   - 남은 데이터: {len(summary_df)}개 행")

        # 3. 같은 전화번호가 여러 개 있는 경우 지역명_매장명 뒤에 넘버링
        print("\n3. 지역명_매장명 넘버링 중...")

        # 전화번호별로 그룹화하여 카운트
        phone_counts = summary_df[phone_col].value_counts()
        phones_with_multiple = phone_counts[phone_counts > 1].index.tolist()

        if phones_with_multiple:
            # 빈 전화번호 제외
            phones_with_multiple = [p for p in phones_with_multiple if p != '']

            if phones_with_multiple:
                print(f"   - {len(phones_with_multiple)}개의 전화번호가 2개 이상의 매장을 가지고 있습니다.")

                # 각 전화번호에 대해 넘버링
                for phone in phones_with_multiple:
                    # 해당 전화번호를 가진 모든 행 찾기
                    mask = summary_df[phone_col] == phone
                    indices = summary_df[mask].index.tolist()

                    # 넘버링 추가
                    for idx, row_idx in enumerate(indices, 1):
                        original_name = summary_df.loc[row_idx, location_store_col]
                        # 기존 넘버링 제거 (있다면)
                        import re
                        name_without_number = re.sub(r'_\d+$', '', original_name)
                        new_name = f"{name_without_number}_{idx}"
                        summary_df.loc[row_idx, location_store_col] = new_name

                print(f"   - 넘버링 완료")
            else:
                print("   - 중복된 전화번호가 없습니다.")
        else:
            print("   - 중복된 전화번호가 없습니다.")

        print(f"\n가공 완료: 최종 {len(summary_df)}개 행")

        # 4. 필요한 컬럼만 선택 (지역명_매장명, 매장명, 지역명, 전화번호, 링크)
        print("\n4. 필요한 컬럼만 선택 중...")
        summary_df = summary_df[[location_store_col, store_name_col, location_col, phone_col, link_col]]
        print(f"   - 선택된 컬럼: {location_store_col}, {store_name_col}, {location_col}, {phone_col}, {link_col}")

        # 5. 지역명_매장명 기준 내림차순 정렬
        print("\n5. 지역명_매장명 기준 내림차순 정렬 중...")
        summary_df = summary_df.sort_values(by=location_store_col, ascending=False)
        summary_df = summary_df.reset_index(drop=True)
        print(f"   - 정렬 완료")

        # 기존 summary 시트 데이터 확인
        existing_data = summary_worksheet.get_all_values()

        if existing_data and len(existing_data) > 0:
            print(f"\n'{summary_sheet_name}' 워크시트에 기존 데이터가 있습니다.")
            print(f"기존 데이터: {len(existing_data)}개 행 (헤더 포함)")
            print("기존 데이터를 덮어씁니다...")

        # summary 워크시트에 데이터 쓰기
        print(f"\n'{summary_sheet_name}' 워크시트에 데이터 쓰는 중...")

        # 시트 초기화
        summary_worksheet.clear()

        # 헤더 + 데이터 준비
        headers = summary_df.columns.tolist()
        data_rows = summary_df.values.tolist()
        all_data = [headers] + data_rows

        # 데이터 업로드
        summary_worksheet.update(values=all_data, range_name='A1')

        print(f"\n✅ 작업 완료!")
        print(f"   - '{daangn_sheet_name}' 워크시트에서 {len(df)}개 행 읽음")
        print(f"   - '{summary_sheet_name}' 워크시트에 {len(summary_df)}개 행 쓰기 완료")
        print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0")

    except gspread.WorksheetNotFound:
        print(f"❌ '{daangn_sheet_name}' 워크시트를 찾을 수 없습니다.")
        print("워크시트 이름을 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("daangn → summary 데이터 정리 스크립트")
    print("=" * 60)
    print()

    process_daangn_to_summary()
