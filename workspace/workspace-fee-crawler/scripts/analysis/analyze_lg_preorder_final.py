import pandas as pd

# Excel 파일 읽기
file_path = 'src/ocr/OCR/OCR_결과/20250718/250718_LG_사전예약_tables_calculated.xlsx'
df = pd.read_excel(file_path)

print("=== LG 사전예약 데이터 분석 결과 ===\n")

# 데이터가 있는 행만 필터링 (제품명이 있는 행)
product_rows = df[df.iloc[:, 0].str.contains('SM-', na=False)]

print(f"총 제품 수: {len(product_rows)}개\n")

print("제품 목록:")
print("-" * 50)

# 제품명 추출 및 설명
for idx, row in product_rows.iterrows():
    product_name = row.iloc[0]
    
    # 제품 모델 분석
    if 'F766N' in product_name:
        device_type = "갤럭시 Z 플립7"
    elif 'F966N' in product_name:
        device_type = "갤럭시 Z 폴드7"
    else:
        device_type = "알 수 없는 모델"
    
    # 용량 분석
    if '512' in product_name:
        storage = "512GB"
    elif '1TB' in product_name:
        storage = "1TB"
    else:
        storage = "알 수 없는 용량"
    
    print(f"\n{idx-2}. {product_name}")
    print(f"   - 제품: {device_type}")
    print(f"   - 저장용량: {storage}")
    print(f"   - 유형: 사전예약")

print("\n\n=== 요금제별 지원금 정보 ===")
print("-" * 80)

# 헤더 정보 추출
headers = df.iloc[1:3]
print("\n요금제 그룹:")
print("- 5G 115군 (프리미어플러스 슈퍼이상) - 기본료 115,000원 이상")
print("- 5G 105군 (프리미어플러스)")
print("- 5G 95군 (일반 레귤러기준)")

print("\n가입 유형: MNP(번호이동), 재가입")

print("\n\n지원금 상세 (단위: 만원):")
print("-" * 80)

for idx, row in product_rows.iterrows():
    product_name = row.iloc[0]
    print(f"\n{product_name}:")
    print("  5G 115군: MNP {:.1f}만원, 재가입 {:.1f}만원".format(
        int(row.iloc[1])/10000, int(row.iloc[2])/10000))
    print("  5G 105군: MNP {:.1f}만원, 재가입 {:.1f}만원".format(
        int(row.iloc[3])/10000, int(row.iloc[4])/10000))
    print("  5G 95군:  MNP {:.1f}만원, 재가입 {:.1f}만원".format(
        int(row.iloc[5])/10000, int(row.iloc[6])/10000))

print("\n\n=== 요약 ===")
print(f"- LG 사전예약 정책일: 7월 16일 (1차)")
print(f"- 총 {len(product_rows)}개 제품 (갤럭시 Z 플립7 1개, 갤럭시 Z 폴드7 2개)")
print(f"- 지원금 범위: 18.5만원 ~ 24.5만원")
print(f"- 최고 지원금: 5G 115군 MNP 가입 시 24.5만원")
print(f"- 최저 지원금: 5G 95군 재가입 시 18.5만원")