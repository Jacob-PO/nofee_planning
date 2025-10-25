import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path
import unicodedata

def extract_data_from_번개폰(file_path, date, carrier, dealer):
    """번개폰 파일에서 데이터 추출 (SK용)"""
    df = pd.read_excel(file_path, sheet_name=0)

    device_data = {}

    # 번개폰은 2행부터 데이터 시작 (0행: 헤더, 1행: 컬럼명)
    for idx in range(2, len(df)):
        device_name = df.iloc[idx, 0]

        if pd.isna(device_name) or device_name == '':
            continue

        if device_name not in device_data:
            device_data[device_name] = {
                'date': date,
                'carrier': carrier,
                'dealer': dealer,
                'device_name': device_name
            }

        # SK 번개폰 실제 컬럼 구조:
        # 0열: 기기명
        # 1열: 109k 번호이동 선약
        # 2열: 109k 기기변경 선약
        # 3열: 109k 번호이동 공시
        # 4열: 109k 기기변경 공시

        # 1열: 109k 번호이동 선약
        if pd.notna(df.iloc[idx, 1]):
            device_data[device_name]['번호이동_선약_109k'] = df.iloc[idx, 1]

        # 2열: 109k 기기변경 선약
        if pd.notna(df.iloc[idx, 2]):
            device_data[device_name]['기기변경_선약_109k'] = df.iloc[idx, 2]

        # 3열: 109k 번호이동 공시
        if pd.notna(df.iloc[idx, 3]):
            device_data[device_name]['번호이동_공시_109k'] = df.iloc[idx, 3]

        # 4열: 109k 기기변경 공시
        if pd.notna(df.iloc[idx, 4]):
            device_data[device_name]['기기변경_공시_109k'] = df.iloc[idx, 4]

    return list(device_data.values())

def parse_plan_name(column_name):
    """요금제 이름에서 가격 추출"""
    if pd.isna(column_name):
        return None
    
    str_name = str(column_name)
    
    # 숫자 패턴 찾기
    match = re.search(r'(\d+)', str_name)
    if match:
        value = match.group(1)
        return f"{value}k"
    
    return None

def extract_apple_preorder_data(file_path, date, carrier, dealer):
    """애플사전예약 파일에서 데이터 추출"""
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=None)

        print(f"애플사전예약 파일 처리: {os.path.basename(file_path)}")
        print(f"파일 구조: {len(df)}행 x {len(df.columns)}열")

        # SK 케이 애플사전예약 파일인지 확인
        is_sk_kei = "케이" in file_path or "케이" in dealer

        # 결과를 저장할 리스트
        all_data = []

        if is_sk_kei:
            # SK 케이 애플사전예약 파일 처리
            # 구조: 행 7-10에 실제 데이터 (0-indexed로는 6-9, 포함)
            for row_idx in range(6, min(10, len(df))):
                device_name = df.iloc[row_idx, 0]  # 첫 번째 컬럼이 기기명

                if pd.notna(device_name) and isinstance(device_name, str):
                    device_name = device_name.strip()

                    device_info = {
                        'date': date,
                        'carrier': carrier,
                        'dealer': dealer,
                        'device_name': device_name
                    }

                    # SK 케이 컬럼 매핑
                    # 행3-4에 요금제 정보 있음
                    # 행5에 공시/선약 구분
                    # 행6-9에 실제 데이터
                    # 열1-12 (B-M열): MNP 6개 (109k, 100k, 79k 각각 공시/선약) + 기변 6개

                    column_mapping = {
                        # MNP 부분
                        1: {'join_type': '번호이동', 'support': '공시', 'plan': '109k'},
                        2: {'join_type': '번호이동', 'support': '선약', 'plan': '109k'},
                        3: {'join_type': '번호이동', 'support': '공시', 'plan': '100k'},
                        4: {'join_type': '번호이동', 'support': '선약', 'plan': '100k'},
                        5: {'join_type': '번호이동', 'support': '공시', 'plan': '79k'},
                        6: {'join_type': '번호이동', 'support': '선약', 'plan': '79k'},
                        # 기변 부분
                        7: {'join_type': '기기변경', 'support': '공시', 'plan': '109k'},
                        8: {'join_type': '기기변경', 'support': '선약', 'plan': '109k'},
                        9: {'join_type': '기기변경', 'support': '공시', 'plan': '100k'},
                        10: {'join_type': '기기변경', 'support': '선약', 'plan': '100k'},
                        11: {'join_type': '기기변경', 'support': '공시', 'plan': '79k'},
                        12: {'join_type': '기기변경', 'support': '선약', 'plan': '79k'}
                    }

                    for col_idx, mapping in column_mapping.items():
                        if col_idx < len(df.columns):
                            value = df.iloc[row_idx, col_idx]
                            if pd.notna(value):
                                try:
                                    # _calculated 파일은 이미 계산되어 있음
                                    if "_calculated" in file_path:
                                        rebate_value = int(float(str(value)))
                                    else:
                                        # _tables 파일은 만원 단위이므로 10000을 곱함
                                        rebate_value = int(float(str(value))) * 10000
                                    col_key = f"{mapping['join_type']}_{mapping['support']}_{mapping['plan']}"
                                    device_info[col_key] = rebate_value
                                except (ValueError, TypeError):
                                    continue

                    if len(device_info) > 4:
                        all_data.append(device_info)
        else:
            # SK 상상 애플사전예약 파일 처리 (기존 로직)
            # 구조 분석:
            # 행 1: '모델류', '79 구간 요금제', nan, '109이상 요금제', nan
            # 행 2: nan, 'MNP', nan, '기기변경', nan
            # 행 3: nan, '공시', '선약', '공시', '선약'
            # 행 5: '아이폰 17/ 플러스', '500', '500', '400', '400'
            # 행 6: '아이폰 17 프로 / 맥스', '500', '500', '400', '400'

            # 컬럼 매핑
            column_mapping = {
                1: {'join_type': '번호이동', 'support': '공시', 'plan': '79k'},  # 79구간 MNP 공시
                2: {'join_type': '번호이동', 'support': '선약', 'plan': '79k'},  # 79구간 MNP 선약
                3: {'join_type': '기기변경', 'support': '공시', 'plan': '109k'}, # 109이상 기변 공시
                4: {'join_type': '기기변경', 'support': '선약', 'plan': '109k'}  # 109이상 기변 선약
            }

            # 데이터 행 처리 (행 6, 7 - 0-indexed로는 6, 7)
            for row_idx in [6, 7]:
                if row_idx < len(df):
                    device_name = df.iloc[row_idx, 0]  # 첫 번째 컬럼이 기기명

                    if pd.notna(device_name) and isinstance(device_name, str):
                        device_name = device_name.strip()

                        # 기기명 정규화
                        if "아이폰 17/ 플러스" in device_name:
                            # 아이폰 17과 아이폰 17 플러스로 분리
                            device_names = ["아이폰 17", "아이폰 17 플러스"]
                        elif "아이폰 17 프로 / 맥스" in device_name:
                            # 아이폰 17 프로와 아이폰 17 프로 맥스로 분리
                            device_names = ["아이폰 17 프로", "아이폰 17 프로 맥스"]
                        elif "아이폰17/프로/프로맥스" in device_name:
                            # 아이폰17, 프로, 프로맥스로 분리
                            device_names = ["아이폰 17", "아이폰 17 프로", "아이폰 17 프로맥스"]
                        else:
                            device_names = [device_name]

                        # 각 기기명에 대해 데이터 생성
                        for final_device_name in device_names:
                            device_info = {
                                'date': date,
                                'carrier': carrier,
                                'dealer': dealer,
                                'device_name': final_device_name
                            }

                            # 각 컬럼의 값 추출
                            for col_idx, mapping in column_mapping.items():
                                if col_idx < len(df.columns):
                                    value = df.iloc[row_idx, col_idx]
                                    if pd.notna(value) and isinstance(value, (int, float, str)):
                                        try:
                                            # _calculated 파일은 이미 계산되어 있음
                                            if "_calculated" in file_path:
                                                rebate_value = int(float(str(value)))
                                            else:
                                                # _tables 파일은 천원 단위이므로 1000을 곱함
                                                rebate_value = int(float(str(value))) * 1000

                                            col_key = f"{mapping['join_type']}_{mapping['support']}_{mapping['plan']}"
                                            device_info[col_key] = rebate_value
                                        except:
                                            continue

                            # 데이터가 있는 경우에만 추가
                            if len(device_info) > 4:  # 기본 4개 필드 외에 데이터가 있는 경우
                                all_data.append(device_info)

        print(f"애플사전예약: {len(all_data)}개 기기 추출됨")
        return all_data

    except Exception as e:
        print(f"애플사전예약 파일 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_sk_sangsang_data(file_path, date, carrier, dealer):
    """SK 상상 전용 데이터 추출 함수 - 개선된 버전"""

    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 딕셔너리
    device_data = {}
    
    # 디버깅용
    print(f"SK 상상 처리 시작: {file_path}")
    print(f"파일 구조: {len(df)}행 x {len(df.columns)}열")
    
    # 모든 데이터 확인
    print("\n전체 데이터 구조:")
    for idx in range(min(30, len(df))):
        row_data = []
        for col in range(min(8, len(df.columns))):
            cell_value = df.iloc[idx, col]
            if pd.notna(cell_value):
                row_data.append(f"{cell_value}")
            else:
                row_data.append("")
        if any(row_data):
            print(f"행 {idx}: {' | '.join(row_data)}")
    
    # 제품명 찾기 및 데이터 추출 - 더 유연한 접근
    for row_idx in range(len(df)):
        device_name = df.iloc[row_idx, 0]
        if pd.isna(device_name) or not isinstance(device_name, str):
            continue
            
        # 디바이스명 정규화
        device_name = str(device_name).strip()
        
        # 폴드7, 플립7 처리
        if "폴드7" in device_name or "플립7" in device_name:
            # 512기가 모델 처리
            if "512기가" in device_name:
                if "폴드7" in device_name:
                    dev_name = "폴드7_512기가"
                else:
                    dev_name = "플립7_512기가"
                    
                if dev_name not in device_data:
                    device_data[dev_name] = {
                        'date': date,
                        'carrier': carrier,
                        'dealer': dealer,
                        'device_name': dev_name
                    }
                
                # 109이상 요금제 구간 (열 1-2: MNP, 열 3-4: L_69 구간, 열 5-6: 기변)
                # 109k 요금제에만 적용
                if pd.notna(df.iloc[row_idx, 1]) and isinstance(df.iloc[row_idx, 1], (int, float)):
                    device_data[dev_name][f'번호이동_공시_109k'] = df.iloc[row_idx, 1]
                if pd.notna(df.iloc[row_idx, 2]) and isinstance(df.iloc[row_idx, 2], (int, float)):
                    device_data[dev_name][f'번호이동_선약_109k'] = df.iloc[row_idx, 2]
                    
                # L_69 구간 (69k~109k)
                if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                    for plan in ['69k', '79k', '100k', '109k']:
                        device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
                if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                    for plan in ['69k', '79k', '100k', '109k']:
                        device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                        
                # 기변
                if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                    device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
                if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                    device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]
                    
        # 아이폰17 처리 추가
        elif "아이폰17/프로/프로맥스" in device_name:
            # 아이폰17, 프로, 프로맥스로 분리
            dev_names = ["아이폰 17", "아이폰 17 프로", "아이폰 17 프로맥스"]

            for dev_name in dev_names:
                if dev_name not in device_data:
                    device_data[dev_name] = {
                        'date': date,
                        'carrier': carrier,
                        'dealer': dealer,
                        'device_name': dev_name
                    }

                # 동일한 구조로 처리
                if pd.notna(df.iloc[row_idx, 1]) and isinstance(df.iloc[row_idx, 1], (int, float)):
                    device_data[dev_name][f'번호이동_공시_109k'] = df.iloc[row_idx, 1]
                if pd.notna(df.iloc[row_idx, 2]) and isinstance(df.iloc[row_idx, 2], (int, float)):
                    device_data[dev_name][f'번호이동_선약_109k'] = df.iloc[row_idx, 2]
                if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                    for plan in ['69k', '79k', '100k']:
                        device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
                if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                    for plan in ['69k', '79k', '100k']:
                        device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                    device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
                if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                    device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]

        # 아이폰 에어 처리
        elif "아이폰 에어" in device_name:
            dev_name = "아이폰 에어"
            if dev_name not in device_data:
                device_data[dev_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': dev_name
                }

            # 동일한 구조로 처리
            if pd.notna(df.iloc[row_idx, 1]) and isinstance(df.iloc[row_idx, 1], (int, float)):
                device_data[dev_name][f'번호이동_공시_109k'] = df.iloc[row_idx, 1]
            if pd.notna(df.iloc[row_idx, 2]) and isinstance(df.iloc[row_idx, 2], (int, float)):
                device_data[dev_name][f'번호이동_선약_109k'] = df.iloc[row_idx, 2]
            if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                for plan in ['69k', '79k', '100k']:
                    device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
            if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                for plan in ['69k', '79k', '100k']:
                    device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
            if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
            if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]

        # 갤럭시 S25 처리
        elif "갤럭시 S25" in device_name:
            if "엣지" in device_name:
                dev_names = ["갤럭시 S25 엣지"]
            else:
                # 갤럭시 S25군을 3개 모델로 분리
                dev_names = ["갤럭시 S25", "갤럭시 S25+", "갤럭시 S25 울트라"]
                
            for dev_name in dev_names:
                if dev_name not in device_data:
                    device_data[dev_name] = {
                        'date': date,
                        'carrier': carrier,
                        'dealer': dealer,
                        'device_name': dev_name
                    }
                
                # 동일한 구조로 처리
                if pd.notna(df.iloc[row_idx, 1]):
                    device_data[dev_name][f'번호이동_공시_109k'] = df.iloc[row_idx, 1]
                if pd.notna(df.iloc[row_idx, 2]):
                    device_data[dev_name][f'번호이동_선약_109k'] = df.iloc[row_idx, 2]
                if pd.notna(df.iloc[row_idx, 3]):
                    for plan in ['69k', '79k', '100k', '109k']:
                        device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
                if pd.notna(df.iloc[row_idx, 4]):
                    for plan in ['69k', '79k', '100k', '109k']:
                        device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                if pd.notna(df.iloc[row_idx, 5]):
                    device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
                if pd.notna(df.iloc[row_idx, 6]):
                    device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]
                
        # 퀀텀5 처리
        elif "퀀텀" in device_name:
            dev_name = "퀀텀5"
            if dev_name not in device_data:
                device_data[dev_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': dev_name
                }
            
            # M_50 구간 (50k~109k)
            if pd.notna(df.iloc[row_idx, 1]) and isinstance(df.iloc[row_idx, 1], (int, float)):
                for plan in ['50k', '69k', '79k', '100k', '109k']:
                    device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 1]
            if pd.notna(df.iloc[row_idx, 2]) and isinstance(df.iloc[row_idx, 2], (int, float)):
                for plan in ['50k', '69k', '79k', '100k', '109k']:
                    device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 2]
                    
            # S_33-R43 구간 (33k~43k)
            if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
            if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                    
            # 기변 109k
            if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
            if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]
                
        # iPhone 16 처리
        elif "IP16" in device_name:
            # IP16/16PL 또는 IP16P/16PM 처리
            if "IP16P" in device_name:
                # IP16P/16PM -> iPhone 16 Pro, iPhone 16 Pro Max
                dev_names = ["iPhone 16 Pro", "iPhone 16 Pro Max"]
            else:
                # IP16/16PL -> iPhone 16, iPhone 16 Plus
                dev_names = ["iPhone 16", "iPhone 16 Plus"]
                
            for dev_name in dev_names:
                if dev_name not in device_data:
                    device_data[dev_name] = {
                        'date': date,
                        'carrier': carrier,
                        'dealer': dealer,
                        'device_name': dev_name
                    }
                
                # 109이상 요금제 MNP (열 1-2)
                if pd.notna(df.iloc[row_idx, 1]) and isinstance(df.iloc[row_idx, 1], (int, float)):
                    device_data[dev_name][f'번호이동_공시_109k'] = df.iloc[row_idx, 1]
                if pd.notna(df.iloc[row_idx, 2]) and isinstance(df.iloc[row_idx, 2], (int, float)):
                    device_data[dev_name][f'번호이동_선약_109k'] = df.iloc[row_idx, 2]
                
                # L_69 구간 MNP (열 3-4) - 69k, 79k, 100k에만 적용 (109k는 별도 처리)
                if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                    for plan in ['69k', '79k', '100k']:
                        device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
                if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                    for plan in ['69k', '79k', '100k']:
                        device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                
                # 109이상 기변 (열 5-6)
                if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                    device_data[dev_name][f'기기변경_공시_109k'] = df.iloc[row_idx, 5]
                if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                    device_data[dev_name][f'기기변경_선약_109k'] = df.iloc[row_idx, 6]
                
        # 갤럭시 A16, ZEM폰3 처리
        elif "A16" in device_name or "갤럭시 A16" in device_name:
            dev_name = "갤럭시 A16"
            if dev_name not in device_data:
                device_data[dev_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': dev_name
                }
            
            # S_33-R43 구간 MNP (열 3-4)
            if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
            if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
                    
            # S_33-R43 구간 기변 (열 5-6)
            if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'기기변경_공시_{plan}'] = df.iloc[row_idx, 5]
            if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'기기변경_선약_{plan}'] = df.iloc[row_idx, 6]
                    
        elif "ZEM" in device_name or "ZEM폰3" in device_name:
            dev_name = "ZEM폰3"
            if dev_name not in device_data:
                device_data[dev_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': dev_name
                }
            
            # 동일한 구조로 처리
            if pd.notna(df.iloc[row_idx, 3]) and isinstance(df.iloc[row_idx, 3], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_공시_{plan}'] = df.iloc[row_idx, 3]
            if pd.notna(df.iloc[row_idx, 4]) and isinstance(df.iloc[row_idx, 4], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'번호이동_선약_{plan}'] = df.iloc[row_idx, 4]
            if pd.notna(df.iloc[row_idx, 5]) and isinstance(df.iloc[row_idx, 5], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'기기변경_공시_{plan}'] = df.iloc[row_idx, 5]
            if pd.notna(df.iloc[row_idx, 6]) and isinstance(df.iloc[row_idx, 6], (int, float)):
                for plan in ['33k', '43k']:
                    device_data[dev_name][f'기기변경_선약_{plan}'] = df.iloc[row_idx, 6]
    
    print(f"\n추출된 디바이스: {list(device_data.keys())}")
    return list(device_data.values())

# SK 나텔 관련 함수는 더 이상 사용하지 않음 (나텔은 입점사가 아님)

def extract_sk_yuntel_data(file_path, date, carrier, dealer):
    """SK 윤텔 파일에서 데이터 추출 - 복잡한 구조 처리"""
    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 딕셔너리
    device_data = {}
    
    # 윤텔의 경우 구조가 복잡함
    # 열별 매핑 정보를 수동으로 정의
    column_mapping = []
    
    # 열 4-5: 프리미엄 109k MNP 공시/선약
    column_mapping.extend([
        {'col': 4, 'plan': '109k', 'type': '번호이동', 'support': '공시'},
        {'col': 5, 'plan': '109k', 'type': '번호이동', 'support': '선약'},
    ])
    
    # 열 8-9: I100 MNP 공시/선약
    column_mapping.extend([
        {'col': 8, 'plan': '100k', 'type': '번호이동', 'support': '공시'},
        {'col': 9, 'plan': '100k', 'type': '번호이동', 'support': '선약'},
    ])
    
    # 열 10-11: I100 기변 공시/선약
    column_mapping.extend([
        {'col': 10, 'plan': '100k', 'type': '기기변경', 'support': '공시'},
        {'col': 11, 'plan': '100k', 'type': '기기변경', 'support': '선약'},
    ])
    
    # 열 12-13: F_79 MNP 공시/선약
    column_mapping.extend([
        {'col': 12, 'plan': '79k', 'type': '번호이동', 'support': '공시'},
        {'col': 13, 'plan': '79k', 'type': '번호이동', 'support': '선약'},
    ])
    
    # 열 14-15: F_79 기변 공시/선약
    column_mapping.extend([
        {'col': 14, 'plan': '79k', 'type': '기기변경', 'support': '공시'},
        {'col': 15, 'plan': '79k', 'type': '기기변경', 'support': '선약'},
    ])
    
    # 열 16-17: L 69 MNP 공시/선약
    column_mapping.extend([
        {'col': 16, 'plan': '69k', 'type': '번호이동', 'support': '공시'},
        {'col': 17, 'plan': '69k', 'type': '번호이동', 'support': '선약'},
    ])
    
    # 열 18-19: L 69 기변 공시/선약
    column_mapping.extend([
        {'col': 18, 'plan': '69k', 'type': '기기변경', 'support': '공시'},
        {'col': 19, 'plan': '69k', 'type': '기기변경', 'support': '선약'},
    ])
    
    # 열 20-21: R_43 MNP 공시/선약
    column_mapping.extend([
        {'col': 20, 'plan': '43k', 'type': '번호이동', 'support': '공시'},
        {'col': 21, 'plan': '43k', 'type': '번호이동', 'support': '선약'},
    ])
    
    # 열 22-23: R_43 기변 공시/선약
    column_mapping.extend([
        {'col': 22, 'plan': '43k', 'type': '기기변경', 'support': '공시'},
        {'col': 23, 'plan': '43k', 'type': '기기변경', 'support': '선약'},
    ])
    
    # 기기별 데이터 처리 (5행부터 시작)
    for idx in range(5, len(df)):
        device_name = df.iloc[idx, 0]
        
        if pd.isna(device_name) or device_name == '' or not isinstance(device_name, str):
            continue
        
        # 기기별 데이터 초기화
        if device_name not in device_data:
            device_data[device_name] = {
                'date': date,
                'carrier': carrier,
                'dealer': dealer,
                'device_name': device_name
            }
        
        # 매핑 정보에 따라 데이터 추출
        for mapping in column_mapping:
            col_idx = mapping['col']
            if col_idx < len(df.columns):
                value = df.iloc[idx, col_idx]
                if pd.notna(value) and isinstance(value, (int, float)) and value != 0:
                    key = f"{mapping['type']}_{mapping['support']}_{mapping['plan']}"
                    device_data[device_name][key] = value
    
    return list(device_data.values())

def extract_sk_kei_data(file_path, date, carrier, dealer):
    """SK 케이 파일에서 데이터 추출 - 특수 구조"""

    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 딕셔너리
    device_data = {}
    
    # 파일 타입 확인 (calculated 파일인지 tables 파일인지)
    is_calculated = "_calculated" in file_path
    
    # SK_케이 구조:
    # tables 파일:
    #   1-2행: 헤더
    #   3행: 타이틀 (모델명, MNP, 기변)
    #   4행: 요금제 정보
    #   5행: 공시/선약 구분
    #   6행부터: A열=모델명, B~K열=MNP 데이터, L~U열=기기변경 데이터
    # calculated 파일:
    #   행 인덱스가 1씩 줄어듦
    #   3행: 요금제 정보
    #   4행: 공시/선약 구분
    #   5행부터: 데이터
    
    # 요금제 정보 파싱
    plan_info = {}
    plan_row_idx = 2 if is_calculated else 3  # calculated: 3행(idx 2), tables: 4행(idx 3)
    if len(df) > plan_row_idx:
        # 각 열의 요금제 정보 파싱
        # MNP: B~K열 (1-10), 기기변경: L~U열 (11-20)
        # 각 요금제마다 공시/선약 2개씩
        plan_sequence = ["109k", "100k", "79k", "69k", "43k"]
        
        # MNP 섹션 (열 1-10)
        plan_idx = 0
        for col_idx in range(1, 11):  # B~K열
            if col_idx % 2 == 1:  # 홀수 열은 새로운 요금제 시작
                if plan_idx < len(plan_sequence):
                    plan_info[col_idx] = plan_sequence[plan_idx]
                    plan_info[col_idx + 1] = plan_sequence[plan_idx]
                    plan_idx += 1
        
        # 기기변경 섹션 (열 11-20)
        plan_idx = 0
        for col_idx in range(11, 21):  # L~U열
            if (col_idx - 10) % 2 == 1:  # 홀수 열은 새로운 요금제 시작
                if plan_idx < len(plan_sequence):
                    plan_info[col_idx] = plan_sequence[plan_idx]
                    plan_info[col_idx + 1] = plan_sequence[plan_idx]
                    plan_idx += 1
    
    # 공시/선약 구분
    support_info = {}
    support_row_idx = 3 if is_calculated else 4  # calculated: 4행(idx 3), tables: 5행(idx 4)
    if len(df) > support_row_idx:
        # 모든 열에 대해 공시/선약 패턴 적용 (홀수열=공시, 짝수열=선약)
        for col_idx in range(1, len(df.columns)):
            if col_idx % 2 == 1:
                support_info[col_idx] = "공시"
            else:
                support_info[col_idx] = "선약"
    
    # 데이터 처리
    data_start_idx = 4 if is_calculated else 5  # calculated: 5행부터, tables: 6행부터
    for idx in range(data_start_idx, len(df)):
        # A열의 모델명이 device_name
        device_name = df.iloc[idx, 0]  # A열
        
        if pd.isna(device_name) or device_name == '' or not isinstance(device_name, str):
            continue
        
        # 기기별 데이터 초기화
        if device_name not in device_data:
            device_data[device_name] = {
                'date': date,
                'carrier': carrier,
                'dealer': dealer,
                'device_name': device_name
            }
        
        # 각 열의 값을 추출 (B열부터)
        for col_idx in range(1, len(df.columns)):
            value = df.iloc[idx, col_idx]
            if pd.notna(value) and isinstance(value, (int, float)):
                # 요금제와 지원 유형 결합
                plan = plan_info.get(col_idx, f"col{col_idx}")
                support = support_info.get(col_idx, "공시")
                
                # MNP인지 기기변경인지 구분 (B~K열: MNP, L~U열: 기기변경)
                if col_idx <= 10:
                    join_type = "번호이동"
                else:
                    join_type = "기기변경"
                
                key = f"{join_type}_{support}_{plan}"
                device_data[device_name][key] = value
    
    return list(device_data.values())

def extract_sk_daekyo_data(file_path, date, carrier, dealer):
    """SK 대교 전용 데이터 추출 함수"""
    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 리스트
    all_data = []
    
    # SK 대교 구조:
    # Row 1: 헤더 (모델명, 출고가격, 요금제명들)
    # Row 2: 공시/선택 구분
    # Row 3: 가입유형 (공통, 010, 전환, MNP, 기변 등)
    # Row 4부터: 기기별 데이터
    # 특징: 모델명이 A열과 B열로 나뉘어 있음
    
    print(f"SK 대교 파일 처리: {file_path}")
    print(f"파일 크기: {df.shape}")
    
    # 요금제 매핑
    plan_mapping = {
        # 열 위치별 요금제 구분
        (3, 10): '109k',   # 플래티넘/0청년 109
        (11, 18): '100k',  # 맥스/프라임+ (I_100 구간)
        (19, 26): '89k',   # 프라임 (F_79 구간)
        (27, 34): '79k',   # 스페셜/레귤러 (F_69 구간)
        (35, 42): '50k',   # 베이직+ (M_50 구간)
        (43, 50): '43k',   # 안심2.5G/컴팩트 (R_43 구간)
        (51, 58): '33k'    # 세이브 (S_33 구간)
    }
    
    # Row 4부터 기기별 데이터 추출
    for row_idx in range(4, len(df)):
        # A열 또는 B열에서 모델명 가져오기
        device_name = df.iloc[row_idx, 0]  # A열
        if pd.isna(device_name) or not str(device_name).strip():
            device_name = df.iloc[row_idx, 1]  # B열
        
        if pd.isna(device_name) or not str(device_name).strip():
            continue
            
        device_name = str(device_name).strip()
        
        # 기기별 데이터 수집
        device_info = {
            'date': date,
            'carrier': carrier,
            'dealer': dealer,
            'device_name': device_name
        }
        
        # 각 요금제별로 데이터 추출
        # 실제 컬럼 매핑 (분석 결과 기반)
        plan_columns = {
            '109k': {'공시_010': 3, '공시_mnp': 5, '공시_기변': 6, '선약_010': 7, '선약_mnp': 8, '선약_기변': 9},
            '100k': {'공시_010': 10, '공시_mnp': 13, '공시_기변': 14, '선약_010': 15, '선약_mnp': 16, '선약_기변': 17},
            # 89k는 대교에 없음
            '79k': {'공시_010': 18, '공시_mnp': 21, '공시_기변': 22, '선약_010': 23, '선약_mnp': 24, '선약_기변': 25},  # F_79 구간
            '69k': {'공시_010': 26, '공시_mnp': 29, '공시_기변': 30, '선약_010': 31, '선약_mnp': 32, '선약_기변': 33},  # L_69 구간
            '50k': {'공시_010': 34, '공시_mnp': 37, '공시_기변': 38, '선약_010': 39, '선약_mnp': 40, '선약_기변': 41},  # M_50 구간
            '43k': {'공시_010': 42, '공시_mnp': 45, '공시_기변': 46, '선약_010': 47, '선약_mnp': 48, '선약_기변': 49},  # R_43 구간
            '33k': {'공시_010': 50, '공시_mnp': 53, '공시_기변': 54, '선약_010': 55, '선약_mnp': 56}  # S_33 구간
        }
        
        for plan_name, cols in plan_columns.items():
            # 선택약정을 먼저 처리 (공시와 컬럼이 겹치는 경우가 있음)
            if '선약_010' in cols:
                col_idx = cols['선약_010']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'신규가입_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
            
            # 선택약정 - MNP
            if '선약_mnp' in cols:
                col_idx = cols['선약_mnp']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'번호이동_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
            
            # 선택약정 - 기변
            if '선약_기변' in cols:
                col_idx = cols['선약_기변']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'기기변경_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
            
            # 선택약정 - MNP/기변 공통
            if '선약_mnp_기변' in cols:
                col_idx = cols['선약_mnp_기변']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'번호이동_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
                    device_info[f'기기변경_선약_{plan_name}'] = df.iloc[row_idx, col_idx]

            # 선택약정 - 010/MNP 공통 (100k, 33k용)
            if '선약_010_mnp' in cols:
                col_idx = cols['선약_010_mnp']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'신규가입_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
                    device_info[f'번호이동_선약_{plan_name}'] = df.iloc[row_idx, col_idx]

            # 선택약정 - 010/MNP/기변 공통 (100k용)
            if '선약_010_mnp_기변' in cols:
                col_idx = cols['선약_010_mnp_기변']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'신규가입_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
                    device_info[f'번호이동_선약_{plan_name}'] = df.iloc[row_idx, col_idx]
                    device_info[f'기기변경_선약_{plan_name}'] = df.iloc[row_idx, col_idx]

            # 공시지원금 처리 (선약 처리 이후)
            # 신규가입 010
            if '공시_010' in cols:
                col_idx = cols['공시_010']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'신규가입_공시_{plan_name}'] = df.iloc[row_idx, col_idx]

            # 번호이동 MNP
            if '공시_mnp' in cols:
                col_idx = cols['공시_mnp']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'번호이동_공시_{plan_name}'] = df.iloc[row_idx, col_idx]

            # 기기변경
            if '공시_기변' in cols:
                col_idx = cols['공시_기변']
                if col_idx < len(df.columns) and pd.notna(df.iloc[row_idx, col_idx]) and isinstance(df.iloc[row_idx, col_idx], (int, float)):
                    device_info[f'기기변경_공시_{plan_name}'] = df.iloc[row_idx, col_idx]

        all_data.append(device_info)
    
    print(f"SK 대교: {len(all_data)}개 기기 추출됨")
    return all_data


def extract_sk_telcom_data(file_path, date, carrier, dealer):
    """SK 텔컴 전용 데이터 추출 함수"""
    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 리스트
    all_data = []
    
    # SK 텔컴 구조:
    # Row 0: 빈 행
    # Row 1: 모델명, 공시지원금 선택약정
    # Row 2: 요금제명들 (5G 슬림, 5GX 프라임플러스, 5GX 프리미엄)
    # Row 3: 가입 유형 (010=신규, MNP=번호이동, 기변=기기변경)
    # Row 4부터: 기기별 데이터
    
    # 요금제 매핑
    plan_mapping = {
        '5G 슬림': '69k',            # 월 69,000원
        '5GX 프라임플러스': '100k',  # 월 100,000원
        '5GX 프리미엄': '109k'       # 월 109,000원
    }
    
    # 각 열의 요금제와 가입 유형 파악
    column_info = {}
    
    # Row 2와 Row 3을 함께 분석하여 column_info 생성
    current_plan = None
    for col_idx in range(1, len(df.columns)):
        # 요금제 정보 확인
        plan_name = df.iloc[2, col_idx]
        if pd.notna(plan_name) and plan_name in plan_mapping:
            current_plan = plan_mapping[plan_name]
        
        # 가입 유형 정보 확인
        join_type = df.iloc[3, col_idx]
        if pd.notna(join_type) and current_plan:
            if join_type == '010':
                column_info[col_idx] = {'plan': current_plan, 'join_type': '신규가입'}
            elif join_type == 'MNP':
                column_info[col_idx] = {'plan': current_plan, 'join_type': '번호이동'}
            elif join_type == '기변':
                column_info[col_idx] = {'plan': current_plan, 'join_type': '기기변경'}
    
    # Row 1의 공시/선약 구분
    # J열(인덱스 9)까지는 공시지원금, K열(인덱스 10)부터는 선택약정
    for col_idx in column_info:
        if col_idx <= 9:  # A=0, B=1, ..., J=9
            column_info[col_idx]['support_type'] = '공시'
        else:
            column_info[col_idx]['support_type'] = '선약'
    
    # 데이터 추출 (Row 4부터)
    for row_idx in range(4, len(df)):
        device_name = df.iloc[row_idx, 0]
        
        if pd.isna(device_name) or not isinstance(device_name, str):
            continue
        
        # 아이폰 제품명 처리
        if device_name == "아이폰16,16+":
            device_names = ["iPhone 16", "iPhone 16 Plus"]
        elif device_name == "아이폰16P,PM":
            device_names = ["iPhone 16 Pro", "iPhone 16 Pro Max"]
        else:
            device_names = [device_name]
        
        # 각 디바이스별로 데이터 생성
        for final_device_name in device_names:
            device_data = {
                'date': date,
                'carrier': carrier,
                'dealer': dealer,
                'device_name': final_device_name
            }
            
            # 각 열의 값 추출
            for col_idx, info in column_info.items():
                value = df.iloc[row_idx, col_idx]
                if pd.notna(value) and isinstance(value, (int, float)) and value > 0:
                    key = f"{info['join_type']}_{info['support_type']}_{info['plan']}"
                    device_data[key] = value
            
            all_data.append(device_data)
    
    return all_data

def extract_sk_gwangjang_data(file_path, date, carrier, dealer):
    """SK 광장 전용 데이터 추출 함수 - 010(신규) 제외"""
    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 리스트
    all_data = []
    
    # SK 광장 구조:
    # Row 1: 가입 유형 (010=신규가입, MNP=번호이동, 기변=기기변경)
    # Row 2: 요금제 정보 (I_100, F_79, L_69, R_43, S_33)
    # Row 3: 공시/선약 구분
    # Row 4부터: 기기별 데이터
    
    # 요금제 매핑
    plan_mapping = {
        'I_100': '100k',
        'l_100': '100k',  # 소문자 l
        'F_79': '79k',
        'L_69': '69k',
        'R_43': '43k',
        'S_33': '33k'
    }
    
    # 컬럼 매핑을 수동으로 정의 (분석 결과 기반)
    column_info = {}
    
    # 010(신규) 섹션 (Col 3-7) - 제외
    # MNP 섹션 (Col 8-17)
    column_info[8] = {'join_type': '번호이동', 'plan': '100k', 'support': '공시'}
    column_info[9] = {'join_type': '번호이동', 'plan': '100k', 'support': '선약'}
    column_info[10] = {'join_type': '번호이동', 'plan': '79k', 'support': '공시'}
    column_info[11] = {'join_type': '번호이동', 'plan': '79k', 'support': '선약'}
    column_info[12] = {'join_type': '번호이동', 'plan': '69k', 'support': '공시'}
    column_info[13] = {'join_type': '번호이동', 'plan': '69k', 'support': '선약'}
    column_info[14] = {'join_type': '번호이동', 'plan': '43k', 'support': '공시'}
    column_info[15] = {'join_type': '번호이동', 'plan': '43k', 'support': '선약'}
    column_info[16] = {'join_type': '번호이동', 'plan': '33k', 'support': '공시'}
    column_info[17] = {'join_type': '번호이동', 'plan': '33k', 'support': '선약'}
    
    # 기기변경 섹션 (Col 18-27)
    column_info[18] = {'join_type': '기기변경', 'plan': '100k', 'support': '공시'}
    column_info[19] = {'join_type': '기기변경', 'plan': '100k', 'support': '선약'}
    column_info[20] = {'join_type': '기기변경', 'plan': '79k', 'support': '공시'}
    column_info[21] = {'join_type': '기기변경', 'plan': '79k', 'support': '선약'}
    column_info[22] = {'join_type': '기기변경', 'plan': '69k', 'support': '공시'}
    column_info[23] = {'join_type': '기기변경', 'plan': '69k', 'support': '선약'}
    column_info[24] = {'join_type': '기기변경', 'plan': '43k', 'support': '공시'}
    column_info[25] = {'join_type': '기기변경', 'plan': '43k', 'support': '선약'}
    column_info[26] = {'join_type': '기기변경', 'plan': '33k', 'support': '공시'}
    column_info[27] = {'join_type': '기기변경', 'plan': '33k', 'support': '선약'}
    
    print(f"SK 광장 컬럼 정보: {len(column_info)}개 컬럼 매핑됨")
    
    # 데이터 추출 (Row 4부터)
    for row_idx in range(4, len(df)):
        device_name = df.iloc[row_idx, 0]
        
        if pd.isna(device_name) or not isinstance(device_name, str):
            continue
        
        device_name = str(device_name).strip()
        
        # 디바이스명 정규화
        if device_name.startswith('IP16'):
            # iPhone 16 시리즈 처리
            if device_name == 'IP16_128GB':
                device_name = 'iPhone 16'
            elif device_name == 'IP16PL_128GB':
                device_name = 'iPhone 16 Plus'
            elif device_name == 'IP16P_128GB':
                device_name = 'iPhone 16 Pro'
            elif device_name == 'IP16PM_256GB':
                device_name = 'iPhone 16 Pro Max'
            elif device_name == 'IP16E_128GB' or device_name == 'IP16E_256GB':
                device_name = 'iPhone SE'
        elif device_name.startswith('IP15'):
            # iPhone 15 시리즈 처리
            if device_name == 'IP15_128GB':
                device_name = 'iPhone 15'
            elif device_name == 'IP15PL_128GB':
                device_name = 'iPhone 15 Plus'
            elif device_name == 'IP15P_128GB':
                device_name = 'iPhone 15 Pro'
        elif device_name == 'IPHONE_13_128GB':
            device_name = 'iPhone 13'
        elif device_name.startswith('SM-'):
            # 갤럭시 모델명은 그대로 유지
            pass
        elif device_name.startswith('AT-'):
            # AT 모델명도 그대로 유지
            pass
        
        # 디바이스 데이터 초기화
        device_data = {
            'date': date,
            'carrier': carrier,
            'dealer': dealer,
            'device_name': device_name
        }
        
        # 각 컬럼의 값 추출
        for col_idx, info in column_info.items():
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, (int, float)):
                key = f"{info['join_type']}_{info['support']}_{info['plan']}"
                device_data[key] = value
        
        # 데이터가 있는 경우만 추가
        if len(device_data) > 4:  # 기본 4개 필드 외에 데이터가 있는 경우
            all_data.append(device_data)
    
    print(f"SK 광장: {len(all_data)}개 기기 추출됨")
    return all_data

# SK 사전예약 관련 함수 제거

def merge_sk_files():
    """모든 SK 파일을 병합"""
    from shared_config.config.data_merge_config import find_latest_ocr_results_folder
    
    base_path = find_latest_ocr_results_folder()
    if not base_path:
        return None
    
    # 폴더명에서 날짜 추출 (20250714 -> 2025. 7. 14)
    folder_name = os.path.basename(base_path)
    if len(folder_name) == 8 and folder_name.isdigit():
        year = folder_name[:4]
        month = str(int(folder_name[4:6]))  # 앞의 0 제거
        day = folder_name[6:8]              # 일자는 2자리 유지
        date_str = f"{year}. {month}. {day}"
    else:
        date_str = "2025. 7. 14"  # 기본값
    
    all_data = []
    
    # SK 나텔은 더 이상 입점사가 아니므로 제거됨
    
    # SK 상상 파일 처리 - calculated 파일만 (애플사전예약 제외)
    sangsang_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        # 애플사전예약이 아닌 일반 상상 파일만 처리
        if "SK" in normalized_file and "상상" in normalized_file and file.endswith("_calculated.xlsx") and "애플사전예약" not in normalized_file:
            sangsang_file = os.path.join(base_path, file)
            break

    if sangsang_file and os.path.exists(sangsang_file):
        print(f"SK 상상 파일 처리 중: {os.path.basename(sangsang_file)}")
        sangsang_data = extract_sk_sangsang_data(sangsang_file, date_str, "SK", "상상")
        all_data.extend(sangsang_data)
        print(f"SK 상상: {len(sangsang_data)}개 기기 추출")
    
    # SK 윤텔 파일 처리 - calculated 파일만 사용
    yuntel_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "SK" in normalized_file and "윤텔" in normalized_file and file.endswith("_calculated.xlsx"):
            yuntel_file = os.path.join(base_path, file)
            break
    
    if yuntel_file and os.path.exists(yuntel_file):
        print(f"SK 윤텔 파일 처리 중: {os.path.basename(yuntel_file)}")
        yuntel_data = extract_sk_yuntel_data(yuntel_file, date_str, "SK", "윤텔")
        all_data.extend(yuntel_data)
        print(f"SK 윤텔: {len(yuntel_data)}개 기기 추출")
    
    # SK 케이 파일 처리 - calculated 파일만 (애플사전예약 제외)
    kei_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        # 애플사전예약이 아닌 일반 케이 파일만 처리
        if "SK" in normalized_file and "케이" in normalized_file and file.endswith("_calculated.xlsx") and "애플사전예약" not in normalized_file:
            kei_file = os.path.join(base_path, file)
            break

    if kei_file and os.path.exists(kei_file):
        print(f"SK 케이 파일 처리 중: {os.path.basename(kei_file)}")
        kei_data = extract_sk_kei_data(kei_file, date_str, "SK", "케이")
        all_data.extend(kei_data)
        print(f"SK 케이: {len(kei_data)}개 기기 추출")
    
    # SK 텔컴 파일 처리 - calculated 파일만 사용
    telcom_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "SK" in normalized_file and "텔컴" in normalized_file and file.endswith("_calculated.xlsx"):
            telcom_file = os.path.join(base_path, file)
            break
    
    if telcom_file and os.path.exists(telcom_file):
        print(f"SK 텔컴 파일 처리 중: {os.path.basename(telcom_file)}")
        telcom_data = extract_sk_telcom_data(telcom_file, date_str, "SK", "텔컴")  # SK 텔컴 전용 함수 사용
        all_data.extend(telcom_data)
        print(f"SK 텔컴: {len(telcom_data)}개 기기 추출")
    
    # SK 대교 파일 찾기 (새로 추가)
    daekyo_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "SK" in normalized_file and "대교" in normalized_file and file.endswith("_calculated.xlsx"):
            daekyo_file = os.path.join(base_path, file)
            break
    
    if daekyo_file and os.path.exists(daekyo_file):
        print(f"SK 대교 파일 처리 중: {os.path.basename(daekyo_file)}")
        daekyo_data = extract_sk_daekyo_data(daekyo_file, date_str, "SK", "대교")  # SK 대교 전용 함수 사용
        all_data.extend(daekyo_data)
        print(f"SK 대교: {len(daekyo_data)}개 기기 추출")
    
    # SK 번개폰 파일 처리 - calculated 파일만 사용
    bungyae_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "SK" in normalized_file and "번개폰" in normalized_file and file.endswith("_calculated.xlsx"):
            bungyae_file = os.path.join(base_path, file)
            break

    if bungyae_file and os.path.exists(bungyae_file):
        print(f"SK 번개폰 파일 처리 중: {os.path.basename(bungyae_file)}")
        bungyae_data = extract_data_from_번개폰(bungyae_file, date_str, "SK", "번개폰")
        all_data.extend(bungyae_data)
        print(f"SK 번개폰: {len(bungyae_data)}개 기기 추출")

    # SK 광장 파일 찾기 (새로 추가)
    gwangjang_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "SK" in normalized_file and "광장" in normalized_file and file.endswith("_calculated.xlsx"):
            gwangjang_file = os.path.join(base_path, file)
            break

    if gwangjang_file and os.path.exists(gwangjang_file):
        print(f"SK 광장 파일 처리 중: {os.path.basename(gwangjang_file)}")
        gwangjang_data = extract_sk_gwangjang_data(gwangjang_file, date_str, "SK", "광장")  # SK 광장 전용 함수 사용
        all_data.extend(gwangjang_data)
        print(f"SK 광장: {len(gwangjang_data)}개 기기 추출")

    # SK 애플사전예약 파일 처리 - _calculated 파일만 사용
    apple_preorder_files = []
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        # _calculated 파일만 처리
        if "SK" in normalized_file and "애플사전예약" in normalized_file and file.endswith("_calculated.xlsx"):
            apple_preorder_files.append(os.path.join(base_path, file))

    for apple_file in apple_preorder_files:
        if os.path.exists(apple_file):
            print(f"SK 애플사전예약 파일 처리 중: {os.path.basename(apple_file)}")
            # 파일명에서 대리점명 추출 (예: 250915_SK_상상_애플사전예약 -> 상상_애플사전예약)
            filename = os.path.basename(apple_file)
            print(f"  파일명: {filename}")

            # 유니코드 정규화 적용
            normalized_filename = unicodedata.normalize('NFC', filename)
            print(f"  정규화된 파일명: {normalized_filename}")
            print(f"  상상 포함: {'상상' in normalized_filename}")
            print(f"  케이 포함: {'케이' in normalized_filename}")

            if "상상" in normalized_filename or "상상" in filename:
                dealer_name = "상상_애플사전예약"
            elif "케이" in normalized_filename or "케이" in filename:
                dealer_name = "케이_애플사전예약"
            else:
                dealer_name = "애플사전예약"

            print(f"  -> dealer_name 설정: {dealer_name}")

            apple_data = extract_apple_preorder_data(apple_file, date_str, "SK", dealer_name)
            all_data.extend(apple_data)
            print(f"SK {dealer_name}: {len(apple_data)}개 기기 추출")
    
    
    # DataFrame으로 변환
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 모든 가능한 컬럼 정의
        base_columns = ['date', 'carrier', 'dealer', 'device_name']
        plan_types = ['33k', '43k', '50k', '69k', '79k', '89k', '100k', '109k']
        join_types = ['신규가입', '번호이동', '기기변경']
        support_types = ['공시', '선약']
        
        # 동적 컬럼 생성
        dynamic_columns = []
        for join_type in join_types:
            for support_type in support_types:
                for plan_type in plan_types:
                    dynamic_columns.append(f'{join_type}_{support_type}_{plan_type}')
        
        # 전체 컬럼 리스트
        all_columns = base_columns + dynamic_columns
        
        # 누락된 컬럼 추가
        for col in all_columns:
            if col not in df.columns:
                df[col] = None
        
        # 컬럼 순서 정렬
        df = df[all_columns]
        
        # 빈 값 처리 - 선약 컬럼은 빈 값 유지, 나머지는 'Null'로 채우기
        seon_yak_columns = [col for col in df.columns if '선약' in col]
        for col in df.columns:
            if col not in seon_yak_columns:
                df[col] = df[col].fillna('Null')
        
        # PathManager를 사용한 출력 경로 설정
        from shared_config.config.paths import PathManager
        pm = PathManager()
        archive_path, latest_path = pm.get_merged_output_path('sk', is_rebated=False, with_colors=False)

        # 결과 저장
        output_file = archive_path
        df.to_excel(str(output_file), index=False)

        # latest 파일로 복사
        pm.save_with_archive(archive_path, archive_path, latest_path)

        print(f"\n병합 완료!")
        print(f"총 {len(df)}개 기기")
        print(f"📁 Archive: {archive_path}")
        print(f"📁 Latest: {latest_path}")
        
        # 데이터 검증
        print("\n데이터 검증:")
        # SK 나텔은 더 이상 입점사가 아니므로 제거
        print(f"SK 상상 기기 수: {len(df[df['dealer'] == '상상'])}")
        print(f"SK 윤텔 기기 수: {len(df[df['dealer'] == '윤텔'])}")
        print(f"SK 케이 기기 수: {len(df[df['dealer'] == '케이'])}")
        print(f"SK 텔컴 기기 수: {len(df[df['dealer'] == '텔컴'])}")
        print(f"SK 대교 기기 수: {len(df[df['dealer'] == '대교'])}")
        print(f"SK 광장 기기 수: {len(df[df['dealer'] == '광장'])}")
        print(f"SK 상상_애플사전예약 기기 수: {len(df[df['dealer'] == '상상_애플사전예약'])}")
        print(f"SK 케이_애플사전예약 기기 수: {len(df[df['dealer'] == '케이_애플사전예약'])}")
        
        # 선약 데이터 확인
        print(f"\n선약 데이터 확인 (상상만 해당):")
        dealer = '상상'
        dealer_df = df[df['dealer'] == dealer]
        if len(dealer_df) > 0:
            선약_count = 0
            for col in df.columns:
                if '선약' in col and (dealer_df[col] != 'Null').sum() > 0:
                    선약_count += 1
            print(f"{dealer}: {선약_count}개 선약 컬럼에 데이터 있음")
        
        return df
    else:
        print("추출된 데이터가 없습니다.")
        return None

if __name__ == "__main__":
    df = merge_sk_files()