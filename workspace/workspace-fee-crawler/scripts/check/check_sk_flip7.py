import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets 인증
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('src/config/google_api_key.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# 스프레드시트 열기
sheet = gc.open_by_key('1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4')

print("=== 1. SK_price 시트의 플립7 데이터 확인 ===")
sk_price_worksheet = sheet.worksheet('sk_price')
sk_price_data = sk_price_worksheet.get_all_records()
sk_price_df = pd.DataFrame(sk_price_data)

# SK 플립7 데이터 필터링
sk_flip7_price = sk_price_df[sk_price_df['device_nm'] == '플립7']
print(f"총 {len(sk_flip7_price)}개 행")
if len(sk_flip7_price) > 0:
    print("요금제 컬럼들:")
    for col in sk_price_df.columns:
        if '_' in col and col not in ['date', 'carrier', 'dealer', 'device_nm']:
            print(f"  - {col}")
    # 첫 번째 행의 데이터 확인
    print("\n첫 번째 행 데이터:")
    first_row = sk_flip7_price.iloc[0]
    for col in sk_price_df.columns:
        if '_' in col and col not in ['date', 'carrier', 'dealer', 'device_nm']:
            value = first_row[col]
            if pd.notna(value) and str(value).strip():
                print(f"  {col}: {value}")

print("\n=== 2. Support 시트의 SK 플립7 데이터 확인 ===")
support_worksheet = sheet.worksheet('support')
support_data = support_worksheet.get_all_records()
support_df = pd.DataFrame(support_data)

# SK + 플립7 데이터 필터링
sk_flip7_support = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'].str.contains('플립7|플립 7', na=False))]
print(f"총 {len(sk_flip7_support)}개 행")
if len(sk_flip7_support) > 0:
    print("\n필드별 고유값:")
    print(f"device_nm: {sk_flip7_support['device_nm'].unique()}")
    print(f"storage: {sk_flip7_support['storage'].unique()}")
    print(f"rate_plan_month_fee: {sorted(sk_flip7_support['rate_plan_month_fee'].unique())}")
    
    # rate_plan_month_fee가 109000인 데이터 확인
    flip7_109k = sk_flip7_support[sk_flip7_support['rate_plan_month_fee'] == 109000]
    print(f"\n109k 요금제 데이터: {len(flip7_109k)}개")

print("\n=== 3. Product_group_nm 시트의 플립7 매핑 확인 ===")
pg_worksheet = sheet.worksheet('product_group_nm')
pg_data = pg_worksheet.get_all_records()
pg_df = pd.DataFrame(pg_data)

# 플립7 매핑 찾기
flip7_mapping = pg_df[pg_df['device_nm'] == '플립7']
print(f"총 {len(flip7_mapping)}개 매핑")
if len(flip7_mapping) > 0:
    print("매핑 정보:")
    for idx, row in flip7_mapping.iterrows():
        print(f"  - device_nm: '{row['device_nm']}' -> product_group_nm: '{row['product_group_nm']}', storage: '{row['storage']}'")

print("\n=== 4. 불일치 원인 분석 ===")
if len(flip7_mapping) > 0 and len(sk_flip7_support) > 0:
    # product_group_nm으로 support 데이터 필터링
    pg_name = flip7_mapping.iloc[0]['product_group_nm']
    pg_storage = flip7_mapping.iloc[0]['storage']
    
    # Support에서 해당 product_group_nm 찾기 (device_nm 대신)
    support_by_pg = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'] == pg_name)]
    print(f"\nSupport 시트에서 product_group_nm='{pg_name}' 검색 결과: {len(support_by_pg)}개")
    
    if len(support_by_pg) > 0:
        # storage와 109k 요금제 확인
        matching_support = support_by_pg[(support_by_pg['storage'] == pg_storage) & (support_by_pg['rate_plan_month_fee'] == 109000)]
        print(f"storage='{pg_storage}' AND rate_plan_month_fee=109000 매칭: {len(matching_support)}개")
        
        # storage 값 비교
        print(f"\nStorage 값 비교:")
        print(f"  - product_group_nm 시트의 storage: '{pg_storage}'")
        print(f"  - Support 시트의 storage 값들: {support_by_pg['storage'].unique()}")