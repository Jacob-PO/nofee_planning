import pandas as pd
import re

def extract_model_capacity(device_name):
    """모델명에서 모델과 용량을 추출"""
    # iPhone 모델 패턴: iPhone 숫자 [Pro/Pro Max/Plus/e/mini]
    model_pattern = r'(iPhone \d+(?:e|Pro Max|Pro|Plus|mini)?)'
    capacity_pattern = r'(\d+(?:G|GB|T|TB))'
    
    model_match = re.search(model_pattern, device_name)
    capacity_match = re.search(capacity_pattern, device_name)
    
    model = model_match.group(1) if model_match else device_name
    capacity = capacity_match.group(1) if capacity_match else 'Unknown'
    
    # 용량 정규화
    capacity = capacity.replace('G', 'GB').replace('T', 'TB')
    
    return model, capacity

def analyze_carrier_prices(carrier_name, df):
    """통신사별 가격 분석"""
    print(f"\n{'='*60}")
    print(f"{carrier_name} 통신사 iPhone 모델별 출고가")
    print(f"{'='*60}")
    
    # iPhone 데이터 필터링
    iphone_df = df[df['device_nm'].str.contains('iPhone', na=False)].copy()
    
    # 매장 전시용 제외
    iphone_df = iphone_df[~iphone_df['device_nm'].str.contains('매장 전시용', na=False)]
    
    # 모델과 용량 추출
    iphone_df[['model', 'capacity']] = iphone_df['device_nm'].apply(
        lambda x: pd.Series(extract_model_capacity(x))
    )
    
    # 중복 제거
    unique_df = iphone_df[['model', 'capacity', 'release_price']].drop_duplicates()
    
    # 모델별로 그룹화
    models = sorted(unique_df['model'].unique())
    
    for model in models:
        model_data = unique_df[unique_df['model'] == model].sort_values('capacity')
        
        if len(model_data) == 0:
            continue
            
        print(f"\n【{model}】")
        
        # 용량별 가격과 차이 출력
        prev_price = None
        for idx, row in model_data.iterrows():
            price = row['release_price']
            capacity = row['capacity']
            
            if prev_price is not None:
                diff = price - prev_price
                print(f"  {capacity}: {price:,}원 (+{diff:,}원)")
            else:
                print(f"  {capacity}: {price:,}원")
            
            prev_price = price

# 각 통신사 데이터 분석
sk_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/sk_20250715_084232.csv')
kt_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/kt_20250715_084559.csv')
lg_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/lg_20250715_100202.csv')

analyze_carrier_prices("SK", sk_df)
analyze_carrier_prices("KT", kt_df)
analyze_carrier_prices("LG U+", lg_df)

# 모델별 통신사 가격 비교
print(f"\n{'='*80}")
print("주요 iPhone 모델별 통신사 가격 비교")
print(f"{'='*80}")

# 공통 모델 찾기
def get_iphone_prices(df, carrier):
    """통신사별 iPhone 가격 정보 추출"""
    iphone_df = df[df['device_nm'].str.contains('iPhone', na=False)].copy()
    iphone_df = iphone_df[~iphone_df['device_nm'].str.contains('매장 전시용', na=False)]
    iphone_df['normalized_name'] = iphone_df['device_nm'].str.replace(r'_', ' ', regex=True)
    return iphone_df[['normalized_name', 'release_price']].drop_duplicates()

sk_prices = get_iphone_prices(sk_df, 'SK')
kt_prices = get_iphone_prices(kt_df, 'KT')
lg_prices = get_iphone_prices(lg_df, 'LG')

# iPhone 16 시리즈 비교
print("\n【iPhone 16 시리즈】")
models_16 = ['iPhone 16 128GB', 'iPhone 16 256GB', 'iPhone 16 512GB',
             'iPhone 16 Pro 128GB', 'iPhone 16 Pro 256GB', 'iPhone 16 Pro 512GB', 'iPhone 16 Pro 1TB',
             'iPhone 16 Pro Max 256GB', 'iPhone 16 Pro Max 512GB', 'iPhone 16 Pro Max 1TB']

for model in models_16:
    print(f"\n{model}:")
    
    # 모델명 변형들 확인
    variations = [model, model.replace('GB', 'G'), model.replace('TB', 'T')]
    
    found = False
    for var in variations:
        sk_price = sk_prices[sk_prices['normalized_name'].str.contains(var, na=False, regex=False)]
        kt_price = kt_prices[kt_prices['normalized_name'].str.contains(var, na=False, regex=False)]
        lg_price = lg_prices[lg_prices['normalized_name'].str.contains(var, na=False, regex=False)]
        
        if not sk_price.empty or not kt_price.empty or not lg_price.empty:
            found = True
            if not sk_price.empty:
                print(f"  SK: {sk_price.iloc[0]['release_price']:,}원")
            if not kt_price.empty:
                print(f"  KT: {kt_price.iloc[0]['release_price']:,}원")
            if not lg_price.empty:
                print(f"  LG: {lg_price.iloc[0]['release_price']:,}원")
            break
    
    if not found:
        print("  데이터 없음")