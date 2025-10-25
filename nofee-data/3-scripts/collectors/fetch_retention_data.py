import pymysql
import json
from datetime import datetime, timedelta
from collections import defaultdict

# DB 연결 정보
DB_CONFIG = {
    'host': '43.203.125.223',
    'port': 3306,
    'user': 'nofee',
    'password': 'HBDyNLZBXZ41TkeZ',
    'database': 'db_nofee',
    'charset': 'utf8mb4'
}

def get_cohort_retention_data():
    """사용자 코호트별 리텐션 및 재방문 데이터 수집"""
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = {}

            # 1. 월별 코호트 리텐션 계산
            print("📊 월별 코호트 리텐션 계산 중...")

            # 가입월별 사용자 리스트와 그들의 활동 이력 조회
            cursor.execute("""
                SELECT
                    u.user_no,
                    DATE_FORMAT(u.created_at, '%Y-%m') as signup_month,
                    u.created_at as signup_date,
                    GROUP_CONCAT(DISTINCT DATE_FORMAT(ap.created_at, '%Y-%m') ORDER BY ap.created_at) as activity_months
                FROM tb_user u
                LEFT JOIN tb_apply_phone ap ON u.user_no = ap.user_no
                WHERE u.created_at >= '2025-07-01'
                GROUP BY u.user_no, DATE_FORMAT(u.created_at, '%Y-%m'), u.created_at
                ORDER BY u.created_at
            """)

            users_cohort = list(cursor.fetchall())

            # 코호트별 리텐션 계산
            cohorts = defaultdict(lambda: {
                'total_users': 0,
                'month_0': 0,  # 가입월
                'month_1': 0,  # 1개월 후
                'month_2': 0,  # 2개월 후
                'month_3': 0   # 3개월 후
            })

            for user in users_cohort:
                signup_month = user['signup_month']
                activity_months = user['activity_months'].split(',') if user['activity_months'] else []

                cohorts[signup_month]['total_users'] += 1

                # 가입월 활동
                if signup_month in activity_months:
                    cohorts[signup_month]['month_0'] += 1

                # 각 월별 리텐션 계산
                signup_date = datetime.strptime(signup_month, '%Y-%m')
                for i in range(1, 4):
                    check_month = (signup_date + timedelta(days=30*i)).strftime('%Y-%m')
                    if check_month in activity_months:
                        cohorts[signup_month][f'month_{i}'] += 1

            # 리텐션율 계산
            cohort_retention = []
            for month, stats in sorted(cohorts.items()):
                if stats['total_users'] > 0:
                    cohort_retention.append({
                        'cohort_month': month,
                        'total_users': stats['total_users'],
                        'month_0_count': stats['month_0'],
                        'month_0_rate': round(stats['month_0'] / stats['total_users'] * 100, 2),
                        'month_1_count': stats['month_1'],
                        'month_1_rate': round(stats['month_1'] / stats['total_users'] * 100, 2),
                        'month_2_count': stats['month_2'],
                        'month_2_rate': round(stats['month_2'] / stats['total_users'] * 100, 2),
                        'month_3_count': stats['month_3'],
                        'month_3_rate': round(stats['month_3'] / stats['total_users'] * 100, 2)
                    })

            data['cohort_retention'] = cohort_retention

            # 2. 사용자별 재방문 간격 분석
            print("📊 사용자별 재방문 간격 분석 중...")
            cursor.execute("""
                SELECT
                    user_no,
                    created_at,
                    LAG(created_at) OVER (PARTITION BY user_no ORDER BY created_at) as prev_activity
                FROM (
                    SELECT DISTINCT user_no, DATE(created_at) as created_at
                    FROM tb_apply_phone
                    WHERE user_no IS NOT NULL
                ) activities
                ORDER BY user_no, created_at
            """)

            revisit_intervals = []
            current_user = None
            user_intervals = []

            for row in cursor.fetchall():
                if row['prev_activity']:
                    interval_days = (row['created_at'] - row['prev_activity']).days
                    revisit_intervals.append(interval_days)

            # 재방문 간격 통계
            if revisit_intervals:
                data['revisit_stats'] = {
                    'avg_revisit_days': round(sum(revisit_intervals) / len(revisit_intervals), 2),
                    'min_revisit_days': min(revisit_intervals),
                    'max_revisit_days': max(revisit_intervals),
                    'total_revisits': len(revisit_intervals)
                }
            else:
                data['revisit_stats'] = {
                    'avg_revisit_days': 0,
                    'min_revisit_days': 0,
                    'max_revisit_days': 0,
                    'total_revisits': 0
                }

            # 3. 재방문 사용자 vs 1회 사용자 비율
            print("📊 재방문 사용자 비율 계산 중...")
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT user_no) as total_active_users,
                    COUNT(DISTINCT CASE WHEN activity_count = 1 THEN user_no END) as one_time_users,
                    COUNT(DISTINCT CASE WHEN activity_count >= 2 THEN user_no END) as returning_users,
                    COUNT(DISTINCT CASE WHEN activity_count >= 3 THEN user_no END) as loyal_users
                FROM (
                    SELECT
                        user_no,
                        COUNT(DISTINCT DATE(created_at)) as activity_count
                    FROM tb_apply_phone
                    WHERE user_no IS NOT NULL
                    GROUP BY user_no
                ) user_activities
            """)

            user_types = cursor.fetchone()
            total = user_types['total_active_users'] or 1

            data['user_engagement'] = {
                'total_active_users': user_types['total_active_users'],
                'one_time_users': user_types['one_time_users'],
                'one_time_rate': round(user_types['one_time_users'] / total * 100, 2),
                'returning_users': user_types['returning_users'],
                'returning_rate': round(user_types['returning_users'] / total * 100, 2),
                'loyal_users': user_types['loyal_users'],
                'loyal_rate': round(user_types['loyal_users'] / total * 100, 2)
            }

            # 4. 주별 활성 사용자 (WAU) 추이
            print("📊 주별 활성 사용자 (WAU) 추이 계산 중...")
            cursor.execute("""
                SELECT
                    YEARWEEK(created_at, 1) as week,
                    DATE(DATE_SUB(created_at, INTERVAL WEEKDAY(created_at) DAY)) as week_start,
                    COUNT(DISTINCT user_no) as active_users
                FROM tb_apply_phone
                WHERE created_at >= '2025-07-01'
                GROUP BY YEARWEEK(created_at, 1), DATE(DATE_SUB(created_at, INTERVAL WEEKDAY(created_at) DAY))
                ORDER BY week
            """)

            data['weekly_active_users'] = list(cursor.fetchall())

            # 5. 일별 활성 사용자 (DAU) 추이
            print("📊 일별 활성 사용자 (DAU) 추이 계산 중...")
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(DISTINCT user_no) as active_users
                FROM tb_apply_phone
                WHERE created_at >= '2025-07-01'
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            data['daily_active_users'] = list(cursor.fetchall())

            # 6. 사용자 활동 빈도 분포
            print("📊 사용자 활동 빈도 분포 계산 중...")
            cursor.execute("""
                SELECT
                    activity_count,
                    COUNT(*) as user_count
                FROM (
                    SELECT
                        user_no,
                        COUNT(*) as activity_count
                    FROM tb_apply_phone
                    WHERE user_no IS NOT NULL
                    GROUP BY user_no
                ) user_activity_counts
                GROUP BY activity_count
                ORDER BY activity_count
            """)

            data['activity_frequency_distribution'] = list(cursor.fetchall())

            # 7. 가입 후 첫 신청까지 소요 시간
            print("📊 가입 후 첫 신청까지 소요 시간 계산 중...")
            cursor.execute("""
                SELECT
                    AVG(days_to_first_apply) as avg_days,
                    MIN(days_to_first_apply) as min_days,
                    MAX(days_to_first_apply) as max_days
                FROM (
                    SELECT
                        u.user_no,
                        TIMESTAMPDIFF(DAY, u.created_at, MIN(ap.created_at)) as days_to_first_apply
                    FROM tb_user u
                    INNER JOIN tb_apply_phone ap ON u.user_no = ap.user_no
                    WHERE u.created_at >= '2025-07-01'
                    GROUP BY u.user_no, u.created_at
                ) first_applies
            """)

            first_apply_stats = cursor.fetchone()
            data['time_to_first_apply'] = {
                'avg_days': round(first_apply_stats['avg_days'] or 0, 2),
                'min_days': first_apply_stats['min_days'] or 0,
                'max_days': first_apply_stats['max_days'] or 0
            }

            # 8. 월별 신규 vs 재방문 사용자
            print("📊 월별 신규 vs 재방문 사용자 계산 중...")
            cursor.execute("""
                SELECT
                    DATE_FORMAT(activity_date, '%Y-%m') as month,
                    COUNT(DISTINCT user_no) as total_active,
                    COUNT(DISTINCT CASE WHEN is_new = 1 THEN user_no END) as new_users,
                    COUNT(DISTINCT CASE WHEN is_new = 0 THEN user_no END) as returning_users
                FROM (
                    SELECT
                        ap.user_no,
                        DATE(ap.created_at) as activity_date,
                        CASE
                            WHEN DATE(ap.created_at) = DATE(u.created_at) THEN 1
                            ELSE 0
                        END as is_new
                    FROM tb_apply_phone ap
                    JOIN tb_user u ON ap.user_no = u.user_no
                    WHERE ap.created_at >= '2025-07-01'
                ) activities
                GROUP BY DATE_FORMAT(activity_date, '%Y-%m')
                ORDER BY month
            """)

            data['monthly_new_vs_returning'] = list(cursor.fetchall())

            print("✅ 리텐션 데이터 수집 완료!")
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

def save_to_json(data, filename='retention_data.json'):
    """데이터를 JSON 파일로 저장"""
    # 모든 데이터를 JSON 직렬화 가능한 형태로 변환
    data = convert_to_serializable(data)

    # 메타데이터 추가
    output = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'database': 'db_nofee',
            'data_type': 'cohort_retention'
        },
        'data': data
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 데이터 저장 완료: {filename}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 NoFee 리텐션 데이터 수집 시작")
    print("="*60)

    data = get_cohort_retention_data()
    save_to_json(data, '/Users/jacob_athometrip/Desktop/dev/nofee/nofee-workspace/nofee-planning/nofee-data/1-raw-data/database/retention_data.json')

    print("\n📈 수집된 리텐션 데이터 요약:")
    print(f"  - 코호트 수: {len(data['cohort_retention'])}개월")
    print(f"  - 전체 활성 사용자: {data['user_engagement']['total_active_users']:,}명")
    print(f"  - 재방문 사용자 비율: {data['user_engagement']['returning_rate']:.1f}%")
    print(f"  - 평균 재방문 간격: {data['revisit_stats']['avg_revisit_days']:.1f}일")
    print(f"  - 가입 후 첫 신청까지: {data['time_to_first_apply']['avg_days']:.1f}일")
