import pymysql
import json
from datetime import datetime, timedelta

# DB 연결 정보
DB_CONFIG = {
    'host': '43.203.125.223',
    'port': 3306,
    'user': 'nofee',
    'password': 'HBDyNLZBXZ41TkeZ',
    'database': 'db_nofee',
    'charset': 'utf8mb4'
}

def get_db_data_all():
    """DB에서 전체 기간 주요 비즈니스 지표 수집"""
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = {}

            # 1. 전체 통계
            print("📊 전체 통계 수집 중...")
            cursor.execute("SELECT COUNT(*) as count FROM tb_user")
            data['total_users'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM tb_apply_phone")
            data['total_quote_applications'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM tb_apply_campaign_phone")
            data['total_event_applications'] = cursor.fetchone()['count']

            data['total_applications'] = data['total_quote_applications'] + data['total_event_applications']

            # 구매수 (tb_store_purchase 기준)
            cursor.execute("SELECT COUNT(*) as count FROM tb_store_purchase WHERE deleted_yn = 'N'")
            data['total_purchases'] = cursor.fetchone()['count']

            # 개통완료수 (step_code = 0201005)
            cursor.execute("SELECT COUNT(*) as count FROM tb_apply_phone WHERE step_code = '0201005'")
            data['total_quote_completed'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM tb_apply_campaign_phone WHERE step_code = '0201005'")
            data['total_event_completed'] = cursor.fetchone()['count']

            data['total_completed'] = data['total_quote_completed'] + data['total_event_completed']

            cursor.execute("SELECT COUNT(*) as count FROM tb_store")
            data['total_stores'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM tb_campaign_phone WHERE deleted_yn = 'N'")
            data['active_campaigns'] = cursor.fetchone()['count']

            # 2. 전체 기간 일별 견적신청 추이
            print("📈 전체 기간 일별 견적신청 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM tb_apply_phone
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            data['daily_quote_applications_all'] = list(cursor.fetchall())

            # 3. 전체 기간 일별 이벤트신청 추이
            print("📈 전체 기간 일별 이벤트신청 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM tb_apply_campaign_phone
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            data['daily_event_applications_all'] = list(cursor.fetchall())

            # 4. 전체 기간 일별 전체신청 추이
            print("📈 전체 기간 일별 전체신청 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM (
                    SELECT created_at FROM tb_apply_phone
                    UNION ALL
                    SELECT created_at FROM tb_apply_campaign_phone
                ) combined
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            data['daily_applications_all'] = list(cursor.fetchall())

            # 5. 전체 기간 일별 가입 추이
            print("👥 전체 기간 일별 가입 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM tb_user
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            data['daily_signups_all'] = list(cursor.fetchall())

            # 6. 가입 유형별 통계
            print("📋 가입 유형별 통계 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.apply_join_type_code) as join_type,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_join_type_code = cc.code
                WHERE ap.apply_join_type_code IS NOT NULL
                GROUP BY ap.apply_join_type_code, cc.nm_ko
                ORDER BY count DESC
            """)
            data['join_type_stats'] = list(cursor.fetchall())

            # 7. 통신사별 신청 통계
            print("📱 통신사별 신청 통계 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.apply_carrier_code) as carrier,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_carrier_code = cc.code
                WHERE ap.apply_carrier_code IS NOT NULL AND ap.apply_carrier_code != ''
                GROUP BY ap.apply_carrier_code, cc.nm_ko
                ORDER BY count DESC
            """)
            data['carrier_stats'] = list(cursor.fetchall())

            # 8. 인기 제품 TOP 20
            print("🏆 인기 제품 TOP 20 수집 중...")
            cursor.execute("""
                SELECT
                    pgp.product_group_nm as product_name,
                    COUNT(ap.apply_no) as application_count
                FROM tb_apply_phone ap
                JOIN tb_product_group_phone pgp ON ap.apply_product_group_code = pgp.product_group_code
                WHERE pgp.product_group_nm IS NOT NULL
                GROUP BY pgp.product_group_nm
                ORDER BY application_count DESC
                LIMIT 20
            """)
            data['top_products'] = list(cursor.fetchall())

            # 9. 매장별 구매 통계 TOP 20
            print("🏪 매장별 구매 통계 TOP 20 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(s.nickname, CONCAT('매장#', s.store_no)) as store_name,
                    COUNT(sp.purchase_no) as purchase_count
                FROM tb_store_purchase sp
                JOIN tb_store s ON sp.store_no = s.store_no
                GROUP BY s.store_no, s.nickname
                ORDER BY purchase_count DESC
                LIMIT 20
            """)
            data['top_stores'] = list(cursor.fetchall())

            # 10. 지역별 신청 통계 (전체)
            print("🗺️  지역별 신청 통계 수집 중...")
            cursor.execute("""
                SELECT
                    apply_sido_nm as region,
                    COUNT(*) as count
                FROM (
                    SELECT apply_sido_nm FROM tb_apply_phone WHERE apply_sido_nm IS NOT NULL AND apply_sido_nm != ''
                    UNION ALL
                    SELECT apply_sido_nm FROM tb_apply_campaign_phone WHERE apply_sido_nm IS NOT NULL AND apply_sido_nm != ''
                ) combined
                GROUP BY apply_sido_nm
                ORDER BY count DESC
            """)
            data['total_region_stats'] = list(cursor.fetchall())

            # 시군구별 TOP 20
            cursor.execute("""
                SELECT
                    CONCAT(apply_sido_nm, ' ', apply_sigungu_nm) as region,
                    COUNT(*) as count
                FROM (
                    SELECT apply_sido_nm, apply_sigungu_nm FROM tb_apply_phone
                    WHERE apply_sido_nm IS NOT NULL AND apply_sigungu_nm IS NOT NULL
                    UNION ALL
                    SELECT apply_sido_nm, apply_sigungu_nm FROM tb_apply_campaign_phone
                    WHERE apply_sido_nm IS NOT NULL AND apply_sigungu_nm IS NOT NULL
                ) combined
                GROUP BY apply_sido_nm, apply_sigungu_nm
                ORDER BY count DESC
                LIMIT 20
            """)
            data['top_regions'] = list(cursor.fetchall())

            # 11. 최근 7일 vs 이전 7일 비교
            print("📊 주간 비교 통계 수집 중...")
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as last_7days,
                    SUM(CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                        AND created_at < DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as prev_7days
                FROM tb_apply_phone
            """)
            weekly_data = cursor.fetchone()
            data['weekly_comparison'] = {
                'last_7days': weekly_data['last_7days'] or 0,
                'prev_7days': weekly_data['prev_7days'] or 0,
                'growth_rate': ((weekly_data['last_7days'] or 0) - (weekly_data['prev_7days'] or 0)) / (weekly_data['prev_7days'] or 1) * 100 if weekly_data['prev_7days'] else 0
            }

            # 12. 전환 퍼널 데이터
            print("🔄 전환 퍼널 분석 중...")
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT u.user_no) as total_users,
                    COUNT(DISTINCT ap.user_no) as applied_users,
                    SUM(CASE WHEN ap.step_code = '0201005' THEN 1 ELSE 0 END) as completed_applications,
                    COUNT(DISTINCT sp.apply_no) as purchased_applications
                FROM tb_user u
                LEFT JOIN tb_apply_phone ap ON u.user_no = ap.user_no
                LEFT JOIN tb_store_purchase sp ON ap.apply_no = sp.apply_no AND sp.deleted_yn = 'N'
            """)
            funnel = cursor.fetchone()
            data['conversion_funnel'] = {
                'total_users': funnel['total_users'] or 0,
                'applied_users': funnel['applied_users'] or 0,
                'completed_applications': funnel['completed_applications'] or 0,
                'purchased_applications': funnel['purchased_applications'] or 0,
                'application_rate': (funnel['applied_users'] / funnel['total_users'] * 100) if funnel['total_users'] else 0,
                'completion_rate': (funnel['completed_applications'] / data['total_applications'] * 100) if data['total_applications'] else 0,
                'purchase_rate': (funnel['purchased_applications'] / data['total_applications'] * 100) if data['total_applications'] else 0
            }

            # 13. 평균 금액 데이터
            print("💵 평균 금액 데이터 수집 중...")
            cursor.execute("""
                SELECT
                    AVG(apply_month_price) as avg_month_price,
                    AVG(apply_month_device_price) as avg_device_price,
                    AVG(apply_installment_principal) as avg_installment,
                    AVG(apply_month_rate_plan_price) as avg_rate_plan_price
                FROM tb_apply_phone
                WHERE apply_month_price > 0
            """)
            pricing = cursor.fetchone()
            data['average_pricing'] = {
                'avg_month_price': int(pricing['avg_month_price'] or 0),
                'avg_device_price': int(pricing['avg_device_price'] or 0),
                'avg_installment': int(pricing['avg_installment'] or 0),
                'avg_rate_plan_price': int(pricing['avg_rate_plan_price'] or 0)
            }

            # 14. 제조사별 통계
            print("📱 제조사별 통계 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.apply_manufacturer_code) as manufacturer,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_manufacturer_code = cc.code
                WHERE ap.apply_manufacturer_code IS NOT NULL AND ap.apply_manufacturer_code != ''
                GROUP BY ap.apply_manufacturer_code, cc.nm_ko
                ORDER BY count DESC
            """)
            data['manufacturer_stats'] = list(cursor.fetchall())

            # 15. 요금대별 통계
            print("💰 요금대별 통계 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.apply_price_range_code) as price_range,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_price_range_code = cc.code
                WHERE ap.apply_price_range_code IS NOT NULL AND ap.apply_price_range_code != ''
                GROUP BY ap.apply_price_range_code, cc.nm_ko
                ORDER BY count DESC
            """)
            data['price_range_stats'] = list(cursor.fetchall())

            # 16. 시간대별 신청 패턴
            print("⏰ 시간대별 신청 패턴 수집 중...")
            cursor.execute("""
                SELECT
                    HOUR(created_at) as hour,
                    COUNT(*) as count
                FROM tb_apply_phone
                GROUP BY HOUR(created_at)
                ORDER BY hour
            """)
            data['hourly_pattern'] = list(cursor.fetchall())

            # 17. 요일별 신청 패턴
            print("📅 요일별 신청 패턴 수집 중...")
            cursor.execute("""
                SELECT
                    DAYOFWEEK(created_at) as day_of_week,
                    COUNT(*) as count
                FROM tb_apply_phone
                GROUP BY DAYOFWEEK(created_at)
                ORDER BY day_of_week
            """)
            data['daily_pattern'] = list(cursor.fetchall())

            # 18. 전체 기간 월별 성과 트렌드
            print("📈 전체 기간 월별 성과 트렌드 수집 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(created_at, '%Y-%m') as month,
                    COUNT(*) as applications,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as completed
                FROM tb_apply_phone
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month
            """)
            data['monthly_trend'] = list(cursor.fetchall())

            # 19. 단계별 신청 현황
            print("📊 단계별 신청 현황 수집 중...")
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.step_code) as step_name,
                    ap.step_code,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.step_code = cc.code
                GROUP BY ap.step_code, cc.nm_ko
                ORDER BY ap.step_code
            """)
            data['application_steps'] = list(cursor.fetchall())

            # 이벤트 신청 단계별 현황
            cursor.execute("""
                SELECT
                    COALESCE(cc.nm_ko, ap.step_code) as step_name,
                    ap.step_code,
                    COUNT(*) as count
                FROM tb_apply_campaign_phone ap
                LEFT JOIN tb_common_code cc ON ap.step_code = cc.code
                GROUP BY ap.step_code, cc.nm_ko
                ORDER BY ap.step_code
            """)
            data['event_application_steps'] = list(cursor.fetchall())

            # 20. 전체 기간 월별 회원 가입 추이
            print("📊 전체 기간 월별 회원 가입 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(created_at, '%Y-%m') as month,
                    COUNT(*) as count
                FROM tb_user
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month
            """)
            data['monthly_signups'] = list(cursor.fetchall())

            # 21. 매장별 월별 실적 (전체 기간)
            print("📊 매장별 전체 기간 월별 실적 수집 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(sp.created_at, '%Y-%m') as month,
                    COALESCE(s.nickname, CONCAT('매장#', s.store_no)) as store_name,
                    COUNT(*) as purchase_count
                FROM tb_store_purchase sp
                JOIN tb_store s ON sp.store_no = s.store_no
                WHERE sp.deleted_yn = 'N'
                GROUP BY DATE_FORMAT(sp.created_at, '%Y-%m'), s.store_no, s.nickname
                ORDER BY month DESC, purchase_count DESC
            """)
            data['store_monthly_performance'] = list(cursor.fetchall())

            # 22. 상품별 평균 금액
            print("💰 상품별 평균 금액 수집 중...")
            cursor.execute("""
                SELECT
                    pgp.product_group_nm as product_name,
                    COUNT(ap.apply_no) as application_count,
                    AVG(ap.apply_month_price) as avg_month_price,
                    AVG(ap.apply_month_device_price) as avg_device_price,
                    AVG(ap.apply_installment_principal) as avg_installment
                FROM tb_apply_phone ap
                JOIN tb_product_group_phone pgp ON ap.apply_product_group_code = pgp.product_group_code
                WHERE pgp.product_group_nm IS NOT NULL
                GROUP BY pgp.product_group_nm
                ORDER BY application_count DESC
                LIMIT 30
            """)
            data['product_pricing'] = list(cursor.fetchall())

            # 23. 요금제별 통계
            print("📊 요금제별 통계 수집 중...")
            cursor.execute("""
                SELECT
                    rp.rate_plan_nm as rate_plan_name,
                    COUNT(ap.apply_no) as count,
                    AVG(ap.apply_month_rate_plan_price) as avg_price
                FROM tb_apply_phone ap
                JOIN tb_rate_plan_phone rp ON ap.apply_rate_plan_code = rp.rate_plan_code
                WHERE rp.rate_plan_nm IS NOT NULL
                GROUP BY rp.rate_plan_nm
                ORDER BY count DESC
                LIMIT 30
            """)
            data['rate_plan_stats'] = list(cursor.fetchall())

            # 24. 통신사별 전체 기간 월별 추이
            print("📊 통신사별 전체 기간 월별 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(ap.created_at, '%Y-%m') as month,
                    COALESCE(cc.nm_ko, ap.apply_carrier_code) as carrier,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_carrier_code = cc.code
                GROUP BY DATE_FORMAT(ap.created_at, '%Y-%m'), ap.apply_carrier_code, cc.nm_ko
                ORDER BY month, count DESC
            """)
            data['carrier_monthly_trend'] = list(cursor.fetchall())

            # 25. 가입유형별 전체 기간 월별 추이
            print("📊 가입유형별 전체 기간 월별 추이 수집 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(ap.created_at, '%Y-%m') as month,
                    COALESCE(cc.nm_ko, ap.apply_join_type_code) as join_type,
                    COUNT(*) as count
                FROM tb_apply_phone ap
                LEFT JOIN tb_common_code cc ON ap.apply_join_type_code = cc.code
                GROUP BY DATE_FORMAT(ap.created_at, '%Y-%m'), ap.apply_join_type_code, cc.nm_ko
                ORDER BY month, count DESC
            """)
            data['join_type_monthly_trend'] = list(cursor.fetchall())

            # 26. 상세 퍼널 분석
            print("📊 상세 퍼널 분석 중...")
            # 견적신청 상세 퍼널
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN step_code >= '0201001' THEN 1 ELSE 0 END) as step1_신청시작,
                    SUM(CASE WHEN step_code >= '0201002' THEN 1 ELSE 0 END) as step2_상담중,
                    SUM(CASE WHEN step_code >= '0201003' THEN 1 ELSE 0 END) as step3_서류제출,
                    SUM(CASE WHEN step_code >= '0201004' THEN 1 ELSE 0 END) as step4_심사중,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as step5_개통완료,
                    SUM(CASE WHEN step_code = '0201006' THEN 1 ELSE 0 END) as step6_취소,
                    SUM(CASE WHEN step_code = '0201007' THEN 1 ELSE 0 END) as step7_반려
                FROM tb_apply_phone
            """)
            quote_funnel = cursor.fetchone()
            data['quote_application_funnel'] = quote_funnel

            # 이벤트신청 상세 퍼널
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN step_code >= '0201001' THEN 1 ELSE 0 END) as step1_신청시작,
                    SUM(CASE WHEN step_code >= '0201002' THEN 1 ELSE 0 END) as step2_상담중,
                    SUM(CASE WHEN step_code >= '0201003' THEN 1 ELSE 0 END) as step3_서류제출,
                    SUM(CASE WHEN step_code >= '0201004' THEN 1 ELSE 0 END) as step4_심사중,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as step5_개통완료,
                    SUM(CASE WHEN step_code = '0201006' THEN 1 ELSE 0 END) as step6_취소,
                    SUM(CASE WHEN step_code = '0201007' THEN 1 ELSE 0 END) as step7_반려
                FROM tb_apply_campaign_phone
            """)
            event_funnel = cursor.fetchone()
            data['event_application_funnel'] = event_funnel

            # 퍼널 전환율 계산
            data['quote_funnel_rates'] = {
                'total': quote_funnel['total'],
                '신청시작': 100.0,
                '상담중_rate': (quote_funnel['step2_상담중'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
                '서류제출_rate': (quote_funnel['step3_서류제출'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
                '심사중_rate': (quote_funnel['step4_심사중'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
                '개통완료_rate': (quote_funnel['step5_개통완료'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
                '취소_rate': (quote_funnel['step6_취소'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
                '반려_rate': (quote_funnel['step7_반려'] / quote_funnel['total'] * 100) if quote_funnel['total'] > 0 else 0,
            }

            data['event_funnel_rates'] = {
                'total': event_funnel['total'],
                '신청시작': 100.0,
                '상담중_rate': (event_funnel['step2_상담중'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
                '서류제출_rate': (event_funnel['step3_서류제출'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
                '심사중_rate': (event_funnel['step4_심사중'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
                '개통완료_rate': (event_funnel['step5_개통완료'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
                '취소_rate': (event_funnel['step6_취소'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
                '반려_rate': (event_funnel['step7_반려'] / event_funnel['total'] * 100) if event_funnel['total'] > 0 else 0,
            }

            # 27. 유저 활동 통계
            print("📊 유저 활동 통계 수집 중...")
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT user_no) as total_users,
                    COUNT(DISTINCT CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN user_no END) as weekly_signups,
                    COUNT(DISTINCT CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN user_no END) as monthly_signups,
                    COUNT(DISTINCT CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN user_no END) as daily_signups
                FROM tb_user
            """)
            data['user_activity'] = cursor.fetchone()

            # 28. 신청 완료까지 평균 소요 시간
            print("📊 신청 완료까지 평균 소요 시간 수집 중...")
            cursor.execute("""
                SELECT
                    AVG(TIMESTAMPDIFF(DAY, created_at, modified_at)) as avg_days_to_complete
                FROM tb_apply_phone
                WHERE step_code = '0201005' AND modified_at IS NOT NULL
            """)
            result = cursor.fetchone()
            data['avg_completion_days'] = result['avg_days_to_complete'] if result else 0

            # 29. 디바이스별 통계
            print("📊 디바이스별 통계 수집 중...")
            cursor.execute("""
                SELECT
                    pgp.product_group_nm as device_name,
                    COUNT(ap.apply_no) as count,
                    AVG(ap.apply_month_device_price) as avg_device_price,
                    AVG(ap.apply_installment_principal) as avg_installment
                FROM tb_apply_phone ap
                JOIN tb_product_group_phone pgp ON ap.apply_product_group_code = pgp.product_group_code
                WHERE pgp.product_group_nm IS NOT NULL
                GROUP BY pgp.product_group_nm
                ORDER BY count DESC
                LIMIT 30
            """)
            data['device_stats'] = list(cursor.fetchall())

            print("✅ 모든 데이터 수집 완료!")
            return data

    finally:
        connection.close()

def convert_to_serializable(obj):
    """재귀적으로 JSON 직렬화 불가능한 객체 변환"""
    import datetime as dt
    from decimal import Decimal

    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (datetime, dt.date)):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def save_to_json(data, filename='db_data_all.json'):
    """데이터를 JSON 파일로 저장"""
    # 모든 데이터를 JSON 직렬화 가능한 형태로 변환
    data = convert_to_serializable(data)

    # 메타데이터 추가
    output = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'database': 'db_nofee',
            'period': 'all'
        },
        'data': data
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 데이터 저장 완료: {filename}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 NoFee 전체 기간 DB 데이터 수집 시작")
    print("="*60)

    data = get_db_data_all()
    save_to_json(data)

    print("\n📈 수집된 데이터 요약:")
    print(f"  - 전체 회원: {data['total_users']:,}명")
    print(f"  - 전체 신청: {data['total_applications']:,}건")
    print(f"  - 전체 구매: {data['total_purchases']:,}건")
    print(f"  - 전체 매장: {data['total_stores']:,}개")
    print(f"  - 활성 캠페인: {data['active_campaigns']:,}개")
    print(f"\n  - 최근 7일 신청: {data['weekly_comparison']['last_7days']:,}건")
    print(f"  - 이전 7일 대비: {data['weekly_comparison']['growth_rate']:.1f}%")
    print(f"\n  - 전체 기간 일별 데이터: {len(data['daily_applications_all']):,}일")
    print(f"  - 전체 기간 월별 데이터: {len(data['monthly_trend']):,}개월")
