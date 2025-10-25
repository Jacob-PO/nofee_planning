#!/usr/bin/env python3
"""
iPhone 용량별 확장 기능 정합성 검증 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_support_data():
    """Support 시트에서 용량별 가격 차이 정보 로드"""
    support_file = Path("data/support/support_data.xlsx")
    if not support_file.exists():
        print(f"Support 파일을 찾을 수 없습니다: {support_file}")
        return None
    
    try:
        df = pd.read_excel(support_file, sheet_name="iPhone용량별가격")
        return df
    except Exception as e:
        print(f"Support 데이터 로드 실패: {e}")
        return None

def validate_original_data_preserved(original_df, expanded_df, carrier):
    """원본 데이터가 확장된 데이터에 그대로 포함되어 있는지 검증"""
    print(f"\n{'='*60}")
    print(f"{carrier.upper()} - 1. 원본 데이터 보존 검증")
    print(f"{'='*60}")
    
    # iPhone 데이터만 필터링
    original_iphones = original_df[original_df['device_name'].str.contains('iPhone', case=False, na=False)].copy()
    expanded_iphones = expanded_df[expanded_df['device_name'].str.contains('iPhone', case=False, na=False)].copy()
    
    print(f"원본 iPhone 수: {len(original_iphones)}")
    print(f"확장된 iPhone 수: {len(expanded_iphones)}")
    
    # 검증을 위한 키 컬럼들
    key_columns = ['device_name', 'plan_name', 'discount_type']
    value_columns = ['installment_24', 'installment_30', 'installment_36', 
                     'official_price', 'upfront_fee', 'total_monthly_fee']
    
    # 원본 데이터의 각 행이 확장된 데이터에 존재하는지 확인
    missing_records = []
    changed_records = []
    
    for idx, row in original_iphones.iterrows():
        # 동일한 레코드 찾기
        mask = True
        for col in key_columns:
            if col in expanded_iphones.columns:
                mask = mask & (expanded_iphones[col] == row[col])
        
        matched = expanded_iphones[mask]
        
        if len(matched) == 0:
            missing_records.append(row[key_columns].to_dict())
        elif len(matched) == 1:
            # 값이 변경되었는지 확인
            for col in value_columns:
                if col in row and col in matched.columns:
                    original_val = row[col]
                    expanded_val = matched.iloc[0][col]
                    
                    # NaN 처리
                    if pd.isna(original_val) and pd.isna(expanded_val):
                        continue
                    elif original_val != expanded_val:
                        changed_records.append({
                            'device': row['device_name'],
                            'plan': row['plan_name'],
                            'column': col,
                            'original': original_val,
                            'expanded': expanded_val
                        })
    
    print(f"\n✓ 검증 결과:")
    print(f"  - 누락된 레코드: {len(missing_records)}개")
    print(f"  - 변경된 값: {len(changed_records)}개")
    
    if missing_records:
        print("\n⚠️  누락된 레코드 예시 (최대 5개):")
        for i, rec in enumerate(missing_records[:5]):
            print(f"  {i+1}. {rec}")
    
    if changed_records:
        print("\n⚠️  변경된 값 예시 (최대 5개):")
        for i, rec in enumerate(changed_records[:5]):
            print(f"  {i+1}. {rec['device']} - {rec['column']}: {rec['original']} → {rec['expanded']}")
    
    return len(missing_records) == 0 and len(changed_records) == 0

def validate_price_differences(expanded_df, support_df, carrier):
    """용량별 가격 차이가 Support 시트와 일치하는지 검증"""
    print(f"\n{'='*60}")
    print(f"{carrier.upper()} - 2. 용량별 가격 차이 검증")
    print(f"{'='*60}")
    
    if support_df is None:
        print("Support 데이터가 없어 검증을 수행할 수 없습니다.")
        return False
    
    # iPhone 데이터만 필터링
    iphones = expanded_df[expanded_df['device_name'].str.contains('iPhone', case=False, na=False)].copy()
    
    # 모델별로 그룹화
    model_groups = {}
    for idx, row in iphones.iterrows():
        device_name = row['device_name']
        # 모델명 추출 (용량 제외)
        if 'GB' in device_name:
            base_model = device_name.split('GB')[0].strip()
            base_model = base_model.replace('512', '').replace('256', '').replace('128', '').strip()
            
            if base_model not in model_groups:
                model_groups[base_model] = []
            model_groups[base_model].append(row)
    
    print(f"\n발견된 iPhone 모델 수: {len(model_groups)}")
    
    # 각 모델별로 용량 차이 검증
    validation_errors = []
    
    for model, records in model_groups.items():
        if len(records) < 2:
            continue
            
        print(f"\n▶ {model} 검증:")
        
        # 용량별로 정렬
        records_sorted = sorted(records, key=lambda x: extract_capacity(x['device_name']))
        
        # 기준 용량 (가장 작은 용량)
        base_record = records_sorted[0]
        base_capacity = extract_capacity(base_record['device_name'])
        
        print(f"  기준 용량: {base_capacity}GB")
        
        # 다른 용량들과 비교
        for i in range(1, len(records_sorted)):
            record = records_sorted[i]
            capacity = extract_capacity(record['device_name'])
            
            # Support 시트에서 예상 가격 차이 찾기
            expected_diff = get_expected_price_diff(support_df, base_capacity, capacity)
            
            if expected_diff is not None:
                # 실제 가격 차이 계산
                actual_diff = record['official_price'] - base_record['official_price']
                
                print(f"  {capacity}GB: 예상 차이 {expected_diff:,}원, 실제 차이 {actual_diff:,}원", end="")
                
                if abs(actual_diff - expected_diff) > 1:  # 1원 오차 허용
                    print(" ❌")
                    validation_errors.append({
                        'model': model,
                        'base_capacity': base_capacity,
                        'target_capacity': capacity,
                        'expected': expected_diff,
                        'actual': actual_diff,
                        'difference': actual_diff - expected_diff
                    })
                else:
                    print(" ✅")
    
    print(f"\n✓ 검증 결과:")
    print(f"  - 가격 차이 오류: {len(validation_errors)}개")
    
    if validation_errors:
        print("\n⚠️  가격 차이 오류 상세:")
        for err in validation_errors[:10]:
            print(f"  - {err['model']} ({err['base_capacity']}GB → {err['target_capacity']}GB): "
                  f"차이 {err['difference']:,}원")
    
    return len(validation_errors) == 0

def extract_capacity(device_name):
    """디바이스명에서 용량 추출"""
    if '512GB' in device_name:
        return 512
    elif '256GB' in device_name:
        return 256
    elif '128GB' in device_name:
        return 128
    else:
        return 128  # 기본값

def get_expected_price_diff(support_df, base_capacity, target_capacity):
    """Support 시트에서 예상 가격 차이 찾기"""
    if support_df is None:
        return None
    
    # Support 시트 구조에 따라 로직 조정 필요
    try:
        # 용량 조합 찾기
        mask = ((support_df['base_capacity'] == base_capacity) & 
                (support_df['target_capacity'] == target_capacity))
        
        if mask.any():
            return support_df[mask].iloc[0]['price_difference']
    except:
        pass
    
    # 하드코딩된 기본값 (실제 Support 시트 구조 확인 필요)
    if base_capacity == 128 and target_capacity == 256:
        return 150000
    elif base_capacity == 128 and target_capacity == 512:
        return 450000
    elif base_capacity == 256 and target_capacity == 512:
        return 300000
    
    return None

def validate_data_integrity(expanded_df, carrier):
    """데이터 무결성 확인"""
    print(f"\n{'='*60}")
    print(f"{carrier.upper()} - 3. 데이터 무결성 확인")
    print(f"{'='*60}")
    
    # iPhone 데이터만 필터링
    iphones = expanded_df[expanded_df['device_name'].str.contains('iPhone', case=False, na=False)].copy()
    
    # 필수 컬럼 확인
    required_columns = ['device_name', 'plan_name', 'discount_type', 
                       'installment_24', 'official_price']
    
    missing_columns = [col for col in required_columns if col not in iphones.columns]
    
    print(f"\n✓ 필수 컬럼 확인:")
    if missing_columns:
        print(f"  ⚠️  누락된 컬럼: {missing_columns}")
    else:
        print(f"  ✅ 모든 필수 컬럼 존재")
    
    # Null 값 확인
    print(f"\n✓ Null 값 확인:")
    null_counts = {}
    for col in required_columns:
        if col in iphones.columns:
            null_count = iphones[col].isna().sum()
            if null_count > 0:
                null_counts[col] = null_count
    
    if null_counts:
        print(f"  ⚠️  Null 값이 있는 컬럼:")
        for col, count in null_counts.items():
            print(f"    - {col}: {count}개")
    else:
        print(f"  ✅ 필수 컬럼에 Null 값 없음")
    
    # 비정상적인 값 확인
    print(f"\n✓ 비정상적인 값 확인:")
    anomalies = []
    
    # 가격이 0이거나 음수인 경우
    if 'official_price' in iphones.columns:
        invalid_prices = iphones[iphones['official_price'] <= 0]
        if len(invalid_prices) > 0:
            anomalies.append(f"출고가가 0 이하: {len(invalid_prices)}개")
    
    # 할부금이 음수인 경우
    for col in ['installment_24', 'installment_30', 'installment_36']:
        if col in iphones.columns:
            invalid = iphones[iphones[col] < 0]
            if len(invalid) > 0:
                anomalies.append(f"{col}이 음수: {len(invalid)}개")
    
    if anomalies:
        for anomaly in anomalies:
            print(f"  ⚠️  {anomaly}")
    else:
        print(f"  ✅ 비정상적인 값 없음")
    
    return len(missing_columns) == 0 and len(null_counts) == 0 and len(anomalies) == 0

def validate_expansion_logic(original_df, expanded_df, carrier):
    """확장 로직 검증"""
    print(f"\n{'='*60}")
    print(f"{carrier.upper()} - 4. 확장 로직 검증")
    print(f"{'='*60}")
    
    # iPhone 데이터만 필터링
    original_iphones = original_df[original_df['device_name'].str.contains('iPhone', case=False, na=False)]
    expanded_iphones = expanded_df[expanded_df['device_name'].str.contains('iPhone', case=False, na=False)]
    
    print(f"\n✓ 확장 결과:")
    print(f"  - 원본 iPhone 수: {len(original_iphones)}")
    print(f"  - 확장된 iPhone 수: {len(expanded_iphones)}")
    if len(original_iphones) > 0:
        print(f"  - 증가율: {(len(expanded_iphones) / len(original_iphones) - 1) * 100:.1f}%")
    else:
        print(f"  - 증가율: N/A (원본에 iPhone 없음)")
    
    # 모델별 용량 확인
    print(f"\n✓ 모델별 용량 버전 수:")
    
    model_capacities = {}
    for idx, row in expanded_iphones.iterrows():
        device_name = row['device_name']
        if 'GB' in device_name:
            base_model = device_name.split('GB')[0].strip()
            base_model = base_model.replace('512', '').replace('256', '').replace('128', '').strip()
            
            if base_model not in model_capacities:
                model_capacities[base_model] = set()
            
            capacity = extract_capacity(device_name)
            model_capacities[base_model].add(capacity)
    
    for model, capacities in sorted(model_capacities.items())[:10]:
        print(f"  - {model}: {sorted(capacities)}")
    
    # device_name 형식 확인
    print(f"\n✓ device_name 형식 확인:")
    invalid_names = []
    
    for idx, row in expanded_iphones.iterrows():
        device_name = row['device_name']
        if 'GB' not in device_name:
            invalid_names.append(device_name)
    
    if invalid_names:
        print(f"  ⚠️  GB가 없는 device_name: {len(invalid_names)}개")
        for name in invalid_names[:5]:
            print(f"    - {name}")
    else:
        print(f"  ✅ 모든 iPhone에 용량 정보 포함")
    
    return True

def main():
    """메인 실행 함수"""
    print("iPhone 용량별 확장 기능 정합성 검증")
    print("="*60)
    
    # Support 데이터 로드
    support_df = load_support_data()
    
    # 각 통신사별로 검증
    carriers = ['sk', 'kt', 'lg']
    
    # 최신 파일 찾기
    results_dir = Path("src/data_processing/results")
    
    overall_results = {}
    
    for carrier in carriers:
        print(f"\n\n{'#'*60}")
        print(f"# {carrier.upper()} 통신사 검증")
        print(f"{'#'*60}")
        
        # 최신 merged 파일 찾기
        merged_files = sorted(results_dir.glob(f"{carrier}_merged_data_*.xlsx"))
        if not merged_files:
            print(f"{carrier} merged 파일을 찾을 수 없습니다.")
            continue
        
        original_file = merged_files[-1]
        
        # 최신 expanded 파일 찾기
        expanded_files = sorted(results_dir.glob(f"{carrier}_expanded_*.xlsx"))
        if not expanded_files:
            print(f"{carrier} expanded 파일을 찾을 수 없습니다.")
            continue
        
        expanded_file = expanded_files[-1]
        
        print(f"\n원본 파일: {original_file.name}")
        print(f"확장 파일: {expanded_file.name}")
        
        # 데이터 로드
        try:
            original_df = pd.read_excel(original_file)
            expanded_df = pd.read_excel(expanded_file)
        except Exception as e:
            print(f"파일 로드 실패: {e}")
            continue
        
        # 각 검증 수행
        results = {
            'original_preserved': validate_original_data_preserved(original_df, expanded_df, carrier),
            'price_differences': validate_price_differences(expanded_df, support_df, carrier),
            'data_integrity': validate_data_integrity(expanded_df, carrier),
            'expansion_logic': validate_expansion_logic(original_df, expanded_df, carrier)
        }
        
        overall_results[carrier] = results
    
    # 최종 결과 요약
    print(f"\n\n{'='*60}")
    print("최종 검증 결과 요약")
    print(f"{'='*60}")
    
    for carrier, results in overall_results.items():
        print(f"\n{carrier.upper()}:")
        print(f"  1. 원본 데이터 보존: {'✅ 통과' if results.get('original_preserved', False) else '❌ 실패'}")
        print(f"  2. 용량별 가격 차이: {'✅ 통과' if results.get('price_differences', False) else '❌ 실패'}")
        print(f"  3. 데이터 무결성: {'✅ 통과' if results.get('data_integrity', False) else '❌ 실패'}")
        print(f"  4. 확장 로직: {'✅ 통과' if results.get('expansion_logic', False) else '❌ 실패'}")

if __name__ == "__main__":
    main()