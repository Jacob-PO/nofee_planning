"""Support 시트에서 Z플립7, Z폴드7 출고가 일괄 수정"""


import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import glob

# Google Sheets 인증 설정
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 스프레드시트 ID
SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"

def get_credentials():
    """Google Sheets 인증 파일 찾기"""
    credentials_dir = "src/config"
    json_files = glob.glob(os.path.join(credentials_dir, "*.json"))
    
    if not json_files:
        raise FileNotFoundError("Google Sheets API 키 파일을 찾을 수 없습니다.")
    
    credentials_file = json_files[0]
    print(f"사용할 credentials 파일: {credentials_file}")
    
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)

def update_flip7_fold7_prices():
    """Z플립7, Z폴드7 출고가 수정"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("support")
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        
        # release_price 컬럼 인덱스 찾기
        try:
            price_col_idx = headers.index('release_price')
        except ValueError:
            print("❌ 'release_price' 컬럼을 찾을 수 없습니다.")
            return
            
        # device_nm 컬럼 인덱스 찾기
        try:
            device_col_idx = headers.index('device_nm')
        except ValueError:
            print("❌ 'device_nm' 컬럼을 찾을 수 없습니다.")
            return
        
        # 수정 통계
        flip7_count = 0
        fold7_count = 0
        
        # 배치 업데이트를 위한 리스트
        updates = []
        
        print("Support 시트 분석 중...")
        
        for i, row in enumerate(all_values):
            if i == 0:  # 헤더 스킵
                continue
                
            device_nm = row[device_col_idx]
            
            # Z플립7 확인 (대소문자 구분 없이)
            if '플립' in device_nm and '7' in device_nm:
                # Z플립7 FE가 아닌 일반 플립7만
                if 'FE' not in device_nm.upper():
                    cell_address = f'{chr(65 + price_col_idx)}{i+1}'
                    updates.append({
                        'range': cell_address,
                        'values': [['1485000']]
                    })
                    flip7_count += 1
                    
            # Z폴드7 확인
            elif '폴드' in device_nm and '7' in device_nm:
                cell_address = f'{chr(65 + price_col_idx)}{i+1}'
                updates.append({
                    'range': cell_address,
                    'values': [['2379300']]
                })
                fold7_count += 1
        
        # 배치 업데이트 실행
        if updates:
            print(f"\n수정 대상:")
            print(f"  - Z플립7: {flip7_count}개")
            print(f"  - Z폴드7: {fold7_count}개")
            print(f"  총 {len(updates)}개 셀 수정 중...")
            
            # 100개씩 나누어 업데이트 (Google Sheets API 제한)
            batch_size = 100
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                worksheet.batch_update(batch)
                print(f"  {i+1}~{min(i+batch_size, len(updates))}번째 업데이트 완료")
            
            print(f"\n✅ 수정 완료:")
            print(f"  - Z플립7: {flip7_count}개 → 1,485,000원")
            print(f"  - Z폴드7: {fold7_count}개 → 2,379,300원")
        else:
            print("수정할 데이터가 없습니다.")
                    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("Z플립7, Z폴드7 출고가 수정 시작...")
    update_flip7_fold7_prices()
    print("\n완료!")