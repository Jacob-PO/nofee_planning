import pandas as pd

# Excel 파일 읽기
file_path = 'src/ocr/OCR/OCR_결과/20250718/250718_LG_사전예약_tables_calculated.xlsx'
df = pd.read_excel(file_path)

print(f'총 행 수: {len(df)}')
print(f'컬럼명: {list(df.columns)}')

# 첫 번째 컬럼이 제품명이라고 가정
print(f'\n전체 제품 목록:')
print('-' * 50)

for i, row in df.iterrows():
    product_name = row.iloc[0] if pd.notna(row.iloc[0]) else "제품명 없음"
    print(f'{i+1}. {product_name}')

# 제품별 개수 확인
print(f'\n제품별 집계:')
print('-' * 50)
product_counts = df.iloc[:, 0].value_counts()
for product, count in product_counts.items():
    print(f'{product}: {count}개')