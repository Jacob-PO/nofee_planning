import pandas as pd
import re

def parse_iphone_model(device_name):
    """iPhone 모델명을 정규화하여 파싱"""
    # 기본 정리
    name = device_name.strip()
    name = re.sub(r'_', ' ', name)
    
    # 모델 추출 패턴
    patterns = [
        r'(iPhone \d+e)',  # iPhone 16e
        r'(iPhone \d+ Pro Max)',  # iPhone 16 Pro Max
        r'(iPhone \d+ Pro)',  # iPhone 16 Pro
        r'(iPhone \d+ Plus)',  # iPhone 16 Plus
        r'(iPhone \d+ mini)',  # iPhone 13 mini
        r'(iPhone \d+)',  # iPhone 16
    ]
    
    model = None
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            model = match.group(1)
            break
    
    if not model:
        return None, None
    
    # 용량 추출
    capacity_match = re.search(r'(\d+)\s*(GB|G|TB|T)', name, re.IGNORECASE)
    if capacity_match:
        size = capacity_match.group(1)
        unit = capacity_match.group(2).upper()
        if unit in ['G', 'GB']:
            capacity = f"{size}GB"
        elif unit in ['T', 'TB']:
            capacity = f"{size}TB"
        else:
            capacity = None
    else:
        capacity = None
    
    return model, capacity

def analyze_prices():
    # 데이터 로드
    sk_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/sk_20250715_084232.csv')
    kt_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/kt_20250715_084559.csv')
    lg_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/lg_20250715_100202.csv')
    
    # 통신사별 분석
    carriers = [
        ('SK', sk_df),
        ('KT', kt_df),
        ('LG U+', lg_df)
    ]
    
    all_data = []
    
    for carrier_name, df in carriers:
        # iPhone 데이터만 필터링
        iphone_df = df[df['device_nm'].str.contains('iPhone', na=False, case=False)]
        
        # 매장 전시용 제외
        iphone_df = iphone_df[~iphone_df['device_nm'].str.contains('매장 전시용', na=False)]
        
        for _, row in iphone_df.iterrows():
            model, capacity = parse_iphone_model(row['device_nm'])
            if model and capacity:
                all_data.append({
                    'carrier': carrier_name,
                    'model': model,
                    'capacity': capacity,
                    'price': row['release_price'],
                    'original_name': row['device_nm']
                })
    
    # DataFrame으로 변환
    result_df = pd.DataFrame(all_data)
    
    # 중복 제거 (같은 통신사, 모델, 용량)
    result_df = result_df.drop_duplicates(subset=['carrier', 'model', 'capacity'])
    
    # 정렬
    result_df = result_df.sort_values(['model', 'capacity', 'carrier'])
    
    # 결과 출력
    print("="*80)
    print("각 통신사별 iPhone 모델의 용량별 출고가 정리")
    print("="*80)
    
    # 통신사별로 출력
    for carrier in ['SK', 'KT', 'LG U+']:
        carrier_data = result_df[result_df['carrier'] == carrier]
        
        print(f"\n【{carrier} 통신사】")
        print("-"*60)
        
        # 모델별로 그룹화
        models = sorted(carrier_data['model'].unique())
        
        # iPhone 시리즈별로 분류
        series_order = ['iPhone 13', 'iPhone 14', 'iPhone 15', 'iPhone 16']
        
        for series in series_order:
            series_models = [m for m in models if m.startswith(series)]
            
            if not series_models:
                continue
                
            print(f"\n◆ {series} 시리즈")
            
            for model in sorted(series_models):
                model_data = carrier_data[carrier_data['model'] == model]
                
                if model_data.empty:
                    continue
                
                print(f"\n  《{model}》")
                
                # 용량 순서 정의
                capacity_order = ['128GB', '256GB', '512GB', '1TB']
                sorted_data = []
                
                for cap in capacity_order:
                    cap_data = model_data[model_data['capacity'] == cap]
                    if not cap_data.empty:
                        sorted_data.append(cap_data.iloc[0])
                
                # 가격 차이 계산하며 출력
                prev_price = None
                for idx, data in enumerate(sorted_data):
                    price = data['price']
                    capacity = data['capacity']
                    
                    if prev_price is not None:
                        diff = price - prev_price
                        print(f"    {capacity}: {price:,}원 (▲{diff:,}원)")
                    else:
                        print(f"    {capacity}: {price:,}원")
                    
                    prev_price = price
    
    # 통신사간 가격 비교
    print("\n\n" + "="*80)
    print("주요 모델 통신사별 가격 비교")
    print("="*80)
    
    # iPhone 16 시리즈 비교
    compare_models = [
        'iPhone 16', 'iPhone 16 Plus', 'iPhone 16 Pro', 'iPhone 16 Pro Max', 'iPhone 16e'
    ]
    
    for model in compare_models:
        model_data = result_df[result_df['model'] == model]
        
        if model_data.empty:
            continue
            
        print(f"\n【{model}】")
        
        capacities = sorted(model_data['capacity'].unique(), 
                          key=lambda x: (int(re.search(r'\d+', x).group()), x))
        
        for capacity in capacities:
            cap_data = model_data[model_data['capacity'] == capacity]
            
            print(f"\n  {capacity}:")
            
            # 각 통신사별 가격
            for carrier in ['SK', 'KT', 'LG U+']:
                carrier_price = cap_data[cap_data['carrier'] == carrier]
                if not carrier_price.empty:
                    price = carrier_price.iloc[0]['price']
                    print(f"    {carrier}: {price:,}원")
                else:
                    print(f"    {carrier}: -")
            
            # 가격 차이 분석
            prices = cap_data['price'].values
            if len(prices) > 1:
                min_price = min(prices)
                max_price = max(prices)
                if min_price != max_price:
                    print(f"    ※ 가격차: {max_price - min_price:,}원")

if __name__ == "__main__":
    analyze_prices()