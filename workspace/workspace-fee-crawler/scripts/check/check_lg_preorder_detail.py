import pandas as pd

# Excel 파일 읽기
file_path = 'src/ocr/OCR/OCR_결과/20250718/250718_LG_사전예약_tables_calculated.xlsx'
df = pd.read_excel(file_path)

print(f'전체 데이터 크기: {df.shape}')
print(f'행 수: {len(df)}, 열 수: {len(df.columns)}')
print('\n전체 데이터:')
print('-' * 80)

# 전체 데이터 출력
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

print(df)

# 실제 제품 데이터가 있는 행 찾기
print('\n제품 정보가 있는 행:')
print('-' * 80)

for i, row in df.iterrows():
    if 'SM-' in str(row.iloc[0]):
        print(f'\n행 {i+1}:')
        for j, value in enumerate(row):
            if pd.notna(value):
                print(f'  컬럼{j+1}: {value}')

# 다른 시트가 있는지 확인
xl_file = pd.ExcelFile(file_path)
print(f'\n엑셀 파일의 시트 목록: {xl_file.sheet_names}')

# 모든 시트 확인
for sheet_name in xl_file.sheet_names:
    print(f'\n=== {sheet_name} 시트 ===')
    sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f'크기: {sheet_df.shape}')
    if len(sheet_df) > 0:
        print('데이터 미리보기:')
        print(sheet_df)