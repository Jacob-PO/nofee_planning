import gspread
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import os

def download_and_backup():
    """Google Sheets에서 데이터 다운로드 및 백업"""
    
    # Google Sheets 정보
    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    sheet_name = '영업DB'
    
    print("Google Sheets 연결 중...")
    
    # 인증 설정
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    
    creds = service_account.Credentials.from_service_account_file(
        'google_api_key.json', scopes=scope)
    client = gspread.authorize(creds)
    
    # 스프레드시트 열기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    print("데이터 다운로드 중...")
    
    # 모든 데이터 가져오기
    all_data = worksheet.get_all_values()
    
    if not all_data:
        print("시트에 데이터가 없습니다.")
        return
    
    # DataFrame으로 변환
    headers = all_data[0]
    data = all_data[1:]
    df = pd.DataFrame(data, columns=headers)
    
    print(f"다운로드 완료: {len(df)}개의 데이터")
    
    # 백업 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_영업DB_{timestamp}.csv'
    
    # CSV로 저장
    df.to_csv(backup_filename, index=False, encoding='utf-8-sig')
    print(f"백업 완료: {backup_filename}")
    
    # 현재 데이터도 저장
    df.to_csv('current_data.csv', index=False, encoding='utf-8-sig')
    print(f"현재 데이터 저장: current_data.csv")
    
    # 중복 분석
    print("\n중복 분석:")
    print(f"- 전체 데이터: {len(df)}개")
    print(f"- 고유한 주소: {df['주소'].nunique()}개")
    print(f"- 중복된 주소: {len(df) - df['주소'].nunique()}개")
    
    # 가장 많이 중복된 주소 확인
    duplicate_addresses = df['주소'].value_counts()
    duplicates = duplicate_addresses[duplicate_addresses > 1]
    
    if len(duplicates) > 0:
        print(f"\n중복이 가장 많은 주소 TOP 10:")
        for addr, count in duplicates.head(10).items():
            if addr:  # 빈 주소가 아닌 경우만 출력
                print(f"  - {addr}: {count}개")
    
    return df

if __name__ == "__main__":
    download_and_backup()