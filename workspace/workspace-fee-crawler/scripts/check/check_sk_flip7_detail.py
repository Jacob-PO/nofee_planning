import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets 인증
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('src/config/google_api_key.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# 스프레드시트 열기
sheet = gc.open_by_key('1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4')

print("=== SK 플립7 관련 매핑 문제 상세 분석 ===\n")

# 1. product_group_nm 시트
pg_worksheet = sheet.worksheet('product_group_nm')
pg_data = pg_worksheet.get_all_records()
pg_df = pd.DataFrame(pg_data)

flip7_mapping = pg_df[pg_df['device_nm'] == '플립7']
print("1. product_group_nm 시트의 플립7 매핑:")
for idx, row in flip7_mapping.iterrows():
    print(f"   device_nm: '{row['device_nm']}' → product_group_nm: '{row['product_group_nm']}', storage: '{row['storage']}'")

# 2. Support 시트
support_worksheet = sheet.worksheet('support')
support_data = support_worksheet.get_all_records()
support_df = pd.DataFrame(support_data)

print("\n2. Support 시트의 SK 플립7 관련 device_nm 종류:")
sk_flip7_all = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'].str.contains('플립7|플립 7', na=False))]
unique_devices = sk_flip7_all['device_nm'].unique()
for device in unique_devices:
    count = len(sk_flip7_all[sk_flip7_all['device_nm'] == device])
    print(f"   '{device}': {count}개")

# 3. 정확한 매칭 시도
print("\n3. 매칭 시도:")
print("   product_group_nm 시트: '갤럭시 Z 플립 7'")
print("   Support 시트에서 검색:")

# 정확한 문자열 매칭
exact_match = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'] == '갤럭시 Z 플립 7')]
print(f"   - 정확히 '갤럭시 Z 플립 7': {len(exact_match)}개")

# 부분 매칭
partial_match = support_df[(support_df['carrier'] == 'SK') & (support_df['device_nm'].str.contains('갤럭시 Z 플립7', na=False))]
print(f"   - '갤럭시 Z 플립7' 포함: {len(partial_match)}개")

# 4. 256GB storage 매칭 확인
print("\n4. Storage 매칭 분석:")
print("   product_group_nm 시트의 storage: '256GB'")
print("   Support 시트의 갤럭시 Z 플립7 관련 storage:")

for device in unique_devices:
    device_data = sk_flip7_all[sk_flip7_all['device_nm'] == device]
    storages = device_data['storage'].unique()
    print(f"   - '{device}': {storages}")

# 5. 109k 요금제로 필터링
print("\n5. 109k 요금제 데이터:")
flip7_109k = sk_flip7_all[sk_flip7_all['rate_plan_month_fee'] == 109000]
print(f"   총 {len(flip7_109k)}개")
for device in flip7_109k['device_nm'].unique():
    device_109k = flip7_109k[flip7_109k['device_nm'] == device]
    for storage in device_109k['storage'].unique():
        count = len(device_109k[device_109k['storage'] == storage])
        print(f"   - '{device}' / storage: '{storage}': {count}개")

print("\n=== 결론 ===")
print("문제: product_group_nm 시트의 '갤럭시 Z 플립 7'과 Support 시트의 device_nm이 일치하지 않음")
print("- product_group_nm: '갤럭시 Z 플립 7' (띄어쓰기 있음)")
print("- Support: '갤럭시 Z 플립7 512G', '갤럭시 Z 플립7 FE 256G' (띄어쓰기 없음, 용량 포함)")
print("\n해결 방안:")
print("1. product_group_nm 시트를 Support 시트의 실제 device_nm과 일치하도록 수정")
print("2. 또는 매칭 로직을 수정하여 유연한 매칭 적용")