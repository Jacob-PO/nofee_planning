"""
Find Galaxy Z Fold 7 data in Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import pandas as pd

# Google Sheets 설정
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"
CREDENTIALS_DIR = "/Users/jacob_athometrip/Desktop/dev/nofee/workspace_nofee/config"

# Google Sheets 연결 설정
possible_paths = [
    Path(CREDENTIALS_DIR) / 'google_api_key.json',
    Path(CREDENTIALS_DIR) / 'google-sheets-key.json',
    Path(CREDENTIALS_DIR) / 'service_account_key.json',
]

# 존재하는 첫 번째 파일 사용
credentials_path = None
for path in possible_paths:
    if path.exists():
        credentials_path = str(path)
        print(f"사용할 credentials 파일: {credentials_path}")
        break

if not credentials_path:
    raise FileNotFoundError(f"Google Sheets credentials 파일을 찾을 수 없습니다.")

# Google Sheets 연결
scope = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# 모든 시트 가져오기
all_worksheets = spreadsheet.worksheets()
print(f"총 {len(all_worksheets)}개의 시트가 있습니다.\n")

# 각 시트 탐색
for worksheet in all_worksheets:
    print(f"=== 시트: {worksheet.title} (ID: {worksheet.id}) ===")
    
    try:
        # 시트 데이터 가져오기
        all_data = worksheet.get_all_values()
        
        if len(all_data) > 0:
            headers = all_data[0]
            print(f"컬럼: {headers}")
            
            # device_nm, storage, release_price 컬럼이 있는지 확인
            has_device_nm = 'device_nm' in headers
            has_storage = 'storage' in headers
            has_release_price = 'release_price' in headers
            
            if has_device_nm or has_storage or has_release_price:
                print(f"✓ 관련 컬럼 발견! - device_nm: {has_device_nm}, storage: {has_storage}, release_price: {has_release_price}")
                
                # 데이터를 DataFrame으로 변환
                if len(all_data) > 1:
                    df = pd.DataFrame(all_data[1:], columns=headers)
                    
                    # 갤럭시 Z 폴드 관련 데이터 찾기
                    if 'device_nm' in df.columns:
                        galaxy_fold_data = df[df['device_nm'].str.contains('갤럭시 Z 폴드|Galaxy Z Fold|Z Fold', case=False, na=False)]
                        
                        if len(galaxy_fold_data) > 0:
                            print(f"\n★★★ 갤럭시 Z 폴드 데이터 발견! {len(galaxy_fold_data)}개 ★★★")
                            print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
                            
                            # 데이터 샘플 출력
                            for idx, row in galaxy_fold_data.head(10).iterrows():
                                print(f"\n기기명: {row.get('device_nm', 'N/A')}")
                                if 'storage' in row:
                                    print(f"저장용량: {row['storage']}")
                                if 'release_price' in row:
                                    print(f"출고가: {row['release_price']}")
                                if 'product_group_nm' in row:
                                    print(f"제품그룹: {row['product_group_nm']}")
                                # 다른 관련 컬럼도 출력
                                for col in headers:
                                    if col not in ['device_nm', 'storage', 'release_price', 'product_group_nm'] and row.get(col):
                                        print(f"{col}: {row[col]}")
                        else:
                            # 다른 이름으로 저장되어 있을 수 있으니 Z Fold로 검색
                            for col in df.columns:
                                fold_data = df[df[col].astype(str).str.contains('Z 폴드|Z Fold|폴드7|Fold 7', case=False, na=False)]
                                if len(fold_data) > 0:
                                    print(f"\n☆ {col} 컬럼에서 Z 폴드 관련 데이터 발견! {len(fold_data)}개")
                                    print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
                                    for idx, row in fold_data.head(5).iterrows():
                                        print(f"  - {col}: {row[col]}")
                                    break
            
            print(f"총 행 수: {len(all_data)} (헤더 포함)\n")
        else:
            print("시트가 비어있습니다.\n")
            
    except Exception as e:
        print(f"에러 발생: {str(e)}\n")

print("\n검색 완료!")