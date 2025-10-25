"""
지역명_매장명의 지역명 부분을 새로운 지역명으로 교체하는 스크립트
"""

import pandas as pd
import gspread
from google.oauth2 import service_account
from pathlib import Path
import re

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
config_dir = project_root / 'config'


def update_location_store_names():
    """지역명_매장명의 지역명 부분을 업데이트"""

    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    summary_sheet_name = 'summary'

    api_key_file = config_dir / 'google_api_key.json'

    if not api_key_file.exists():
        print(f"❌ 인증 파일을 찾을 수 없습니다: {api_key_file}")
        return

    try:
        print("=" * 80)
        print("지역명_매장명 업데이트")
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
        region_col = None
        location_store_col = None
        store_name_col = None

        for col in df.columns:
            if col == '지역명':
                region_col = col
            elif '지역명_매장명' in col:
                location_store_col = col
            elif col == '매장명':
                store_name_col = col

        if not region_col or not location_store_col or not store_name_col:
            print("❌ 필수 컬럼을 찾을 수 없습니다.")
            return

        print(f"\n컬럼 확인:")
        print(f"  - 지역명: {region_col}")
        print(f"  - 지역명_매장명: {location_store_col}")
        print(f"  - 매장명: {store_name_col}")

        # 지역명_매장명 업데이트
        print("\n지역명_매장명 업데이트 중...")
        updated_count = 0

        for idx, row in df.iterrows():
            region = row[region_col]
            current_location_store = row[location_store_col]
            store_name = row[store_name_col]

            # 지역명_매장명 = 지역명 + "_" + 매장명
            new_location_store = f"{region}_{store_name}"

            # 기존과 다른 경우만 업데이트
            if current_location_store != new_location_store:
                df.at[idx, location_store_col] = new_location_store
                updated_count += 1

                # 처음 20개만 상세 로그 출력
                if updated_count <= 20:
                    print(f"\n[{idx + 1}] 업데이트:")
                    print(f"  이전: {current_location_store}")
                    print(f"  이후: {new_location_store}")

        print(f"\n✓ 총 {updated_count}개 지역명_매장명 업데이트됨")

        if updated_count > 0:
            # 중복 제거 및 넘버링 (전화번호 기준)
            print("\n전화번호 중복 체크 및 넘버링 중...")
            phone_col = None
            for col in df.columns:
                if '전화번호' in col or 'phone' in col.lower():
                    phone_col = col
                    break

            if phone_col:
                # 전화번호별로 그룹화하여 카운트
                phone_counts = df[phone_col].value_counts()
                phones_with_multiple = phone_counts[phone_counts > 1].index.tolist()
                phones_with_multiple = [p for p in phones_with_multiple if p != '']

                if phones_with_multiple:
                    print(f"✓ {len(phones_with_multiple)}개의 전화번호가 여러 매장을 가지고 있습니다.")

                    # 각 전화번호에 대해 넘버링
                    for phone in phones_with_multiple:
                        mask = df[phone_col] == phone
                        indices = df[mask].index.tolist()

                        # 넘버링 추가
                        for idx_num, row_idx in enumerate(indices, 1):
                            original_name = df.loc[row_idx, location_store_col]
                            # 기존 넘버링 제거 (있다면)
                            name_without_number = re.sub(r'_\d+$', '', original_name)
                            new_name = f"{name_without_number}_{idx_num}"
                            df.loc[row_idx, location_store_col] = new_name

                    print(f"✓ 넘버링 완료")
                else:
                    print("✓ 중복된 전화번호가 없습니다.")

            # 지역명_매장명 기준 오름차순 정렬
            print("\n지역명_매장명 기준 오름차순 정렬 중...")
            df = df.sort_values(by=location_store_col, ascending=True)
            df = df.reset_index(drop=True)
            print("✓ 정렬 완료")

            # Summary 시트에 업데이트
            print(f"\n'{summary_sheet_name}' 워크시트에 데이터 쓰는 중...")

            # 시트 초기화
            worksheet.clear()

            # 헤더 + 데이터 준비
            all_data = [df.columns.tolist()] + df.values.tolist()

            # 데이터 업로드
            worksheet.update(values=all_data, range_name='A1')

            print("\n" + "=" * 80)
            print("✅ 작업 완료!")
            print("=" * 80)
            print(f"  - {updated_count}개 지역명_매장명 업데이트됨")
            print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        else:
            print("\n⚠️  업데이트할 데이터가 없습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_location_store_names()
