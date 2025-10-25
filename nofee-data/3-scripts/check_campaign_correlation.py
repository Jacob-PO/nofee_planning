import pymysql
import json

# DB 연결 정보
DB_CONFIG = {
    'host': '43.203.125.223',
    'port': 3306,
    'user': 'nofee',
    'password': 'HBDyNLZBXZ41TkeZ',
    'database': 'db_nofee',
    'charset': 'utf8mb4'
}

def check_campaign_correlation():
    """매장별 캠페인(상품) 등록 수와 신청 수신 건수, 구매 전환 상관관계 분석"""
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 매장별 캠페인 수, 신청 수, 구매 수 분석
            print("📊 매장별 캠페인 등록과 성과 상관관계 분석 중...")
            cursor.execute("""
                SELECT
                    s.store_no,
                    COALESCE(s.nickname, CONCAT('매장#', s.store_no)) as store_name,
                    COUNT(DISTINCT c.campaign_no) as campaign_count,
                    COUNT(DISTINCT app.apply_no) as application_count,
                    COUNT(DISTINCT p.purchase_no) as purchase_count,
                    CASE
                        WHEN COUNT(DISTINCT app.apply_no) > 0
                        THEN ROUND(COUNT(DISTINCT p.purchase_no) * 100.0 / COUNT(DISTINCT app.apply_no), 2)
                        ELSE 0
                    END as conversion_rate
                FROM tb_store s
                LEFT JOIN tb_campaign_phone c ON s.store_no = c.store_no AND c.deleted_yn = 'N'
                LEFT JOIN (
                    SELECT store_no, apply_no FROM tb_apply_phone
                    UNION ALL
                    SELECT store_no, apply_no FROM tb_apply_campaign_phone
                ) app ON s.store_no = app.store_no
                LEFT JOIN tb_store_purchase p ON s.store_no = p.store_no AND p.deleted_yn = 'N'
                WHERE s.store_no IS NOT NULL
                GROUP BY s.store_no, s.nickname
                HAVING application_count > 0
                ORDER BY campaign_count DESC, application_count DESC
                LIMIT 30
            """)
            stores_data = cursor.fetchall()

            print("\n=== 매장별 캠페인 수와 성과 분석 ===\n")

            # 캠페인 많은 매장 vs 적은 매장 비교
            high_campaign_stores = [s for s in stores_data if s['campaign_count'] >= 10]
            low_campaign_stores = [s for s in stores_data if s['campaign_count'] < 10]

            print(f"캠페인 10개 이상 매장 ({len(high_campaign_stores)}개):")
            if high_campaign_stores:
                avg_app = sum(s['application_count'] for s in high_campaign_stores) / len(high_campaign_stores)
                avg_purchase = sum(s['purchase_count'] for s in high_campaign_stores) / len(high_campaign_stores)
                avg_conversion = sum(s['conversion_rate'] for s in high_campaign_stores) / len(high_campaign_stores)
                print(f"  - 평균 신청 수: {avg_app:.1f}건")
                print(f"  - 평균 구매 수: {avg_purchase:.1f}건")
                print(f"  - 평균 전환율: {avg_conversion:.1f}%")
                print()

            print(f"캠페인 10개 미만 매장 ({len(low_campaign_stores)}개):")
            if low_campaign_stores:
                avg_app = sum(s['application_count'] for s in low_campaign_stores) / len(low_campaign_stores)
                avg_purchase = sum(s['purchase_count'] for s in low_campaign_stores) / len(low_campaign_stores)
                avg_conversion = sum(s['conversion_rate'] for s in low_campaign_stores) / len(low_campaign_stores)
                print(f"  - 평균 신청 수: {avg_app:.1f}건")
                print(f"  - 평균 구매 수: {avg_purchase:.1f}건")
                print(f"  - 평균 전환율: {avg_conversion:.1f}%")
                print()

            # 상위 매장 상세 출력
            print("\n=== TOP 20 매장 상세 ===\n")
            for idx, store in enumerate(stores_data[:20], 1):
                print(f"{idx}. {store['store_name']}")
                print(f"   - 등록 캠페인: {store['campaign_count']}개")
                print(f"   - 총 신청: {store['application_count']}건")
                print(f"   - 총 구매: {store['purchase_count']}건")
                print(f"   - 전환율: {store['conversion_rate']:.1f}%")
                print()

            # 캠페인 0개인 매장 통계
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT s.store_no) as store_count,
                    COUNT(DISTINCT app.apply_no) as total_applications,
                    COUNT(DISTINCT p.purchase_no) as total_purchases
                FROM tb_store s
                LEFT JOIN tb_campaign_phone c ON s.store_no = c.store_no AND c.deleted_yn = 'N'
                LEFT JOIN (
                    SELECT store_no, apply_no FROM tb_apply_phone
                    UNION ALL
                    SELECT store_no, apply_no FROM tb_apply_campaign_phone
                ) app ON s.store_no = app.store_no
                LEFT JOIN tb_store_purchase p ON s.store_no = p.store_no AND p.deleted_yn = 'N'
                WHERE c.campaign_no IS NULL
                GROUP BY (c.campaign_no IS NULL)
            """)
            no_campaign = cursor.fetchone()

            if no_campaign:
                print("\n=== 캠페인 미등록 매장 통계 ===")
                print(f"매장 수: {no_campaign['store_count']}개")
                print(f"총 신청: {no_campaign['total_applications']}건")
                print(f"총 구매: {no_campaign['total_purchases']}건")
                if no_campaign['store_count'] > 0:
                    avg_app = no_campaign['total_applications'] / no_campaign['store_count']
                    avg_purchase = no_campaign['total_purchases'] / no_campaign['store_count']
                    print(f"매장당 평균 신청: {avg_app:.1f}건")
                    print(f"매장당 평균 구매: {avg_purchase:.1f}건")

            return {
                'high_campaign': high_campaign_stores,
                'low_campaign': low_campaign_stores,
                'no_campaign': no_campaign,
                'all_stores': stores_data
            }

    finally:
        connection.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 캠페인 등록과 성과 상관관계 분석")
    print("="*60)

    results = check_campaign_correlation()

    print("\n✅ 분석 완료!")
