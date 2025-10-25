import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import unicodedata
import copy

def extract_data_from_번개폰(file_path, date, carrier, dealer):
    """번개폰 파일에서 데이터 추출 (LG용)"""
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

        # LG 번개폰 실제 컬럼 구조:
        # 0열: 기기명
        # 1열: 110k/109k 번호이동 선약
        # 2열: 110k/109k 기기변경 선약
        # 3열: 109k 번호이동 공시
        # 4열: 109k 기기변경 공시

        # 1열: 번호이동 선약 (115k로 매핑)
        if pd.notna(df.iloc[idx, 1]):
            device_data[device_name]['번호이동_선약_115k'] = df.iloc[idx, 1]

        # 2열: 기기변경 선약 (115k로 매핑)
        if pd.notna(df.iloc[idx, 2]):
            device_data[device_name]['기기변경_선약_115k'] = df.iloc[idx, 2]

        # 3열: 번호이동 공시 (105k로 매핑)
        if pd.notna(df.iloc[idx, 3]):
            device_data[device_name]['번호이동_공시_105k'] = df.iloc[idx, 3]
            device_data[device_name]['번호이동_선약_105k'] = df.iloc[idx, 3]  # LG는 선약도 같이
            # 115k에도 동일 값 설정
            device_data[device_name]['번호이동_공시_115k'] = df.iloc[idx, 3]

        # 4열: 기기변경 공시 (105k로 매핑)
        if pd.notna(df.iloc[idx, 4]):
            device_data[device_name]['기기변경_공시_105k'] = df.iloc[idx, 4]
            device_data[device_name]['기기변경_선약_105k'] = df.iloc[idx, 4]  # LG는 선약도 같이
            # 115k에도 동일 값 설정
            device_data[device_name]['기기변경_공시_115k'] = df.iloc[idx, 4]

    return list(device_data.values())

def split_device_by_storage(device_name):
    """기기명에서 용량 정보를 분리하여 여러 기기로 나눔
    예: '갤럭시 폴드6(256,512)' -> [('갤럭시 폴드6 256GB', '256GB'), ('갤럭시 폴드6 512GB', '512GB')]
    예: 'F966-512G/1TB' -> [('F966-512G', '512G'), ('F966-1TB', '1TB')]
    """
    import re

    # F966-512G/1TB 같은 패턴 처리
    if '/' in device_name and '-' in device_name:
        # 기본 모델명 추출 (예: F966)
        parts = device_name.split('-')
        if len(parts) >= 2:
            base_name = parts[0]
            # 용량 부분 (예: 512G/1TB)
            storage_part = '-'.join(parts[1:])
            # '/'로 분리
            storages = storage_part.split('/')

            result = []
            for storage in storages:
                storage = storage.strip()
                # 각 용량별로 새로운 기기명 생성
                new_device_name = f"{base_name}-{storage}"
                result.append((new_device_name, storage))

            return result

    # 괄호 안의 용량 정보 찾기 (예: (256,512) 또는 (256.512))
    match = re.search(r'\(([0-9,.\s]+)\)', device_name)
    if match:
        # 괄호 앞의 기기명
        base_name = device_name[:match.start()].strip()
        # 괄호 안의 용량들
        storage_str = match.group(1)
        # 쉼표 또는 점으로 구분
        if ',' in storage_str:
            storages = [s.strip() for s in storage_str.split(',')]
        else:
            storages = [s.strip() for s in storage_str.split('.')]

        # 각 용량별로 기기명 생성
        result = []
        for storage in storages:
            # 숫자만 있으면 GB 추가
            if storage.isdigit():
                storage_gb = f"{storage}GB"
            else:
                storage_gb = storage

            # 새로운 기기명
            new_device_name = f"{base_name} {storage_gb}"
            result.append((new_device_name, storage_gb))

        return result
    else:
        # 용량 정보가 없는 경우 원본 그대로 반환
        return [(device_name, '')]

def extract_data_from_lg_bk(file_path, date, carrier, dealer):
    """LG 비케이 파일에서 데이터 추출"""
    df = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # 결과를 저장할 딕셔너리
    device_data = {}
    
    # 비케이2인지 일반 비케이인지 구분
    is_bk2 = "비케이2" in dealer
    
    if is_bk2:
        # 비케이2 구조:
        # 행0-2: 헤더
        # 행3: 구분/모델/가입유형 헤더
        # 행4부터: 실제 데이터 (1열=기기명, 2열=모델코드, 3열부터=금액)
        start_row = 4
        device_col = 1  # 기기명은 1열에 있음
        
        # 요금제 매핑 (비케이2는 3열부터 데이터)
        plan_mapping = [
            {'cols': [3, 4], 'plan': '115k', 'types': ['번호이동', '기기변경']},
            {'cols': [5, 6], 'plan': '105k', 'types': ['번호이동', '기기변경']},
            {'cols': [7, 8], 'plan': '95k', 'types': ['번호이동', '기기변경']},
            {'cols': [9, 10], 'plan': '61k', 'types': ['번호이동', '기기변경']},
        ]
    else:
        # 일반 비케이 구조:
        # 행0-2: 헤더
        # 행3부터: 실제 데이터 (0열=기기명, 2열부터=금액)
        start_row = 3
        device_col = 0  # 기기명은 0열에 있음
        
        # 요금제 매핑 (일반 비케이는 2열부터 데이터)
        plan_mapping = [
            {'cols': [2, 3], 'plan': '115k', 'types': ['번호이동', '기기변경']},
            {'cols': [4, 5], 'plan': '105k', 'types': ['번호이동', '기기변경']},
            {'cols': [6, 7], 'plan': '95k', 'types': ['번호이동', '기기변경']},
            {'cols': [8, 9], 'plan': '61k', 'types': ['번호이동', '기기변경']},
        ]
    
    # 기기별 데이터 처리
    for idx in range(start_row, len(df)):
        device_name = df.iloc[idx, device_col]
        
        # 기기명이 없거나 헤더인 경우 건너뛰기
        if pd.isna(device_name):
            continue
            
        device_name = str(device_name)
        
        # 헤더 텍스트 건너뛰기
        if device_name in ['모델', '모델류', 'device', 'Device', '구분']:
            continue
        
        # 용량별로 기기 분리
        device_variants = split_device_by_storage(device_name)
        
        # 각 용량별로 데이터 생성
        for new_device_name, storage_info in device_variants:
            # 기기별 데이터 초기화
            if new_device_name not in device_data:
                device_data[new_device_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': new_device_name
                }
        
        # 각 요금제 그룹별로 데이터 추출
        for plan_info in plan_mapping:
            plan = plan_info['plan']
            for col_offset, join_type in enumerate(plan_info['types']):
                col_idx = plan_info['cols'][col_offset]
                if col_idx < len(df.columns):
                    value = df.iloc[idx, col_idx]
                    
                    # 값 처리: 문자열로 된 숫자를 정수로 변환하고, 100 미만이면 만원 단위로 처리
                    if pd.notna(value):
                        try:
                            # 문자열이나 숫자를 float로 변환
                            num_value = float(str(value).replace(',', ''))
                            # 100 미만이면 만원 단위로 간주하여 10000을 곱함
                            if num_value < 1000:
                                num_value = int(num_value * 10000)
                            else:
                                num_value = int(num_value)
                            value = num_value
                        except:
                            # 변환 실패시 원본 값 유지
                            pass
                    
                    # 각 용량별로 동일한 값 설정
                    for new_device_name, _ in device_variants:
                        # 공시지원금
                        key = f"{join_type}_공시_{plan}"
                        device_data[new_device_name][key] = value if pd.notna(value) else None
                        # LG_비케이는 선택약정도 동일한 값으로 추가
                        key_선약 = f"{join_type}_선약_{plan}"
                        device_data[new_device_name][key_선약] = value if pd.notna(value) else None
    
    return list(device_data.values())

def extract_data_from_lg_lk(file_path, date, carrier, dealer):
    """LG 엘에스 파일에서 데이터 추출"""
    df = pd.read_excel(file_path, sheet_name=0)
    
    # 결과를 저장할 딕셔너리
    device_data = {}
    
    # LG 엘에스의 경우:
    # 1행: 요금제 정보 (115군, 105군, 95군)
    # 2행: 가입 유형 (MNP, 재가입=기기변경)
    # 3행부터: 기기별 데이터
    
    # 각 요금제 그룹과 열 매핑 (61k 없음)
    plan_mapping = [
        # 115k 그룹 (열 1-2)
        {'cols': [1, 2], 'plan': '115k', 'types': ['번호이동', '기기변경']},
        # 105k 그룹 (열 3-4)
        {'cols': [3, 4], 'plan': '105k', 'types': ['번호이동', '기기변경']},
        # 95k 그룹 (열 5-6)
        {'cols': [5, 6], 'plan': '95k', 'types': ['번호이동', '기기변경']},
    ]
    
    # 기기별 데이터 처리 (3행부터)
    for idx in range(3, len(df)):
        device_name = df.iloc[idx, 0]
        
        if pd.isna(device_name) or device_name == '':
            continue
        
        # 용량별로 기기 분리
        device_variants = split_device_by_storage(str(device_name))
        
        # 각 용량별로 데이터 생성
        for new_device_name, storage_info in device_variants:
            # 기기별 데이터 초기화
            if new_device_name not in device_data:
                device_data[new_device_name] = {
                    'date': date,
                    'carrier': carrier,
                    'dealer': dealer,
                    'device_name': new_device_name
                }
        
        # 각 요금제 그룹별로 데이터 추출
        for plan_info in plan_mapping:
            plan = plan_info['plan']
            for col_offset, join_type in enumerate(plan_info['types']):
                col_idx = plan_info['cols'][col_offset]
                if col_idx < len(df.columns):
                    value = df.iloc[idx, col_idx]
                    # 각 용량별로 동일한 값 설정
                    for new_device_name, _ in device_variants:
                        # 공시지원금
                        key = f"{join_type}_공시_{plan}"
                        device_data[new_device_name][key] = value if pd.notna(value) else None
                        # LG_엘에스는 선택약정도 동일한 값으로 추가
                        key_선약 = f"{join_type}_선약_{plan}"
                        device_data[new_device_name][key_선약] = value if pd.notna(value) else None
    
    return list(device_data.values())

# LG 사전예약 관련 함수 제거

def merge_lg_files():
    """모든 LG 파일을 병합"""
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
    
    # LG 비케이 파일 처리 - calculated 파일만 사용 (비케이2 제외)
    bk_files = []
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        # 비케이2가 아닌 비케이 파일만 처리
        if "LG" in normalized_file and "비케이" in normalized_file and "비케이2" not in normalized_file and file.endswith("_calculated.xlsx"):
            bk_files.append(os.path.join(base_path, file))
    
    # 모든 비케이 파일 처리
    for idx, bk_file in enumerate(bk_files):
        if os.path.exists(bk_file):
            file_name = os.path.basename(bk_file)
            print(f"LG 비케이 파일 처리 중... ({file_name})")
            bk_data = extract_data_from_lg_bk(bk_file, date_str, "LG", "비케이")
            all_data.extend(bk_data)
            print(f"  → {len(bk_data)}개 기기 추출")
    
    # LG 엘에스 파일 처리 - calculated 파일만 사용
    lk_files = []
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "LG" in normalized_file and "엘에스" in normalized_file and file.endswith("_calculated.xlsx"):
            lk_files.append(os.path.join(base_path, file))
    
    # 모든 엘에스 파일 처리
    for idx, lk_file in enumerate(lk_files):
        if os.path.exists(lk_file):
            file_name = os.path.basename(lk_file)
            print(f"LG 엘에스 파일 처리 중... ({file_name})")
            lk_data = extract_data_from_lg_lk(lk_file, date_str, "LG", "엘에스")
            all_data.extend(lk_data)
            print(f"  → {len(lk_data)}개 기기 추출")
    
    # LG 비케이2 파일 처리 - calculated 파일만 사용
    bk2_files = []
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "LG" in normalized_file and "비케이2" in normalized_file and file.endswith("_calculated.xlsx"):
            bk2_files.append(os.path.join(base_path, file))
    
    # 모든 비케이2 파일 처리
    for idx, bk2_file in enumerate(bk2_files):
        if os.path.exists(bk2_file):
            file_name = os.path.basename(bk2_file)
            print(f"LG 비케이2 파일 처리 중... ({file_name})")
            bk2_data = extract_data_from_lg_bk(bk2_file, date_str, "LG", "비케이2")
            all_data.extend(bk2_data)
            print(f"  → {len(bk2_data)}개 기기 추출")
    
    # LG 번개폰 파일 처리 - calculated 파일만 사용
    bungyae_file = None
    for file in os.listdir(base_path):
        normalized_file = unicodedata.normalize('NFC', file)
        if "LG" in normalized_file and "번개폰" in normalized_file and file.endswith("_calculated.xlsx"):
            bungyae_file = os.path.join(base_path, file)
            break
    if bungyae_file and os.path.exists(bungyae_file):
        print(f"LG 번개폰 파일 처리 중: {os.path.basename(bungyae_file)}")
        bungyae_data = extract_data_from_번개폰(bungyae_file, date_str, "LG", "번개폰")
        all_data.extend(bungyae_data)
        print(f"  → {len(bungyae_data)}개 기기 추출")

    # 애플 사전예약 데이터 추가
    try:
        from data_merge.apple_preorder_merge import process_apple_preorder_data
        apple_df = process_apple_preorder_data('LG')
        if apple_df is not None and not apple_df.empty:
            # DataFrame을 딕셔너리 리스트로 변환
            apple_data = apple_df.to_dict('records')
            all_data.extend(apple_data)
            print(f"  → LG 애플사전예약: {len(apple_data)}개 기기 추출")
    except Exception as e:
        print(f"애플 사전예약 데이터 처리 중 오류: {e}")
    
    # DataFrame으로 변환
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 모든 가능한 컬럼 정의
        base_columns = ['date', 'carrier', 'dealer', 'device_name']
        plan_types = ['115k', '105k', '95k', '61k']
        join_types = ['번호이동', '기기변경']
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
        
        # 빈 값을 'Null'로 채우기
        df = df.fillna('Null')
        
        # PathManager를 사용한 출력 경로 설정
        from shared_config.config.paths import PathManager
        pm = PathManager()
        archive_path, latest_path = pm.get_merged_output_path('lg', is_rebated=False, with_colors=False)

        # 결과 저장
        output_file = archive_path
        df.to_excel(str(output_file), index=False)

        # latest 파일로 복사
        pm.save_with_archive(archive_path, archive_path, latest_path)

        print(f"\n병합 완료!")
        print(f"총 {len(df)}개 기기")
        print(f"📁 Archive: {archive_path}")
        print(f"📁 Latest: {latest_path}")
        
        # 샘플 데이터 출력
        print("\n샘플 데이터 (처음 5행):")
        sample_cols = ['date', 'carrier', 'dealer', 'device_name', 
                      '번호이동_공시_115k', '기기변경_공시_115k']
        print(df[sample_cols].head())
        
        # 데이터 검증
        print("\n데이터 검증:")
        print(f"LG 비케이 기기 수: {len(df[df['dealer'] == '비케이'])}")
        print(f"LG 비케이2 기기 수: {len(df[df['dealer'] == '비케이2'])}")
        print(f"LG 엘에스 기기 수: {len(df[df['dealer'] == '엘에스'])}")
        print(f"LG 애플사전예약 기기 수: {len(df[df['dealer'] == '애플사전예약'])}")
        
        # 공시지원금 데이터 확인
        print(f"\n공시지원금 데이터 확인:")
        for col in df.columns:
            if '공시' in col and col not in base_columns:
                non_null_count = (df[col] != 'Null').sum()
                if non_null_count > 0:
                    print(f"  {col}: {non_null_count}개")
        
        # 선약 데이터 확인 (비케이, 엘에스는 선약 데이터 있음)
        print(f"\n선약 데이터 확인 (비케이, 엘에스만 해당):")
        for col in df.columns:
            if '선약' in col:
                non_null_count = (df[col] != 'Null').sum()
                if non_null_count > 0:
                    print(f"  {col}: {non_null_count}개")
        
        # 요금제별 데이터 확인
        print(f"\n요금제별 데이터 확인:")
        print(f"  61k 데이터: {(df['번호이동_공시_61k'] != 'Null').sum()}개 (비케이만)")
        
        return df
    else:
        print("추출된 데이터가 없습니다.")
        return None

if __name__ == "__main__":
    df = merge_lg_files()