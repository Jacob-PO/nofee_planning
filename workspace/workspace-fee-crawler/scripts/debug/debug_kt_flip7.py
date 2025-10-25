"""KT 플립7 매칭 문제 디버깅"""

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

def debug_kt_flip7():
    """KT 플립7 매칭 디버깅"""
    try:
        # Google Sheets 연결
        gc = get_credentials()
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # 1. KT_price 데이터 확인
        print("=== 1. KT_price 시트 확인 ===")
        kt_price_df = pd.DataFrame(sheet.worksheet("kt_price").get_all_records())
        kt_price_df['carrier'] = 'KT'
        
        flip7_prices = kt_price_df[kt_price_df['device_nm'] == '플립7']
        print(f"\nKT_price에서 '플립7' 데이터: {len(flip7_prices)}개")
        if len(flip7_prices) > 0:
            print("컬럼 목록:", list(flip7_prices.columns))
            # 110k 요금제 관련 컬럼 찾기
            for col in flip7_prices.columns:
                if '110k' in col:
                    values = flip7_prices[col].dropna()
                    if len(values) > 0:
                        print(f"  {col}: {values.iloc[0]}")
        
        # 2. Product_group_nm 매핑 확인
        print("\n=== 2. Product_group_nm 매핑 확인 ===")
        pg_df = pd.DataFrame(sheet.worksheet("product_group_nm").get_all_records())
        flip7_mapping = pg_df[pg_df['device_nm'] == '플립7']
        print(f"'플립7' 매핑: {flip7_mapping.iloc[0]['device_nm']} -> {flip7_mapping.iloc[0]['product_group_nm']} ({flip7_mapping.iloc[0]['storage']})")
        
        # 3. Support 데이터 확인
        print("\n=== 3. Support 시트 확인 ===")
        support_df = pd.DataFrame(sheet.worksheet("support").get_all_records())
        
        # KT + 갤럭시 Z 플립 7 + 256GB + 110k 데이터 찾기
        kt_flip7_support = support_df[
            (support_df['carrier'] == 'KT') & 
            (support_df['device_nm'].str.contains('플립.*7', case=False, na=False)) &
            (support_df['storage'] == '256GB') &
            (support_df['rate_plan_month_fee'] == '110000')
        ]
        
        print(f"\nKT + 플립7 + 256GB + 110k Support 데이터: {len(kt_flip7_support)}개")
        if len(kt_flip7_support) > 0:
            sample = kt_flip7_support.iloc[0]
            print(f"  device_nm: '{sample['device_nm']}'")
            print(f"  product_group_nm 매핑 대상: '갤럭시 Z 플립 7'")
            print(f"  storage: {sample['storage']}")
            print(f"  rate_plan: {sample['rate_plan']}")
            print(f"  support_type: {sample.get('support_type', 'N/A')}")
            
        # 4. 매칭 프로세스 시뮬레이션
        print("\n=== 4. 매칭 프로세스 시뮬레이션 ===")
        
        # device_to_product_info 생성
        device_to_product_info = {}
        for _, row in pg_df.iterrows():
            device_nm = str(row.get('device_nm', ''))
            product_group_nm = str(row.get('product_group_nm', ''))
            storage = str(row.get('storage', ''))
            device_to_product_info[device_nm] = (product_group_nm, storage)
        
        # Support 데이터를 product_group_nm별로 그룹화
        support_by_product_group = {}
        for _, support_row in support_df[support_df['carrier'] == 'KT'].iterrows():
            support_device_nm = support_row.get('device_nm', '')
            carrier = support_row.get('carrier', '')
            
            # 이 Support device_nm이 어떤 product_group_nm에 속하는지 찾기
            if support_device_nm in device_to_product_info:
                matched_product_group, mapped_storage = device_to_product_info[support_device_nm]
                
                # Support 데이터를 복사하고 매핑된 storage 추가
                support_row_copy = support_row.copy()
                support_row_copy['mapped_storage'] = mapped_storage
                support_row_copy['mapped_product_group_nm'] = matched_product_group
                
                key = (carrier, matched_product_group)
                if key not in support_by_product_group:
                    support_by_product_group[key] = []
                support_by_product_group[key].append(support_row_copy)
        
        # 플립7 매칭 확인
        key = ('KT', '갤럭시 Z 플립 7')
        if key in support_by_product_group:
            supports = support_by_product_group[key]
            print(f"\n('KT', '갤럭시 Z 플립 7') 그룹의 Support 데이터: {len(supports)}개")
            
            # 110k + 256GB 매칭 찾기
            matches_110k_256gb = [s for s in supports if s.get('rate_plan_month_fee') == '110000' and s.get('mapped_storage') == '256GB']
            print(f"  - 110k + 256GB 매칭: {len(matches_110k_256gb)}개")
            
            if len(matches_110k_256gb) > 0:
                print("  첫 번째 매칭:")
                s = matches_110k_256gb[0]
                print(f"    device_nm: '{s.get('device_nm')}'")
                print(f"    mapped_storage: {s.get('mapped_storage')}")
                print(f"    original storage: {s.get('storage')}")
        else:
            print(f"\n('KT', '갤럭시 Z 플립 7') 그룹이 support_by_product_group에 없습니다!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    debug_kt_flip7()