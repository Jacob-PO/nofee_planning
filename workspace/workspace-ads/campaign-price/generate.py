import pandas as pd
import pymysql
from datetime import datetime
from pathlib import Path

class CampaignPriceTossStyle:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.output_path = self.base_path / 'output'
        self.output_path.mkdir(exist_ok=True)

        # DB 연결 정보
        self.db_config = {
            'host': '43.203.125.223',
            'port': 3306,
            'user': 'nofee',
            'password': 'HBDyNLZBXZ41TkeZ',
            'database': 'db_nofee',
            'charset': 'utf8mb4'
        }

    def get_campaign_data(self):
        """DB에서 진행중인 캠페인 데이터 가져오기"""
        connection = pymysql.connect(**self.db_config)

        try:
            with connection.cursor() as cursor:
                # 오늘 날짜 가져오기
                today = datetime.now().strftime('%Y-%m-%d')

                query = f"""
                SELECT
                    pg.product_group_nm as device_name,
                    CONCAT(IFNULL(sido.sido_nm, ''), ' ', IFNULL(sigungu.sigungu_nm, '')) as region,
                    c.installment_principal as price,
                    c.carrier_code,
                    c.join_type_code,
                    c.title as campaign_title,
                    s.store_nm,
                    c.campaign_no,
                    c.start_at
                FROM tb_campaign_phone c
                LEFT JOIN tb_product_phone p ON c.product_code = p.product_code
                LEFT JOIN tb_product_group_phone pg ON p.product_group_code = pg.product_group_code
                LEFT JOIN tb_store s ON c.store_no = s.store_no
                LEFT JOIN tb_area_sido sido ON s.sido_no = sido.sido_no
                LEFT JOIN tb_area_sigungu sigungu ON s.sigungu_no = sigungu.sigungu_no
                WHERE c.deleted_yn = 'N'
                    AND c.product_code IS NOT NULL
                    AND c.installment_principal IS NOT NULL
                    AND c.installment_principal < 10000000
                    AND (pg.product_group_nm IS NULL OR pg.product_group_nm NOT LIKE '%사전예약%')
                    AND (c.title IS NULL OR c.title NOT LIKE '%미리보상%')
                    AND (
                        (c.start_at <= '{today} 23:59:59' AND c.end_at >= '{today} 00:00:00')
                        OR (c.start_at <= '{today} 23:59:59' AND c.end_at IS NULL)
                        OR (c.start_at IS NULL AND c.end_at >= '{today} 00:00:00')
                    )
                ORDER BY pg.product_group_nm, c.installment_principal ASC, c.start_at ASC
                """

                cursor.execute(query)
                results = cursor.fetchall()

                df = pd.DataFrame(results, columns=[
                    'device_name', 'region', 'price', 'carrier_code',
                    'join_type_code', 'campaign_title', 'store_nm', 'campaign_no', 'start_at'
                ])

                # 통신사 코드 변환
                carrier_map = {
                    '0301001001': 'SKT',
                    '0301001002': 'KT',
                    '0301001003': 'LG'
                }
                df['carrier'] = df['carrier_code'].map(carrier_map)

                # 가입유형 코드 변환
                join_type_map = {
                    '0301007001': '신규',
                    '0301007002': '번호이동',
                    '0301007003': '기기변경'
                }
                df['join_type'] = df['join_type_code'].map(join_type_map)

                print(f"총 {len(df)}개의 캠페인 데이터를 가져왔습니다.")
                return df

        finally:
            connection.close()

    def mask_store_name(self, store_nm):
        """판매점 닉네임 앞 4글자를 가져와서 2,4번째 글자를 *로 마스킹"""
        if not store_nm:
            return ""

        # 문자열로 변환
        store_nm = str(store_nm)

        if len(store_nm) == 0:
            return ""

        # 앞 4글자 추출
        first_four = store_nm[:4]

        # 길이에 따른 처리
        if len(first_four) == 1:
            return first_four
        elif len(first_four) == 2:
            return first_four[0] + '*'
        elif len(first_four) == 3:
            return first_four[0] + '*' + first_four[2]
        else:  # 4글자 이상
            return first_four[0] + '*' + first_four[2] + '*'

    def sort_devices_by_priority(self, devices):
        """기기명을 최신 모델 우선순위로 정렬 - 애플 > 삼성 순서"""
        def get_device_priority(device_name):
            # 아이폰 우선순위 (애플 제품이 가장 먼저, 음수로 최신 모델이 앞에)
            if '아이폰' in device_name:
                # 아이폰 17 시리즈
                if '아이폰 17' in device_name:
                    if '프로 맥스' in device_name:
                        return (0, -17, -4)
                    elif '프로' in device_name:
                        return (0, -17, -3)
                    elif '플러스' in device_name:
                        return (0, -17, -2)
                    else:
                        return (0, -17, -1)
                # 아이폰 16 시리즈
                elif '아이폰 16' in device_name:
                    if '프로 맥스' in device_name:
                        return (0, -16, -4)
                    elif '프로' in device_name:
                        return (0, -16, -3)
                    elif '플러스' in device_name:
                        return (0, -16, -2)
                    else:
                        return (0, -16, -1)
                # 아이폰 15 시리즈
                elif '아이폰 15' in device_name:
                    if '프로 맥스' in device_name:
                        return (0, -15, -4)
                    elif '프로' in device_name:
                        return (0, -15, -3)
                    elif '플러스' in device_name:
                        return (0, -15, -2)
                    else:
                        return (0, -15, -1)
                # 기타 아이폰 (숫자 추출)
                else:
                    import re
                    match = re.search(r'아이폰\s*(\d+)', device_name)
                    if match:
                        return (0, -int(match.group(1)), 0)
                    return (0, 0, 0)

            # 갤럭시 우선순위 (애플 다음으로 표시)
            elif '갤럭시' in device_name:
                # Z 시리즈 (폴더블)
                if 'Z 플립' in device_name or 'Z플립' in device_name:
                    import re
                    match = re.search(r'(\d+)', device_name)
                    num = int(match.group(1)) if match else 0
                    return (1, -num, -2)
                elif 'Z 폴드' in device_name or 'Z폴드' in device_name:
                    import re
                    match = re.search(r'(\d+)', device_name)
                    num = int(match.group(1)) if match else 0
                    return (1, -num, -3)
                # S 시리즈
                elif 'S' in device_name:
                    import re
                    match = re.search(r'S\s*(\d+)', device_name)
                    if match:
                        num = int(match.group(1))
                        if '울트라' in device_name:
                            return (1, -num, -1)
                        else:
                            return (1, -num, 0)
                    return (1, 0, 0)
                # 기타 갤럭시
                else:
                    return (1, 0, 0)

            # 기타 기기
            else:
                return (2, 0, 0)

        return sorted(devices, key=get_device_priority)

    def generate_toss_style_html(self, df):
        """토스 스타일 HTML 생성 - 컴팩트 버전"""
        now = datetime.now()
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        weekday = weekdays[now.weekday()]
        date = now.strftime(f'%m월 %d일') + f' ({weekday})'

        # 모든 고유 기기명 가져오기
        all_devices = df['device_name'].unique()
        all_devices = [d for d in all_devices if d and '사전예약' not in d and d != '갤럭시 S24 울트라']
        all_devices = self.sort_devices_by_priority(all_devices)  # 최신 모델 우선순위로 정렬

        # 디버깅: 정렬된 기기 순서 출력
        print(f"\n📱 정렬된 기기 순서:")
        for idx, device in enumerate(all_devices, 1):
            print(f"  {idx}. {device}")

        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>휴대폰 최저가</title>
    <link href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/variable/woff2/SUIT-Variable.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'SUIT Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            width: 1000px;
            height: 1000px;
            background: #1A1A2E;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .container {{
            width: 1000px;
            height: 1000px;
            background: linear-gradient(135deg, #2C1654 0%, #6B46C1 30%, #9333EA 70%, #A855F7 100%);
            padding: 15px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .header {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            color: white;
            margin-bottom: 10px;
        }}

        .logo {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 10px;
        }}

        .logo-text {{
            font-size: 32px;
            font-weight: 900;
            color: white;
            margin-bottom: 3px;
        }}

        .date {{
            font-size: 14px;
            background: rgba(255, 255, 255, 0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
        }}

        .content {{
            flex: 1;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            overflow: hidden;
            grid-auto-rows: min-content;
            align-content: start;
            padding-bottom: 8px;
        }}

        .device-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .device-card.single-price-group {{
            grid-column: span 2;
        }}

        .device-card.full-width {{
            grid-column: span 3;
        }}

        .device-name {{
            font-size: 16px;
            font-weight: 800;
            color: #191F28;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
        }}


        .device-tag {{
            font-size: 11px;
            padding: 3px 7px;
            border-radius: 10px;
            font-weight: 600;
            display: inline-block;
        }}

        .device-tag.skt {{
            background: #FFE5E8;
            color: #EA002C;
        }}

        .device-tag.kt {{
            background: #E5F5FF;
            color: #0089D0;
        }}

        .device-tag.lg {{
            background: #FFE5F5;
            color: #E6007E;
        }}

        .device-tag.join-type {{
            background: #F0F2F5;
            color: #191F28;
        }}

        .price-list {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .price-list.two-columns {{
            display: grid;
            grid-template-columns: 1fr 1px 1fr;
            gap: 8px;
        }}

        .divider {{
            width: 1px;
            background: #E0E0E0;
            align-self: stretch;
        }}

        .column {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .price-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 8px;
            background: #F7F9FB;
            border-radius: 8px;
            font-size: 13px;
            min-height: 30px;
            gap: 8px;
        }}

        .price-item.compact {{
            padding: 4px 6px;
            min-height: 28px;
            font-size: 12px;
        }}

        .device-name-small {{
            font-size: 13px;
            font-weight: 700;
            color: #191F28;
            margin-right: 6px;
            min-width: 80px;
        }}

        .device-name-inline {{
            font-size: 14px;
            font-weight: 800;
            color: #191F28;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .price-item-left {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 1;
            min-width: 0;
            overflow: visible;
        }}

        .carrier-price {{
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: nowrap;
        }}

        .price-item-right {{
            display: flex;
            align-items: center;
            gap: 4px;
            flex-shrink: 0;
        }}

        .carrier-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}

        .carrier-dot.skt {{
            background: #EA002C;
        }}

        .carrier-dot.kt {{
            background: #0089D0;
        }}

        .carrier-dot.lg {{
            background: #E6007E;
        }}

        .price {{
            font-weight: 800;
            color: #191F28;
            font-size: 15px;
        }}

        .location-tag {{
            font-size: 12px;
            color: #131FA0;
            font-weight: 700;
            background: #E8EBFF;
            padding: 3px 6px;
            border-radius: 5px;
            white-space: nowrap;
        }}

        .footer {{
            margin-top: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            color: white;
            font-size: 15px;
            font-weight: 600;
            height: 45px;
            flex-shrink: 0;
        }}

        .footer-left {{
            flex: 1;
            text-align: left;
        }}

        .footer-center {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .footer-right {{
            flex: 1;
            text-align: right;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 5px;
        }}

        .search-icon {{
            width: 18px;
            height: 18px;
            fill: white;
        }}

        @media print {{
            body {{
                margin: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-text">{now.strftime('%Y년 %m월')} 전국 휴대폰 최저가 시세표</div>
            <div class="date">{date}</div>
        </div>

        <div class="content">
"""

        # 각 기기별로 데이터 정리하고 단가 개수 계산
        device_price_counts = []
        zero_price_devices = []  # 0원 단일 상품들
        single_price_devices = []  # 단일 가격 상품들 (0원 제외)

        for device in all_devices:
            device_data = df[df['device_name'] == device]
            if device_data.empty:
                continue

            # 가격별로 그룹화하여 같은 가격의 모든 지역과 가입유형 표시
            # 같은 조건일 때 start_at이 가장 이른 지역만 선택
            price_groups = {}
            seen_combinations = {}  # (carrier, price, join_type): earliest_start_at
            seen_regions_per_key = {}  # 각 가격 조합별로 이미 노출된 지역 추적

            for _, row in device_data.iterrows():
                carrier = row['carrier']
                price = row['price']
                region = row['region'] if pd.notna(row['region']) else ''
                join_type = row['join_type'] if pd.notna(row['join_type']) else ''
                start_at = row['start_at']
                store_nm = row['store_nm'] if pd.notna(row['store_nm']) else ''

                # 지역이 없는 경우 건너뛰기
                if not region or not region.strip():
                    continue

                key = (carrier, price, join_type)

                # 처음 보는 조합이거나 더 이른 start_at인 경우만 추가
                if key not in seen_combinations:
                    seen_combinations[key] = start_at
                    price_groups[key] = []
                    seen_regions_per_key[key] = set()

                    price_groups[key].append({
                        'region': region.strip(),
                        'store_nm': store_nm
                    })
                    seen_regions_per_key[key].add(region.strip())
                elif start_at == seen_combinations[key]:
                    # 같은 start_at인 경우만 지역 추가 (해당 키에서 동일 지역은 제외)
                    if region.strip() not in seen_regions_per_key[key]:
                        price_groups[key].append({
                            'region': region.strip(),
                            'store_nm': store_nm
                        })
                        seen_regions_per_key[key].add(region.strip())

            # 가격순으로 정렬하고 지역이 있는 항목만 필터링, 최대 3개까지 표시
            sorted_groups = sorted(
                [(k, v) for k, v in price_groups.items() if v],  # 지역 리스트가 비어있지 않은 것만
                key=lambda x: x[0][1]
            )[:3]

            # 단가가 1개인 경우 분류 (지역이 있는 것만 계산)
            valid_price_groups = {k: v for k, v in price_groups.items() if v}

            # 지역이 있는 가격 항목이 없으면 건너뛰기
            if len(valid_price_groups) == 0:
                continue

            # 단일 가격인지 여러 가격인지에 관계없이 모든 상품을 동적으로 처리
            if len(valid_price_groups) == 1:
                # 단일 가격 상품
                (carrier, price, join_type), regions = sorted_groups[0]
                if price == 0:
                    # 0원인 경우
                    zero_price_devices.append({
                        'device': device,
                        'info': sorted_groups[0]
                    })
                else:
                    # 0원이 아닌 단일 가격
                    single_price_devices.append({
                        'device': device,
                        'info': sorted_groups[0]
                    })
            else:
                # 여러 가격이 있는 경우
                device_price_counts.append({
                    'device': device,
                    'price_count': len(valid_price_groups),
                    'sorted_groups': sorted_groups
                })

        # 기기 우선순위 순서 유지 (all_devices 순서대로 이미 정렬되어 있음)
        # device_price_counts.sort(key=lambda x: x['price_count'], reverse=True)  # 이 정렬 제거

        # 최저가 단가는 모든 상품 표시 (각 상품당 최대 3개 단가)

        # 오늘의 특가를 최저가순으로 정렬하고 최대 8개까지만
        all_special_prices = []

        # 0원 상품 추가
        for device_info in zero_price_devices:
            (carrier, price, join_type), regions = device_info['info']
            all_special_prices.append({
                'device': device_info['device'],
                'price': price,
                'carrier': carrier,
                'join_type': join_type,
                'regions': regions
            })

        # 단일 가격 상품 추가
        for device_info in single_price_devices:
            (carrier, price, join_type), regions = device_info['info']
            all_special_prices.append({
                'device': device_info['device'],
                'price': price,
                'carrier': carrier,
                'join_type': join_type,
                'regions': regions
            })

        # 가격순 정렬 후 최대 8개만
        all_special_prices.sort(key=lambda x: x['price'])
        all_special_prices = all_special_prices[:8]

        # 디버깅: 상품 수 출력
        print(f"\n📊 상품 분류 결과:")
        print(f"  - 표시된 상품: {len(device_price_counts)}개")
        print(f"  - 단일 특가 상품 (미표시): {len(all_special_prices)}개\n")

        # HTML 생성
        for device_info in device_price_counts:
            device = device_info['device']
            sorted_groups = device_info['sorted_groups']

            # 가격 항목이 1개인지 여러개인지 확인
            card_class = "single-price" if len(sorted_groups) == 1 else "multi-price"

            html += f"""
            <div class="device-card {card_class}">
                <div class="device-name">{device}</div>
                <div class="price-list">
"""

            for (carrier, price, join_type), regions in sorted_groups:
                # 통신사 클래스
                carrier_class = carrier.lower().replace(' ', '').replace('+', '')

                # 가격 표시 (모두 검정색)
                if price < 0:
                    price_text = f"{int(price/10000)}만"
                    price_class = "price"
                elif price == 0:
                    price_text = "0원"
                    price_class = "price"
                else:
                    price_text = f"{int(price/10000)}만"
                    price_class = "price"

                # 지역 추출 - 실제 DB에서 가져온 지역 사용 (첫 번째 지역 표시)
                region_display = regions[0]['region'] if regions else ""

                # 지역이 있는 경우만 HTML에 추가
                if region_display:
                    html += f"""
                    <div class="price-item">
                        <div class="carrier-price">
                            <div class="carrier-dot {carrier_class}"></div>
                            <span class="{price_class}">{price_text}</span>
                            <span class="device-tag {carrier_class}" style="margin-left: 5px;">{carrier}</span>
                            <span class="device-tag join-type">{join_type}</span>
                        </div>
                        <span class="location-tag">{region_display}</span>
                    </div>
"""

            html += """
                </div>
            </div>
"""

        # 오늘의 특가 섹션 제거 (하드코딩)

        html += """
        </div>

        <div class="footer">
            <div class="footer-left">nofee.team</div>
            <div class="footer-center">
                <svg width="95" height="20" viewBox="0 0 95 20" fill="none" xmlns="http://www.w3.org/2000/svg" style="height: 22px; width: auto;">
                    <path d="M18 5.38456L18 18.7514C18 19.1651 17.664 19.5 17.2489 19.5L8.63149 19.5L4.63676 14.1508L4.63676 19.5L0.751099 19.5C0.337731 19.5 1.26474e-09 19.1651 1.2367e-09 18.7514L0 1.24864C0 0.834871 0.337731 0.5 0.751099 0.5L13.0994 0.5C13.2982 0.5 13.4899 0.578896 13.6306 0.719157L17.7801 4.85508C17.9208 4.99534 18 5.18644 18 5.38456Z" fill="white"/>
                    <path d="M26 1.34198L29.6922 1.34198C32.4316 5.23816 35.171 9.0426 37.9336 13.1667L37.9816 13.1667L37.9816 1.34198L41.5067 1.34198L41.5067 19.1138L37.8393 19.1138C35.0999 15.2635 32.362 11.5715 29.6226 7.53918L29.5515 7.53918L29.5515 19.1138L26.0031 19.1138L26.0031 1.34198L26 1.34198Z" fill="white"/>
                    <path d="M43.8409 12.779C43.8409 8.83692 46.6514 6.03427 50.701 6.03427C54.7505 6.03427 57.5611 8.83692 57.5611 12.779C57.5611 16.721 54.7505 19.5 50.701 19.5C46.6514 19.5 43.8409 16.7432 43.8409 12.779ZM50.6994 16.4473C52.6994 16.4473 54.0807 14.9202 54.0807 12.779C54.0807 10.6378 52.6994 9.08847 50.6994 9.08847C48.6994 9.08847 47.2934 10.6156 47.2934 12.779C47.2934 14.9424 48.6979 16.4473 50.6994 16.4473Z" fill="white"/>
                    <path d="M60.4892 9.29416L58.5124 9.29416L58.5124 6.40125L60.4892 6.40125L60.4892 5.1479C60.4892 1.77554 62.6083 0.5 65.0383 0.5C65.6339 0.5 66.4908 0.591745 67.2302 0.864019L67.2302 3.52905C66.5867 3.30117 66.2062 3.2331 65.753 3.2331C63.8241 3.2331 63.8241 4.55452 63.8241 5.51192L63.8241 6.39977L66.8961 6.39977L66.8961 9.29268L63.8241 9.29268L63.8241 19.1123L60.4892 19.1123L60.4892 9.29416Z" fill="white"/>
                    <path d="M67.4188 12.8248C67.4188 8.90646 70.1815 6.03427 74.0639 6.03427C77.3741 6.03427 80.4708 8.13108 80.4708 12.8012L80.4708 13.6668L70.7538 13.6668C71.0399 15.5801 72.5403 16.6293 74.2789 16.6293C75.637 16.6293 76.8033 15.9234 77.3989 14.602L80.5188 15.8095C79.6371 17.8826 77.3989 19.5 74.3021 19.5C70.3717 19.5 67.4188 16.8572 67.4188 12.8248ZM77.1127 11.4812C76.8745 9.52204 75.5411 8.77033 74.0407 8.77033C72.3253 8.77033 71.2534 9.88606 70.9208 11.4812L77.1127 11.4812Z" fill="white"/>
                    <path d="M81.9001 12.8248C81.9001 8.90646 84.6627 6.03427 88.5452 6.03427C91.8553 6.03427 94.952 8.13108 94.952 12.8012L94.952 13.6668L85.235 13.6668C85.5212 15.5801 87.0216 16.6293 88.7602 16.6293C90.1183 16.6293 91.2846 15.9234 91.8801 14.602L95 15.8095C94.1183 17.8826 91.8801 19.5 88.7834 19.5C84.8529 19.5 81.9001 16.8572 81.9001 12.8248ZM91.5939 11.4812C91.3557 9.52204 90.0224 8.77033 88.522 8.77033C86.8066 8.77033 85.7346 9.88606 85.4021 11.4812L91.5939 11.4812Z" fill="white"/>
                </svg>
            </div>
            <div class="footer-right">
                <svg class="search-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <span>네이버에서 "노피 휴대폰" 검색</span>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate(self, output_filename='campaign_price_toss.html'):
        """토스 스타일 단가표 생성"""
        try:
            print("캠페인 데이터 로드 중...")
            df = self.get_campaign_data()

            print("토스 스타일 HTML 생성 중...")
            html = self.generate_toss_style_html(df)

            output_file = self.output_path / output_filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"\n✅ 토스 스타일 단가표가 생성되었습니다!")
            print(f"📍 파일 위치: {output_file}")

            return output_file

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    generator = CampaignPriceTossStyle()
    generator.generate()