import pandas as pd
import re

# SK 데이터 분석
sk_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/sk_20250715_084232.csv')
sk_iphones = sk_df[sk_df['device_nm'].str.contains('iPhone', na=False)]
sk_unique = sk_iphones[['device_nm', 'release_price']].drop_duplicates().sort_values('device_nm')

print("=== SK 통신사 iPhone 모델별 출고가 ===")
print(sk_unique)

# KT 데이터 분석
kt_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/kt_20250715_084559.csv')
kt_iphones = kt_df[kt_df['device_nm'].str.contains('iPhone', na=False)]
kt_unique = kt_iphones[['device_nm', 'release_price']].drop_duplicates().sort_values('device_nm')

print("\n=== KT 통신사 iPhone 모델별 출고가 ===")
print(kt_unique)

# LG 데이터 분석
lg_df = pd.read_csv('/Users/jacob_athometrip/Desktop/dev/workspace-fee-crawler_v2/data/raw/lg_20250715_100202.csv')
lg_iphones = lg_df[lg_df['device_nm'].str.contains('iPhone|아이폰', na=False)]
lg_unique = lg_iphones[['device_nm', 'release_price']].drop_duplicates().sort_values('device_nm')

print("\n=== LG 통신사 iPhone 모델별 출고가 ===")
print(lg_unique)