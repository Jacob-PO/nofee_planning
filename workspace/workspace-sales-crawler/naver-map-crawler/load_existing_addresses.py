import pandas as pd
import gspread
from google.oauth2 import service_account

def load_existing_addresses():
    """Google Sheets에서 현재 주소 목록 가져오기"""
    
    print("Google Sheets에서 현재 데이터 로드 중...")
    
    # Google Sheets 정보
    spreadsheet_id = '1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo'
    sheet_name = '영업DB'
    
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
    
    # 모든 데이터 가져오기
    all_data = worksheet.get_all_values()
    
    if not all_data:
        print("시트에 데이터가 없습니다.")
        return set()
    
    # DataFrame으로 변환
    headers = all_data[0]
    data = all_data[1:]
    df = pd.DataFrame(data, columns=headers)
    
    # 주소 목록 추출 (빈 값 제외)
    addresses = df['주소'][df['주소'] != ''].tolist()
    unique_addresses = set(addresses)
    
    print(f"로드 완료: {len(unique_addresses)}개의 고유한 주소")
    
    # 주소 목록을 파일로 저장
    with open('existing_addresses.txt', 'w', encoding='utf-8') as f:
        for addr in sorted(unique_addresses):
            f.write(addr + '\n')
    
    print("existing_addresses.txt 파일에 저장됨")
    
    return unique_addresses

if __name__ == "__main__":
    existing_addresses = load_existing_addresses()