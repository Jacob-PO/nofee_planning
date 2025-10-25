#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노피 전체 기간 성과 데이터 분석 스크립트
DB 데이터를 분석하여 상세한 성과 보고서를 생성합니다.
"""

import json
from datetime import datetime
from pathlib import Path

def load_db_data():
    """전체 기간 DB 데이터 로드"""
    json_file = Path(__file__).parent / "db-analytics" / f"db_full_period_data_{datetime.now().strftime('%Y%m%d')}.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['data']

def analyze_conversion_rates(data):
    """전환율 분석"""
    total_users = data['total_users']
    total_applications = data['total_applications']
    total_purchases = data['total_purchases']
    total_completed = data['total_completed']

    return {
        "회원가입_대비_신청률": round(total_applications / total_users * 100, 2) if total_users > 0 else 0,
        "신청_대비_구매률": round(total_purchases / total_applications * 100, 2) if total_applications > 0 else 0,
        "신청_대비_개통완료율": round(total_completed / total_applications * 100, 2) if total_applications > 0 else 0,
        "회원가입_대비_구매률": round(total_purchases / total_users * 100, 2) if total_users > 0 else 0,
    }

def analyze_growth_trends(data):
    """성장 추이 분석"""
    weekly_comp = data['weekly_comparison']
    monthly_trend = data['monthly_trend']

    # 최근 3개월 평균
    recent_3months = monthly_trend[-3:] if len(monthly_trend) >= 3 else monthly_trend
    avg_monthly_applications = sum([m['applications'] for m in recent_3months]) / len(recent_3months) if recent_3months else 0

    # 월별 성장률 계산
    monthly_growth_rates = []
    for i in range(1, len(monthly_trend)):
        prev = monthly_trend[i-1]['applications']
        curr = monthly_trend[i]['applications']
        growth_rate = ((curr - prev) / prev * 100) if prev > 0 else 0
        monthly_growth_rates.append({
            "월": monthly_trend[i]['month'],
            "성장률": round(growth_rate, 2)
        })

    return {
        "주간_성장률": round(weekly_comp['growth_rate'], 2),
        "최근_7일_신청": weekly_comp['last_7days'],
        "이전_7일_신청": weekly_comp['prev_7days'],
        "월평균_신청수_최근3개월": round(avg_monthly_applications, 0),
        "월별_추이": monthly_trend,
        "월별_성장률": monthly_growth_rates,
        "전체_기간_일수": len(data['daily_applications_all'])
    }

def analyze_product_performance(data):
    """제품별 성과 분석"""
    top_products = data['top_products']
    total_apps = sum([p['application_count'] for p in top_products])

    products_with_share = []
    for product in top_products:
        products_with_share.append({
            "제품명": product['product_name'],
            "신청수": product['application_count'],
            "점유율": round(product['application_count'] / total_apps * 100, 2) if total_apps > 0 else 0
        })

    return {
        "전체_제품": products_with_share,
        "전체_신청수": total_apps
    }

def analyze_regional_performance(data):
    """지역별 성과 분석"""
    region_stats = data['total_region_stats']
    total = sum([r['count'] for r in region_stats])

    regions_with_share = []
    for region in region_stats:
        regions_with_share.append({
            "지역": region['region'],
            "신청수": region['count'],
            "점유율": round(region['count'] / total * 100, 2) if total > 0 else 0
        })

    # 시군구별 TOP 20
    top_regions_detail = []
    for region in data['top_regions']:
        top_regions_detail.append({
            "지역": region['region'],
            "신청수": region['count']
        })

    return {
        "시도별_전체": regions_with_share,
        "시군구별_top20": top_regions_detail,
        "총_신청수": total
    }

def analyze_carrier_performance(data):
    """통신사별 성과 분석"""
    carrier_stats = data['carrier_stats']
    total = sum([c['count'] for c in carrier_stats])

    carriers_with_share = []
    for carrier in carrier_stats:
        carriers_with_share.append({
            "통신사": carrier['carrier'],
            "신청수": carrier['count'],
            "점유율": round(carrier['count'] / total * 100, 2) if total > 0 else 0
        })

    # 월별 통신사 추이
    carrier_monthly = data['carrier_monthly_trend']

    return {
        "통신사별_통계": carriers_with_share,
        "총_신청수": total,
        "월별_추이": carrier_monthly
    }

def analyze_store_performance(data):
    """매장별 성과 분석"""
    top_stores = data['top_stores']
    total_purchases = sum([s['purchase_count'] for s in top_stores])

    stores_with_share = []
    for store in top_stores:
        stores_with_share.append({
            "매장명": store['store_name'],
            "구매수": store['purchase_count'],
            "점유율": round(store['purchase_count'] / total_purchases * 100, 2) if total_purchases > 0 else 0
        })

    return {
        "매장별_통계": stores_with_share,
        "총_구매수": total_purchases,
        "월별_실적": data['store_monthly_performance']
    }

def analyze_funnel_performance(data):
    """퍼널 성과 분석"""
    quote_funnel = data['quote_application_funnel']
    event_funnel = data['event_application_funnel']
    quote_rates = data['quote_funnel_rates']
    event_rates = data['event_funnel_rates']

    return {
        "견적신청_퍼널": {
            "전체": quote_funnel['total'],
            "신청시작": quote_funnel['step1_신청시작'],
            "상담중": quote_funnel['step2_상담중'],
            "서류제출": quote_funnel['step3_서류제출'],
            "심사중": quote_funnel['step4_심사중'],
            "개통완료": quote_funnel['step5_개통완료'],
            "취소": quote_funnel['step6_취소'],
            "반려": quote_funnel['step7_반려']
        },
        "견적신청_전환율": {
            "상담중_전환율": quote_rates['상담중_rate'],
            "서류제출_전환율": quote_rates['서류제출_rate'],
            "심사중_전환율": quote_rates['심사중_rate'],
            "개통완료_전환율": quote_rates['개통완료_rate'],
            "취소율": quote_rates['취소_rate'],
            "반려율": quote_rates['반려_rate']
        },
        "이벤트신청_퍼널": {
            "전체": event_funnel['total'],
            "신청시작": event_funnel['step1_신청시작'],
            "상담중": event_funnel['step2_상담중'],
            "서류제출": event_funnel['step3_서류제출'],
            "심사중": event_funnel['step4_심사중'],
            "개통완료": event_funnel['step5_개통완료'],
            "취소": event_funnel['step6_취소'],
            "반려": event_funnel['step7_반려']
        },
        "이벤트신청_전환율": {
            "상담중_전환율": event_rates['상담중_rate'],
            "서류제출_전환율": event_rates['서류제출_rate'],
            "심사중_전환율": event_rates['심사중_rate'],
            "개통완료_전환율": event_rates['개통완료_rate'],
            "취소율": event_rates['취소_rate'],
            "반려율": event_rates['반려_rate']
        }
    }

def analyze_time_patterns(data):
    """시간/요일 패턴 분석"""
    hourly = data['hourly_pattern']
    daily = data['daily_pattern']

    # 요일명 매핑 (1=일요일, 2=월요일, ...)
    day_names = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']

    daily_with_names = []
    for d in daily:
        day_index = (d['day_of_week'] - 1) % 7
        daily_with_names.append({
            "요일": day_names[day_index],
            "신청수": d['count']
        })

    # 가장 활발한 시간대
    peak_hour = max(hourly, key=lambda x: x['count'])
    peak_day = max(daily, key=lambda x: x['count'])

    return {
        "시간대별_패턴": hourly,
        "요일별_패턴": daily_with_names,
        "최다_신청_시간": f"{peak_hour['hour']}시",
        "최다_신청_요일": day_names[(peak_day['day_of_week'] - 1) % 7]
    }

def generate_comprehensive_report(data):
    """종합 분석 보고서 생성"""

    report = {
        "생성일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "분석_기간": "전체 기간 (서비스 시작 ~ 현재)",

        "1_핵심지표": {
            "전체_회원수": data['total_users'],
            "전체_신청수": data['total_applications'],
            "견적신청": data['total_quote_applications'],
            "이벤트신청": data['total_event_applications'],
            "전체_구매수": data['total_purchases'],
            "개통완료수": data['total_completed'],
            "등록_매장수": data['total_stores'],
            "활성_캠페인수": data['active_campaigns']
        },

        "2_전환율_분석": analyze_conversion_rates(data),

        "3_성장_추이": analyze_growth_trends(data),

        "4_제품별_성과": analyze_product_performance(data),

        "5_지역별_성과": analyze_regional_performance(data),

        "6_통신사별_성과": analyze_carrier_performance(data),

        "7_매장별_성과": analyze_store_performance(data),

        "8_퍼널_분석": analyze_funnel_performance(data),

        "9_평균_금액": {
            "평균_월_납입금": data['average_pricing']['avg_month_price'],
            "평균_단말기가격": data['average_pricing']['avg_device_price'],
            "평균_할부금": data['average_pricing']['avg_installment'],
            "평균_요금제금액": data['average_pricing']['avg_rate_plan_price']
        },

        "10_사용자_활동": {
            "일일_신규가입": data['user_activity']['daily_signups'],
            "주간_신규가입": data['user_activity']['weekly_signups'],
            "월간_신규가입": data['user_activity']['monthly_signups'],
            "전체_기간_일별_가입_데이터": len(data['daily_signups_all'])
        },

        "11_시간패턴_분석": analyze_time_patterns(data),

        "12_월별_가입자_추이": data['monthly_signups'],

        "원본_데이터": {
            "제조사별_통계": data['manufacturer_stats'],
            "요금대별_통계": data['price_range_stats'],
            "가입유형별_통계": data['join_type_stats'],
            "요금제별_통계": data['rate_plan_stats'][:10],  # TOP 10만
            "상품별_평균금액": data['product_pricing'][:10]  # TOP 10만
        }
    }

    return report

def save_analysis_report(report, filename='full_period_analysis_report.json'):
    """분석 보고서 저장"""
    output_path = Path(__file__).parent / "db-analytics" / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ 전체 기간 분석 보고서 저장 완료: {output_path}")
    return output_path

def print_comprehensive_summary(report):
    """종합 요약 출력"""
    print("\n" + "="*80)
    print("📊 노피(NoFee) 전체 기간 성과 데이터 분석 보고서")
    print("="*80)

    core = report['1_핵심지표']
    print(f"\n【1. 핵심 지표】")
    print(f"  • 전체 회원수: {core['전체_회원수']:,}명")
    print(f"  • 전체 신청수: {core['전체_신청수']:,}건")
    print(f"    - 견적신청: {core['견적신청']:,}건")
    print(f"    - 이벤트신청: {core['이벤트신청']:,}건")
    print(f"  • 전체 구매수: {core['전체_구매수']:,}건")
    print(f"  • 개통완료수: {core['개통완료수']:,}건")
    print(f"  • 등록 매장수: {core['등록_매장수']:,}개")
    print(f"  • 활성 캠페인: {core['활성_캠페인수']:,}개")

    conv = report['2_전환율_분석']
    print(f"\n【2. 전환율】")
    print(f"  • 회원 → 신청: {conv['회원가입_대비_신청률']:.2f}%")
    print(f"  • 신청 → 구매: {conv['신청_대비_구매률']:.2f}%")
    print(f"  • 신청 → 개통완료: {conv['신청_대비_개통완료율']:.2f}%")
    print(f"  • 회원 → 구매: {conv['회원가입_대비_구매률']:.2f}%")

    growth = report['3_성장_추이']
    print(f"\n【3. 성장 추이】")
    print(f"  • 전체 운영 일수: {growth['전체_기간_일수']:,}일")
    print(f"  • 주간 성장률: {growth['주간_성장률']:.2f}%")
    print(f"  • 최근 7일 신청: {growth['최근_7일_신청']:,}건")
    print(f"  • 이전 7일 신청: {growth['이전_7일_신청']:,}건")
    print(f"  • 월평균 신청 (최근 3개월): {growth['월평균_신청수_최근3개월']:.0f}건")

    if growth['월별_성장률']:
        print(f"\n  월별 성장률:")
        for mg in growth['월별_성장률']:
            print(f"    - {mg['월']}: {mg['성장률']:+.1f}%")

    products = report['4_제품별_성과']
    print(f"\n【4. 인기 제품 TOP 10】")
    for i, p in enumerate(products['전체_제품'][:10], 1):
        print(f"  {i:2d}. {p['제품명']:30s} {p['신청수']:4d}건 ({p['점유율']:5.1f}%)")

    regions = report['5_지역별_성과']
    print(f"\n【5. 지역별 신청 (시도)】")
    for r in regions['시도별_전체']:
        print(f"  • {r['지역']:10s} {r['신청수']:4d}건 ({r['점유율']:5.1f}%)")

    print(f"\n【6. 지역별 신청 TOP 10 (시군구)】")
    for i, r in enumerate(regions['시군구별_top20'][:10], 1):
        print(f"  {i:2d}. {r['지역']:20s} {r['신청수']:4d}건")

    carriers = report['6_통신사별_성과']
    print(f"\n【7. 통신사별 신청】")
    for c in carriers['통신사별_통계']:
        print(f"  • {c['통신사']:10s} {c['신청수']:4d}건 ({c['점유율']:5.1f}%)")

    stores = report['7_매장별_성과']
    print(f"\n【8. 매장별 구매 TOP 10】")
    for i, s in enumerate(stores['매장별_통계'][:10], 1):
        print(f"  {i:2d}. {s['매장명']:30s} {s['구매수']:4d}건 ({s['점유율']:5.1f}%)")

    funnel = report['8_퍼널_분석']
    print(f"\n【9. 견적신청 퍼널 전환율】")
    quote_rates = funnel['견적신청_전환율']
    print(f"  • 상담중: {quote_rates['상담중_전환율']:.2f}%")
    print(f"  • 서류제출: {quote_rates['서류제출_전환율']:.2f}%")
    print(f"  • 심사중: {quote_rates['심사중_전환율']:.2f}%")
    print(f"  • 개통완료: {quote_rates['개통완료_전환율']:.2f}%")
    print(f"  • 취소: {quote_rates['취소율']:.2f}%")
    print(f"  • 반려: {quote_rates['반려율']:.2f}%")

    pricing = report['9_평균_금액']
    print(f"\n【10. 평균 금액】")
    print(f"  • 평균 월 납입금: {pricing['평균_월_납입금']:,}원")
    print(f"  • 평균 단말기가격: {pricing['평균_단말기가격']:,}원")
    print(f"  • 평균 할부금: {pricing['평균_할부금']:,}원")
    print(f"  • 평균 요금제: {pricing['평균_요금제금액']:,}원")

    time_patterns = report['11_시간패턴_분석']
    print(f"\n【11. 신청 패턴】")
    print(f"  • 최다 신청 시간대: {time_patterns['최다_신청_시간']}")
    print(f"  • 최다 신청 요일: {time_patterns['최다_신청_요일']}")

    print("\n" + "="*80)

if __name__ == "__main__":
    print("🚀 노피 전체 기간 성과 데이터 분석 시작...")

    # 데이터 로드
    data = load_db_data()

    # 분석 보고서 생성
    report = generate_comprehensive_report(data)

    # 보고서 저장
    save_analysis_report(report)

    # 요약 출력
    print_comprehensive_summary(report)

    print("\n✅ 전체 기간 분석 완료!")
