import pandas as pd
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent
results_dir = project_root / 'results'
api_keys_dir = project_root / 'api_keys'

def upload_to_google_sheets_with_api_key():
    """Google Sheets API를 사용한 직접 업로드"""

    # CSV 파일 읽기
    csv_file = results_dir / 'naver_map_results.csv'
    df = pd.read_csv(csv_file)
    
    # 웹사이트 컬럼이 없으면 추가 (기존 데이터와의 호환성을 위해)
    if '웹사이트' not in df.columns:
        # 블로그리뷰 다음에 웹사이트 컬럼 추가
        cols = df.columns.tolist()
        idx = cols.index('블로그리뷰') + 1
        cols.insert(idx, '웹사이트')
        df = df.reindex(columns=cols, fill_value='')
    
    # NaN 값을 빈 문자열로 변환
    df = df.fillna('')
    
    print("데이터 로드 완료:")
    print(f"- 총 {len(df)}개의 매장 정보")
    
    # Google Sheets 정보
    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    sheet_name = '영업DB'
    
    # 인증 파일 경로
    api_key_file = api_keys_dir / 'google_api_key.json'

    try:
        # 서비스 계정 인증 정보가 있는 경우
        if api_key_file.exists():
            print("\n서비스 계정 인증 파일을 사용하여 연결 중...")

            # 인증 설정
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/spreadsheets',
                     'https://www.googleapis.com/auth/drive']

            creds = service_account.Credentials.from_service_account_file(
                str(api_key_file), scopes=scope)
            client = gspread.authorize(creds)
            
            # 스프레드시트 열기
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # 현재 시트의 크기 확인
            row_count = worksheet.row_count
            print(f"현재 시트 크기: {row_count}행")
            
            # 필요한 경우 행 추가
            all_values = worksheet.get_all_values()
            current_rows = len(all_values) if all_values else 0
            new_data_rows = len(df)
            required_rows = current_rows + new_data_rows + 100  # 여유분 100행
            
            if required_rows > row_count:
                worksheet.add_rows(required_rows - row_count)
                print(f"시트 크기 확장: {row_count}행 → {required_rows}행")
            
            # 기존 데이터 가져오기 (헤더 포함)
            try:
                all_values = worksheet.get_all_values()
                
                if all_values:
                    # 첫 번째 행이 헤더인지 확인
                    has_header = False
                    if all_values[0][0] == '크롤링날짜' or all_values[0][0] == '﻿크롤링날짜':
                        has_header = True
                        existing_data_rows = all_values[1:]  # 헤더 제외
                        print(f"기존 데이터: {len(existing_data_rows)}개 행 (헤더 제외)")
                    else:
                        existing_data_rows = all_values
                        print(f"기존 데이터: {len(existing_data_rows)}개 행")
                    
                    # 마지막으로 데이터가 있는 행 번호 찾기
                    last_row = len(all_values) + 1
                    
                    # 새 데이터를 리스트 형태로 준비 (헤더 없이)
                    new_data = df.values.tolist()
                    
                    # 새 데이터를 기존 데이터 하단에 추가
                    if new_data:
                        range_name = f'A{last_row}'
                        worksheet.update(values=new_data, range_name=range_name)
                        print(f"\n✅ Google Sheets에 {len(new_data)}개 행 추가 완료!")
                        print(f"   - 추가 위치: 행 {last_row}부터")
                else:
                    # 시트가 비어있는 경우 헤더와 함께 추가
                    print("시트가 비어있습니다. 헤더와 함께 데이터 추가...")
                    data = [df.columns.tolist()] + df.values.tolist()
                    worksheet.update(values=data, range_name='A1')
                    print(f"\n✅ 첫 번째 업로드 완료! (헤더 포함)")
                    
            except Exception as e:
                print(f"데이터 추가 중 오류: {e}")
                # 오류 발생시 전체 업데이트
                data = [df.columns.tolist()] + df.values.tolist()
                worksheet.clear()
                worksheet.update(values=data, range_name='A1')
            
            print(f"\n✅ Google Sheets 업로드 성공!")
            print(f"   - 시트: {sheet_name}")
            print(f"   - 데이터: {len(df)}개 행")
            print(f"\n확인하기: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0")
            
        else:
            print("\n⚠️  서비스 계정 인증 파일(google_api_key.json)이 없습니다.")
            print("\nGoogle Sheets API 사용을 위한 설정 방법:")
            print("="*60)
            print("1. Google Cloud Console 접속: https://console.cloud.google.com")
            print("2. 새 프로젝트 생성 또는 기존 프로젝트 선택")
            print("3. 'API 및 서비스' > '라이브러리'에서 Google Sheets API 활성화")
            print("4. '사용자 인증 정보' > '서비스 계정' 생성")
            print("5. 서비스 계정의 JSON 키 파일을 'credentials.json'으로 저장")
            print("6. Google Sheets에서 서비스 계정 이메일에 편집 권한 부여")
            print("="*60)
            
            # 대체 방법 제공
            print("\n대체 방법: 수동 복사")
            print("1. google_sheets_upload.tsv 파일을 메모장으로 열기")
            print("2. 전체 내용 복사 (Ctrl+A, Ctrl+C)")
            print("3. Google Sheets 열기")
            print("4. A1 셀에 붙여넣기 (Ctrl+V)")
            
    except Exception as e:
        print(f"\n❌ 업로드 실패: {e}")
        print("\n수동으로 업로드하려면:")
        print("1. google_sheets_upload.tsv 파일 사용")
        print("2. Google Sheets에 직접 붙여넣기")

def create_service_account_guide():
    """서비스 계정 생성 가이드"""
    guide = """
# Google Sheets API 서비스 계정 설정 가이드

## 1. Google Cloud Console 설정
1. https://console.cloud.google.com 접속
2. 프로젝트 생성 또는 선택
3. 'API 및 서비스' > '라이브러리' 메뉴
4. 'Google Sheets API' 검색 후 활성화

## 2. 서비스 계정 생성
1. 'API 및 서비스' > '사용자 인증 정보'
2. '+ 사용자 인증 정보 만들기' > '서비스 계정'
3. 서비스 계정 이름 입력 (예: sheets-uploader)
4. '만들기 및 계속'
5. 역할: '편집자' 선택
6. '완료'

## 3. 키 파일 생성
1. 생성된 서비스 계정 클릭
2. '키' 탭 > '키 추가' > '새 키 만들기'
3. JSON 선택 > '만들기'
4. 다운로드된 파일을 'credentials.json'으로 저장

## 4. Google Sheets 권한 부여
1. 서비스 계정 이메일 복사 (xxxxx@xxxxx.iam.gserviceaccount.com)
2. Google Sheets 문서 열기
3. '공유' 버튼 클릭
4. 서비스 계정 이메일 추가
5. '편집자' 권한 부여
"""
    
    with open('google_api_setup_guide.txt', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("📄 설정 가이드가 'google_api_setup_guide.txt'에 저장되었습니다.")

if __name__ == "__main__":
    print("Google Sheets 업로더")
    print("="*60)

    # 데이터 파일 확인
    csv_file = results_dir / 'naver_map_results.csv'
    if not csv_file.exists():
        print(f"❌ {csv_file} 파일이 없습니다.")
        print("먼저 크롤러를 실행하여 데이터를 수집하세요.")
    else:
        # 업로드 시도
        upload_to_google_sheets_with_api_key()
        
        # 가이드 생성
        if not os.path.exists('credentials.json'):
            print("\n")
            create_service_account_guide()