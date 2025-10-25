"""
스프레드시트의 모든 시트 이름 확인
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 설정
SPREADSHEET_ID = '1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4'
SERVICE_ACCOUNT_FILE = './src/config/google_api_key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# 인증
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# 스프레드시트 메타데이터 가져오기
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

print("=" * 80)
print("스프레드시트의 모든 시트 목록")
print("=" * 80)

sheets = spreadsheet.get('sheets', [])
for i, sheet in enumerate(sheets, 1):
    properties = sheet.get('properties', {})
    sheet_id = properties.get('sheetId')
    sheet_name = properties.get('title')
    print(f"{i}. {sheet_name} (ID: {sheet_id})")

print("\n총 시트 수:", len(sheets))
