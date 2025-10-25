#!/usr/bin/env python3

import pandas as pd
import argparse
import os
from datetime import datetime

def merge_kt_support_data(existing_file, new_file, output_file=None):
    """
    기존 KT support 데이터와 새로 크롤링된 데이터를 병합

    Args:
        existing_file: 기존 support 데이터 파일 경로
        new_file: 새로 크롤링된 KT 데이터 파일 경로
        output_file: 출력 파일 경로 (기본값: data/support_merged_{timestamp}.csv)
    """

    # 파일 존재 확인
    if not os.path.exists(existing_file):
        raise FileNotFoundError(f"기존 support 파일을 찾을 수 없습니다: {existing_file}")
    if not os.path.exists(new_file):
        raise FileNotFoundError(f"새 KT 크롤링 파일을 찾을 수 없습니다: {new_file}")

    print(f"기존 support 데이터 로딩: {existing_file}")
    existing_df = pd.read_csv(existing_file)
    print(f"기존 데이터: {len(existing_df)} 행")

    print(f"새 KT 크롤링 데이터 로딩: {new_file}")
    new_df = pd.read_csv(new_file)
    print(f"새 데이터: {len(new_df)} 행")

    # KT 데이터만 필터링 (새 데이터는 이미 KT만 있음)
    existing_kt = existing_df[existing_df['carrier'] == 'KT'].copy() if 'carrier' in existing_df.columns else pd.DataFrame()
    existing_non_kt = existing_df[existing_df['carrier'] != 'KT'].copy() if 'carrier' in existing_df.columns else existing_df.copy()

    print(f"기존 KT 데이터: {len(existing_kt)} 행")
    print(f"기존 비-KT 데이터: {len(existing_non_kt)} 행")

    # 중복 제거를 위한 키 컬럼들
    key_columns = ['carrier', 'manufacturer', 'scrb_type_name', 'network_type', 'device_nm', 'plan_name', 'monthly_fee']

    # 기존 KT 데이터에서 새 데이터와 겹치는 항목 제거
    if len(existing_kt) > 0:
        # 중복 확인을 위한 키 생성
        existing_kt['merge_key'] = existing_kt[key_columns].astype(str).agg('|'.join, axis=1)
        new_df['merge_key'] = new_df[key_columns].astype(str).agg('|'.join, axis=1)

        # 새 데이터와 겹치지 않는 기존 KT 데이터만 유지
        non_duplicate_existing = existing_kt[~existing_kt['merge_key'].isin(new_df['merge_key'])].copy()
        non_duplicate_existing = non_duplicate_existing.drop('merge_key', axis=1)
        new_df_clean = new_df.drop('merge_key', axis=1)

        print(f"중복 제거 후 기존 KT 데이터: {len(non_duplicate_existing)} 행")
        print(f"제거된 중복 항목: {len(existing_kt) - len(non_duplicate_existing)} 행")

        # 데이터 병합: 기존 비-KT + 기존 KT(중복제거) + 새 KT
        merged_df = pd.concat([existing_non_kt, non_duplicate_existing, new_df_clean], ignore_index=True)
    else:
        # 기존 KT 데이터가 없는 경우
        merged_df = pd.concat([existing_non_kt, new_df], ignore_index=True)

    # 날짜순 정렬 (최신순)
    if 'date' in merged_df.columns:
        merged_df['date'] = pd.to_datetime(merged_df['date'], format='mixed')
        merged_df = merged_df.sort_values(['date', 'carrier', 'device_nm'], ascending=[False, True, True])
        merged_df['date'] = merged_df['date'].dt.strftime('%Y-%m-%d')

    print(f"최종 병합 데이터: {len(merged_df)} 행")

    # 출력 파일명 생성
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/support_merged_{timestamp}.csv"

    # 결과 저장
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"병합된 데이터 저장 완료: {output_file}")

    # 요약 정보 출력
    print("\n=== 병합 결과 요약 ===")
    print(f"총 데이터: {len(merged_df)} 행")
    if 'carrier' in merged_df.columns:
        carrier_counts = merged_df['carrier'].value_counts()
        for carrier, count in carrier_counts.items():
            print(f"{carrier}: {count} 행")

    return output_file

def main():
    parser = argparse.ArgumentParser(description='KT support 데이터 병합')
    parser.add_argument('--existing', '-e', required=True, help='기존 support 데이터 파일 경로')
    parser.add_argument('--new', '-n', required=True, help='새 KT 크롤링 데이터 파일 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')

    args = parser.parse_args()

    try:
        output_file = merge_kt_support_data(args.existing, args.new, args.output)
        print(f"\n성공적으로 병합되었습니다: {output_file}")
    except Exception as e:
        print(f"오류 발생: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())