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

def check_activation_info():
    """개통정보 입력 여부에 따른 전환율 분석"""
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 먼저 tb_apply_phone 테이블 구조 확인
            print("📊 tb_apply_phone 테이블 구조 확인...")
            cursor.execute("DESCRIBE tb_apply_phone")
            columns = cursor.fetchall()

            print("\n테이블 컬럼 목록:")
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']}")

            # 개통정보 관련 필드 찾기
            print("\n\n🔍 개통정보 관련 필드 검색 중...")

            # 견적신청 테이블에서 개통정보 필드 확인 (open_info_yn)
            cursor.execute("""
                SELECT
                    open_info_yn,
                    COUNT(*) as count
                FROM tb_apply_phone
                GROUP BY open_info_yn
            """)
            sample_data = cursor.fetchall()
            print("\n견적신청 open_info_yn 분포:")
            for row in sample_data:
                print(f"  {row}")

            # 개통정보 입력 여부에 따른 전환율 비교 (견적신청)
            print("\n\n📊 견적신청: 개통정보 입력 여부별 전환율 분석...")
            cursor.execute("""
                SELECT
                    COALESCE(open_info_yn, 'N') as has_activation_info,
                    COUNT(*) as total_applications,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN step_code = '0201006' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN step_code = '0201007' THEN 1 ELSE 0 END) as rejected
                FROM tb_apply_phone
                GROUP BY open_info_yn
            """)
            quote_results = cursor.fetchall()

            print("\n견적신청 결과:")
            for row in quote_results:
                completion_rate = (row['completed'] / row['total_applications'] * 100) if row['total_applications'] > 0 else 0
                print(f"\n  개통정보 입력: {row['has_activation_info']}")
                print(f"    - 총 신청: {row['total_applications']:,}건")
                print(f"    - 개통완료: {row['completed']:,}건")
                print(f"    - 취소: {row['cancelled']:,}건")
                print(f"    - 반려: {row['rejected']:,}건")
                print(f"    - 개통완료율: {completion_rate:.2f}%")

            # 이벤트신청 테이블 구조 확인
            print("\n\n📊 tb_apply_campaign_phone 테이블 구조 확인...")
            cursor.execute("DESCRIBE tb_apply_campaign_phone")
            event_columns = cursor.fetchall()

            print("\n테이블 컬럼 목록:")
            for col in event_columns:
                print(f"  - {col['Field']}: {col['Type']}")

            # 개통정보 입력 여부에 따른 전환율 비교 (이벤트신청)
            print("\n\n📊 이벤트신청: 개통정보 입력 여부별 전환율 분석...")
            cursor.execute("""
                SELECT
                    COALESCE(open_info_yn, 'N') as has_activation_info,
                    COUNT(*) as total_applications,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN step_code = '0201006' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN step_code = '0201007' THEN 1 ELSE 0 END) as rejected
                FROM tb_apply_campaign_phone
                GROUP BY open_info_yn
            """)
            event_results = cursor.fetchall()

            print("\n이벤트신청 결과:")
            for row in event_results:
                completion_rate = (row['completed'] / row['total_applications'] * 100) if row['total_applications'] > 0 else 0
                print(f"\n  개통정보 입력: {row['has_activation_info']}")
                print(f"    - 총 신청: {row['total_applications']:,}건")
                print(f"    - 개통완료: {row['completed']:,}건")
                print(f"    - 취소: {row['cancelled']:,}건")
                print(f"    - 반려: {row['rejected']:,}건")
                print(f"    - 개통완료율: {completion_rate:.2f}%")

            # 전체 합산 (견적신청 + 이벤트신청)
            print("\n\n📊 전체 신청: 개통정보 입력 여부별 전환율 분석...")
            cursor.execute("""
                SELECT
                    COALESCE(open_info_yn, 'N') as has_activation_info,
                    COUNT(*) as total_applications,
                    SUM(CASE WHEN step_code = '0201005' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN step_code = '0201006' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN step_code = '0201007' THEN 1 ELSE 0 END) as rejected
                FROM (
                    SELECT open_info_yn, step_code FROM tb_apply_phone
                    UNION ALL
                    SELECT open_info_yn, step_code FROM tb_apply_campaign_phone
                ) combined
                GROUP BY open_info_yn
            """)
            combined_results = cursor.fetchall()

            print("\n전체 신청 결과:")
            results_summary = {}
            for row in combined_results:
                completion_rate = (row['completed'] / row['total_applications'] * 100) if row['total_applications'] > 0 else 0
                print(f"\n  개통정보 입력: {row['has_activation_info']}")
                print(f"    - 총 신청: {row['total_applications']:,}건")
                print(f"    - 개통완료: {row['completed']:,}건")
                print(f"    - 취소: {row['cancelled']:,}건")
                print(f"    - 반려: {row['rejected']:,}건")
                print(f"    - 개통완료율: {completion_rate:.2f}%")

                results_summary[row['has_activation_info']] = {
                    'total_applications': row['total_applications'],
                    'completed': row['completed'],
                    'cancelled': row['cancelled'],
                    'rejected': row['rejected'],
                    'completion_rate': completion_rate
                }

            # 개선율 계산
            if 'Y' in results_summary and 'N' in results_summary:
                improvement = results_summary['Y']['completion_rate'] - results_summary['N']['completion_rate']
                improvement_pct = (improvement / results_summary['N']['completion_rate'] * 100) if results_summary['N']['completion_rate'] > 0 else 0

                print(f"\n\n✅ 개통정보 입력 효과:")
                print(f"  - 개통정보 미입력 시: {results_summary['N']['completion_rate']:.2f}%")
                print(f"  - 개통정보 입력 시: {results_summary['Y']['completion_rate']:.2f}%")
                print(f"  - 절대 개선: +{improvement:.2f}%p")
                print(f"  - 상대 개선: +{improvement_pct:.1f}%")

            return {
                'quote_results': quote_results,
                'event_results': event_results,
                'combined_results': combined_results,
                'summary': results_summary
            }

    finally:
        connection.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 개통정보 입력 여부별 전환율 분석")
    print("="*60)

    results = check_activation_info()

    print("\n✅ 분석 완료!")
