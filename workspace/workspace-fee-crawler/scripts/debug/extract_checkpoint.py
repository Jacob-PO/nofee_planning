#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""체크포인트에서 데이터 추출 및 저장"""

import sys
import pickle
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# pickle 모듈에 필요한 클래스들 임포트
from src.crawlers.lg_crawler import DeviceData, RatePlan, CrawlTask

checkpoint_file = 'data/checkpoints/lg_checkpoint.pkl'

try:
    print(f"체크포인트 파일 로드 시도: {checkpoint_file}")

    with open(checkpoint_file, 'rb') as f:
        data = pickle.load(f)

    print(f"✅ 체크포인트 로드 성공!")
    print(f"타임스탬프: {data.get('timestamp', 'N/A')}")
    print(f"완료: {data.get('completed', 0)}개")
    print(f"실패: {data.get('failed', 0)}개")
    print(f"총 데이터 수: {len(data.get('data', []))}개")

    # 데이터 추출
    device_data_list = data.get('data', [])

    if device_data_list:
        # dict 형태로 변환 (이미 dict일 수도 있음)
        if isinstance(device_data_list[0], dict):
            df = pd.DataFrame(device_data_list)
        else:
            df = pd.DataFrame([vars(d) if hasattr(d, '__dict__') else d for d in device_data_list])

        # CSV 저장
        timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
        csv_file = f'data/raw/lg_{timestamp}_checkpoint.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

        print(f"\n✅ CSV 저장 완료: {csv_file}")
        print(f"\n📊 통계:")
        print(f"  - 총 데이터: {len(df):,}개")
        print(f"  - 가입유형: {df['scrb_type_name'].nunique()}개")
        print(f"  - 요금제: {df['plan_name'].nunique()}개")
        print(f"  - 디바이스: {df['device_nm'].nunique()}개")
        print(f"  - 평균 공시지원금: {df['public_support_fee'].mean():,.0f}원")
        print(f"  - 최대 공시지원금: {df['public_support_fee'].max():,.0f}원")

        # 가입유형별 통계
        print(f"\n가입유형별 데이터:")
        for scrb_type in df['scrb_type_name'].unique():
            count = len(df[df['scrb_type_name'] == scrb_type])
            print(f"  - {scrb_type}: {count:,}개")

        # 샘플 데이터
        print(f"\n📄 샘플 데이터 (상위 5개):")
        print(df[['device_nm', 'plan_name', 'scrb_type_name', 'public_support_fee']].head().to_string(index=False))

    else:
        print("❌ 저장할 데이터가 없습니다.")

except FileNotFoundError:
    print(f"❌ 파일을 찾을 수 없습니다: {checkpoint_file}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
