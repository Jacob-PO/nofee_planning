"""
Google Sheets 업로드 모듈
수집한 데이터를 구글 시트에 자동으로 업로드
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime


class GoogleSheetsUploader:
    def __init__(self, credentials_file='credentials.json'):
        """
        Google Sheets 연결 초기화

        Args:
            credentials_file: 서비스 계정 인증 JSON 파일 경로
        """
        self.credentials_file = credentials_file
        self.client = None
        self.sheet = None

    def connect(self):
        """Google Sheets API 연결"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file,
                scope
            )
            self.client = gspread.authorize(creds)
            print("✓ Google Sheets API 연결 성공")
            return True

        except FileNotFoundError:
            print(f"❌ 인증 파일을 찾을 수 없습니다: {self.credentials_file}")
            print("\n인증 파일 생성 방법:")
            print("1. https://console.cloud.google.com/ 접속")
            print("2. 프로젝트 생성 또는 선택")
            print("3. API 및 서비스 > 사용자 인증 정보")
            print("4. 서비스 계정 만들기")
            print("5. JSON 키 다운로드 후 'credentials.json'으로 저장")
            return False

        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False

    def open_sheet(self, spreadsheet_url, worksheet_name='naver'):
        """
        스프레드시트 열기

        Args:
            spreadsheet_url: 구글 시트 URL 또는 ID
            worksheet_name: 워크시트 이름 (기본값: 'naver')
        """
        try:
            # URL에서 스프레드시트 ID 추출
            if 'docs.google.com' in spreadsheet_url:
                sheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = spreadsheet_url

            # 스프레드시트 열기
            spreadsheet = self.client.open_by_key(sheet_id)

            # 워크시트 가져오기 또는 생성
            try:
                self.sheet = spreadsheet.worksheet(worksheet_name)
                print(f"✓ '{worksheet_name}' 시트 열기 성공")
            except gspread.WorksheetNotFound:
                self.sheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=10
                )
                print(f"✓ '{worksheet_name}' 시트 생성 완료")

            return True

        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ 스프레드시트를 찾을 수 없습니다.")
            print("서비스 계정 이메일에 시트 편집 권한을 부여했는지 확인하세요.")
            return False

        except Exception as e:
            print(f"❌ 시트 열기 오류: {e}")
            return False

    def append_data(self, data_list):
        """
        데이터를 시트 끝에 추가 (계속 쌓아나가기)

        Args:
            data_list: 추가할 데이터 리스트 (DataFrame 또는 리스트)
        """
        if not self.sheet:
            print("❌ 시트가 연결되지 않았습니다.")
            return False

        try:
            # DataFrame을 리스트로 변환
            if isinstance(data_list, pd.DataFrame):
                # 헤더 확인
                existing_data = self.sheet.get_all_values()

                if len(existing_data) == 0:
                    # 빈 시트면 헤더 추가
                    headers = data_list.columns.tolist()
                    self.sheet.append_row(headers)
                    print(f"✓ 헤더 추가: {headers}")

                # 데이터 변환
                data_list = data_list.values.tolist()

            # 데이터 추가 (일괄 업로드로 API 호출 최소화)
            if data_list:
                # 기존 데이터 행 수 확인
                last_row = len(self.sheet.get_all_values())

                # 일괄 업데이트 (한 번의 API 호출)
                start_cell = f'A{last_row + 1}'
                self.sheet.append_rows(data_list, value_input_option='RAW')

                print(f"✓ {len(data_list)}개 행 추가 완료")
                return True
            else:
                print("⚠️  추가할 데이터가 없습니다.")
                return False

        except Exception as e:
            print(f"❌ 데이터 추가 오류: {e}")
            return False

    def upload_dataframe(self, df, append_mode=True):
        """
        DataFrame을 시트에 업로드

        Args:
            df: 업로드할 DataFrame
            append_mode: True면 기존 데이터에 추가, False면 덮어쓰기
        """
        if not self.sheet:
            print("❌ 시트가 연결되지 않았습니다.")
            return False

        try:
            if append_mode:
                # 추가 모드
                return self.append_data(df)
            else:
                # 덮어쓰기 모드
                self.sheet.clear()

                # 헤더 + 데이터
                headers = df.columns.tolist()
                data = df.values.tolist()

                all_data = [headers] + data
                self.sheet.update('A1', all_data)

                print(f"✓ {len(df)}개 행 업로드 완료 (덮어쓰기)")
                return True

        except Exception as e:
            print(f"❌ 업로드 오류: {e}")
            return False

    def get_existing_links(self, link_column='링크'):
        """
        시트에 이미 존재하는 링크 목록 가져오기 (중복 방지용)

        Args:
            link_column: 링크가 있는 컬럼명

        Returns:
            set: 기존 링크 집합
        """
        if not self.sheet:
            return set()

        try:
            data = self.sheet.get_all_records()
            if not data:
                return set()

            existing_links = {row.get(link_column, '') for row in data if row.get(link_column)}
            print(f"✓ 기존 데이터 {len(existing_links)}개 확인")
            return existing_links

        except Exception as e:
            print(f"⚠️  기존 데이터 확인 실패: {e}")
            return set()


def main():
    """테스트 코드"""
    # 업로더 초기화
    uploader = GoogleSheetsUploader('credentials.json')

    # 연결
    if not uploader.connect():
        return

    # 시트 열기
    sheet_url = "https://docs.google.com/spreadsheets/d/1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo/edit"
    if not uploader.open_sheet(sheet_url, 'naver'):
        return

    # 테스트 데이터
    test_data = pd.DataFrame([
        {
            '지역명': '서울 강남구',
            '매장명': '테스트매장',
            '지역명_매장명': '서울 강남구_테스트매장',
            '링크': 'https://test.com/123',
            '출처': 'test',
            '제목': '테스트 제목'
        }
    ])

    # 업로드
    uploader.upload_dataframe(test_data, append_mode=True)

    print("\n✓ 테스트 완료!")


if __name__ == "__main__":
    main()
