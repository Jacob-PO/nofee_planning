"""
support 시트 정제 및 support_summary 시트 업로드

정제 과정:
1. support 시트에서 데이터 다운로드
2. total_support_fee가 0원인 행 제외
3. 각 기기별로 carrier, scrb_type_name, rate_plan_month_fee가 같은 경우,
   public_support_fee가 가장 높은 1개만 남김
4. product_group_nm 시트에서 device_nm을 매핑하여 product_group_nm, storage 추가
5. 매핑되지 않은 행 제거
6. storage, support_type 칼럼 삭제
7. support_summary 시트에 업로드

Author: Claude Code
Created: 2025-10-07
"""
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
from pathlib import Path


class SupportSheetCleaner:
    def __init__(self, credentials_path='./src/config/google_api_key.json'):
        """
        support 시트 정제 클래스 초기화

        Args:
            credentials_path (str): Google API 인증 파일 경로
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = '1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4'
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']

        # 결과 저장 디렉토리
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Google Sheets API 서비스 초기화
        self.service = self._init_service()

    def _init_service(self):
        """Google Sheets API 서비스 초기화"""
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes)
        return build('sheets', 'v4', credentials=credentials)

    def download_sheet(self, sheet_name):
        """
        구글 시트에서 데이터 다운로드

        Args:
            sheet_name (str): 시트 이름

        Returns:
            pd.DataFrame: 다운로드된 데이터프레임
        """
        print(f"{sheet_name} 시트 다운로드 중...")
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f'{sheet_name}!A:ZZ'
        ).execute()

        values = result.get('values', [])

        if not values:
            raise ValueError(f"{sheet_name} 시트에 데이터가 없습니다.")

        df = pd.DataFrame(values[1:], columns=values[0])
        print(f"✅ {sheet_name} 시트 다운로드 완료: {len(df)} 행")
        return df

    def filter_zero_support_fee(self, df):
        """
        total_support_fee가 0원인 행 제외

        Args:
            df (pd.DataFrame): 원본 데이터프레임

        Returns:
            pd.DataFrame: 필터링된 데이터프레임
        """
        print("\ntotal_support_fee 필터링 중...")
        original_count = len(df)

        # total_support_fee를 숫자로 변환
        df['total_support_fee'] = pd.to_numeric(df['total_support_fee'], errors='coerce').fillna(0)

        # 0보다 큰 값만 남김
        df = df[df['total_support_fee'] > 0]

        removed_count = original_count - len(df)
        print(f"✅ total_support_fee = 0 제거: {removed_count} 행 제거, {len(df)} 행 남음")

        return df

    def deduplicate_data(self, df):
        """
        중복 데이터 제거
        각 기기별로 carrier, scrb_type_name, rate_plan_month_fee가 같은 경우,
        public_support_fee가 가장 높은 1개만 남김

        Args:
            df (pd.DataFrame): 원본 데이터프레임

        Returns:
            pd.DataFrame: 중복 제거된 데이터프레임
        """
        print("\n중복 데이터 제거 중...")
        original_count = len(df)

        # public_support_fee를 숫자로 변환
        df['public_support_fee'] = pd.to_numeric(df['public_support_fee'], errors='coerce').fillna(0)

        # 정렬: device_nm, carrier, scrb_type_name, rate_plan_month_fee, public_support_fee (내림차순)
        df = df.sort_values(
            by=['device_nm', 'carrier', 'scrb_type_name', 'rate_plan_month_fee', 'public_support_fee'],
            ascending=[True, True, True, True, False]
        )

        # 그룹핑하여 첫 번째 값만 유지 (public_support_fee가 가장 높은 값)
        df = df.groupby(
            ['device_nm', 'carrier', 'scrb_type_name', 'rate_plan_month_fee'],
            as_index=False
        ).first()

        removed_count = original_count - len(df)
        print(f"✅ 중복 제거 완료: {removed_count} 행 제거, {len(df)} 행 남음")

        return df

    def map_product_group(self, support_df, product_df):
        """
        product_group_nm 시트에서 device_nm을 매핑

        Args:
            support_df (pd.DataFrame): support 데이터프레임
            product_df (pd.DataFrame): product_group_nm 데이터프레임

        Returns:
            pd.DataFrame: 매핑된 데이터프레임
        """
        print("\nproduct_group_nm 매핑 중...")
        original_count = len(support_df)

        # product_group_nm 시트에서 필요한 컬럼만 추출
        mapping_df = product_df[['device_nm', 'product_group_nm', 'storage']].copy()

        # device_nm 기준으로 중복 제거 (첫 번째 값 사용)
        mapping_df = mapping_df.drop_duplicates(subset='device_nm', keep='first')

        # 매핑
        support_df = support_df.merge(
            mapping_df,
            on='device_nm',
            how='left',
            suffixes=('_old', '')
        )

        # 매핑되지 않은 행 제거
        support_df = support_df[support_df['product_group_nm'].notna()]
        support_df = support_df[support_df['product_group_nm'] != '']

        removed_count = original_count - len(support_df)
        print(f"✅ 매핑 완료: {removed_count} 행 제거 (매핑 안됨), {len(support_df)} 행 남음")

        return support_df

    def finalize_columns(self, df):
        """
        최종 칼럼 정리
        storage_old, support_type 제거

        Args:
            df (pd.DataFrame): 데이터프레임

        Returns:
            pd.DataFrame: 정리된 데이터프레임
        """
        print("\n최종 칼럼 정리 중...")

        final_columns = [
            'date',
            'crawled_at',
            'carrier',
            'manufacturer',
            'scrb_type_name',
            'network_type',
            'device_nm',
            'rate_plan',
            'rate_plan_month_fee',
            'release_price',
            'public_support_fee',
            'additional_support_fee',
            'total_support_fee',
            'total_price',
            'product_group_nm',
            'storage'
        ]

        df = df[final_columns]
        print(f"✅ 최종 칼럼 수: {len(final_columns)}개")

        return df

    def save_to_local(self, df):
        """
        로컬에 CSV 파일로 저장

        Args:
            df (pd.DataFrame): 저장할 데이터프레임

        Returns:
            str: 저장된 파일 경로
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = self.results_dir / f'support_summary_{timestamp}.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ 로컬 저장: {csv_file}")
        return str(csv_file)

    def upload_to_sheet(self, df, sheet_name='support_summary'):
        """
        구글 시트에 데이터 업로드

        Args:
            df (pd.DataFrame): 업로드할 데이터프레임
            sheet_name (str): 업로드할 시트 이름
        """
        print(f"\n{sheet_name} 시트에 업로드 중...")

        # 데이터를 2차원 리스트로 변환
        values = [df.columns.tolist()]
        for _, row in df.iterrows():
            row_values = [str(val) for val in row]
            values.append(row_values)

        # 시트 클리어
        self.service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=f"{sheet_name}!A:ZZ"
        ).execute()

        # 새 데이터 쓰기
        body = {'values': values}
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

        print(f"✅ 업로드 완료: {result.get('updatedCells')}개 셀 업데이트")
        print(f"✅ 업로드 범위: {result.get('updatedRange')}")

    def clean(self):
        """
        전체 정제 과정 실행
        """
        print("=" * 60)
        print("support 시트 정제 프로세스 시작")
        print("=" * 60)

        # 1. support 시트 다운로드
        support_df = self.download_sheet('support')

        # 2. product_group_nm 시트 다운로드
        product_df = self.download_sheet('product_group_nm')

        # 3. total_support_fee가 0원인 행 제외
        support_df = self.filter_zero_support_fee(support_df)

        # 4. 중복 데이터 제거
        support_df = self.deduplicate_data(support_df)

        # 5. product_group_nm 매핑
        support_df = self.map_product_group(support_df, product_df)

        # 6. 최종 칼럼 정리
        support_df = self.finalize_columns(support_df)

        # 7. 로컬 저장
        self.save_to_local(support_df)

        # 8. support_summary 시트에 업로드
        self.upload_to_sheet(support_df, 'support_summary')

        print("\n" + "=" * 60)
        print("✅ 정제 프로세스 완료!")
        print(f"✅ 최종 데이터: {len(support_df)} 행, {len(support_df.columns)}개 칼럼")
        print(f"✅ 스프레드시트: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid=374383555")
        print("=" * 60)

        return support_df


def main():
    """메인 실행 함수"""
    try:
        cleaner = SupportSheetCleaner()
        cleaner.clean()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
