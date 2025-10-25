import pymysql
import json
from datetime import datetime

# DB 연결 정보
DB_CONFIG = {
    'host': '43.203.125.223',
    'port': 3306,
    'user': 'nofee',
    'password': 'HBDyNLZBXZ41TkeZ',
    'database': 'db_nofee',
    'charset': 'utf8mb4'
}

def check_store_performance():
    """매장별 신청 수신 현황 분석 - 가장 많이 받은 매장 확인"""
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 매장별 전체 신청 수 (견적 + 이벤트)
            print("📊 매장별 신청 수신 현황 분석 중...")
            cursor.execute("""
                SELECT
                    s.store_no,
                    COALESCE(s.nickname, CONCAT('매장#', s.store_no)) as store_name,
                    s.created_at as store_joined_date,
                    COUNT(*) as total_applications,
                    DATEDIFF(CURDATE(), s.created_at) as days_active
                FROM tb_store s
                LEFT JOIN (
                    SELECT store_no, created_at FROM tb_apply_phone
                    UNION ALL
                    SELECT store_no, created_at FROM tb_apply_campaign_phone
                ) applications ON s.store_no = applications.store_no
                WHERE s.store_no IS NOT NULL
                GROUP BY s.store_no, s.nickname, s.created_at
                HAVING total_applications > 0
                ORDER BY total_applications DESC
                LIMIT 20
            """)
            top_stores = cursor.fetchall()

            print("\n=== TOP 20 매장별 신청 수신 현황 ===\n")
            for idx, store in enumerate(top_stores, 1):
                daily_avg = store['total_applications'] / store['days_active'] if store['days_active'] > 0 else 0
                print(f"{idx}. {store['store_name']}")
                print(f"   - 총 신청: {store['total_applications']:,}건")
                print(f"   - 활동 기간: {store['days_active']}일")
                print(f"   - 하루 평균: {daily_avg:.1f}건")
                print(f"   - 가입일: {store['store_joined_date']}")
                print()

            # 가장 많이 받은 매장 상세 정보
            if top_stores:
                top_store = top_stores[0]
                daily_avg = top_store['total_applications'] / top_store['days_active'] if top_store['days_active'] > 0 else 0

                print("\n" + "="*60)
                print("🏆 최다 신청 수신 매장")
                print("="*60)
                print(f"매장명: {top_store['store_name']}")
                print(f"총 신청: {top_store['total_applications']:,}건")
                print(f"활동 기간: {top_store['days_active']}일")
                print(f"하루 평균: {daily_avg:.1f}건")
                print(f"가입일: {top_store['store_joined_date']}")
                print()

                # 해당 매장의 월별 추이
                cursor.execute("""
                    SELECT
                        DATE_FORMAT(created_at, '%%Y-%%m') as month,
                        COUNT(*) as count
                    FROM (
                        SELECT created_at FROM tb_apply_phone WHERE store_no = %s
                        UNION ALL
                        SELECT created_at FROM tb_apply_campaign_phone WHERE store_no = %s
                    ) applications
                    GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
                    ORDER BY month
                """, (top_store['store_no'], top_store['store_no']))
                monthly_trend = cursor.fetchall()

                print("월별 신청 추이:")
                for month_data in monthly_trend:
                    print(f"  {month_data['month']}: {month_data['count']:,}건")

            return {
                'top_stores': top_stores,
                'top_store': top_store if top_stores else None,
                'daily_avg': daily_avg if top_stores else 0
            }

    finally:
        connection.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 매장별 신청 수신 현황 분석")
    print("="*60)

    results = check_store_performance()

    print("\n✅ 분석 완료!")
