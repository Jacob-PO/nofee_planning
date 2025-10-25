"""
Clean Architecture Summary Creator
간단하고 명확한 Summary 생성기
"""
import pandas as pd
import os
import glob
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from data_merge.rebate_calculator import RebateCalculator


class CleanSummaryCreator:
    """통신사 요금제 Summary 생성기
    
    Google Sheets의 support, price, product_group_nm 데이터를 결합하여
    최종 요금 계산 결과를 생성하는 클린 아키텍처 기반 시스템
    """
    
    # 상수 정의
    SPREADSHEET_ID = "1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4"
    CREDENTIALS_DIR = "/Users/jacob_athometrip/Desktop/dev/nofee/nofee-workspace/config"
    # ARCHIVE_BASE_DIR는 PathManager에서 관리하므로 제거됨
    
    # 통신사 상수
    CARRIERS = {
        'SK': 'SK',
        'KT': 'KT', 
        'LG': 'LG'
    }
    
    # 개통 방식
    JOIN_TYPES = {
        'NEW': '신규가입',
        'MNP': '번호이동',
        'CHANGE': '기기변경'
    }
    
    # 지원 방식
    SUPPORT_TYPES = {
        'ANNOUNCE': '공시',
        'CHOICE': '선약'
    }
    
    # 요금제 정책 설정
    RATE_PLAN_CONFIG = {
        'MIN_PLAN_FEE': {  # 통신사별 최소 요금제 (원)
            'SK': 43_000,
            'KT': 49_000,
            'LG': 47_000
        },
        'MANDATORY_DAYS': {  # 의무사용기간 (일)
            'SK': {'공시': 188, '선약': 130},
            'KT': {'공시': 188, '선약': 130},
            'LG': {'공시': 188, '선약': 95}
        },
        'STANDARD_PLAN_FEE': 12_100,  # 표준 요금제 (원)
        'CONTRACT_MONTHS': 24,  # 약정 개월
        'CONTRACT_DAYS': 730,  # 24개월 = 730일
        'CHOICE_DISCOUNT_RATE': 0.75  # 선약 할인율 (25% 할인)
    }
    
    # 마진 정책
    MARGIN_CONFIG = {
        'DEFAULT_RATE': 0.40,  # 기본 마진율 40%
        'MIN_AMOUNT': 400_000,   # 최소 마진액 40만원 (원)
    }
    
    # Google Sheets API 설정
    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Summary 시트 헤더 정의
    SUMMARY_HEADERS = {
        'korean': [
            '날짜', '통신사', '제조사', '기기명', '상품 그룹명', '저장 용량', '대리점명', 
            '개통방식', '할인방식', '요금제명', '월 요금 납부액', '출고가', '총 공시지원금', 
            '대리점 리베이트', '원가 할부원금', '원가 할부원금 할부금', '원가 월 납부액', 
            '월 요금제 납부금', '할부원금', '할부원금 할부금', '월 납부액', '마진', '마진액'
        ],
        'english': [
            'date', 'carrier', 'manufacturer', 'device_nm', 'product_group_nm', 'storage', 'dealer',
            'join_type', 'support_type', 'rate_plan', 'rate_plan_month_fee', 'retail_price',
            'total_support_fee', 'dealer_subsidy', 'origin_installment_principal',
            'origin_month_device_price', 'origin_month_price', 'month_rate_plan_price',
            'installment_principal', 'month_device_price', 'month_price', 'margin', 'margin_amount'
        ]
    }
    
    def __init__(self, use_rebate_calculator=True):
        """초기화 메서드

        Args:
            use_rebate_calculator: RebateCalculator 사용 여부 (기본값: True)
        """
        self.setup_google_sheets()
        self._initialize_data_frames()

        # RebateCalculator 초기화
        self.use_rebate_calculator = use_rebate_calculator
        if self.use_rebate_calculator:
            try:
                self.rebate_calculator = RebateCalculator()
                print("✅ RebateCalculator 초기화 완료")
                print(self.rebate_calculator.get_rebate_summary())
            except Exception as e:
                print(f"⚠️ RebateCalculator 초기화 실패: {e}")
                self.use_rebate_calculator = False
                self.rebate_calculator = None
        else:
            self.rebate_calculator = None

        # 리베이트 적용 통계
        self.rebate_stats = {
            'total_applied': 0,
            'total_rebate_amount': 0,
            'by_dealer': {},
            'by_description': {},
            'high_rebate_items': []  # 20만원 이상 리베이트 항목
        }
        
    def _initialize_data_frames(self):
        """데이터프레임 초기화"""
        self.support_df = None
        self.price_df = None
        self.product_group_df = None
        
    def setup_google_sheets(self):
        """Google Sheets API 설정"""
        credentials_file = self._find_credentials_file()
        self._authenticate_google_sheets(credentials_file)
        
    def _find_credentials_file(self):
        """Google API 인증 파일 찾기"""
        # google_api_key.json 파일을 우선적으로 찾기
        google_api_key = os.path.join(self.CREDENTIALS_DIR, "google_api_key.json")
        if os.path.exists(google_api_key):
            print(f"사용할 credentials 파일: {google_api_key}")
            return google_api_key

        # 없으면 다른 json 파일들 중 service account 파일 찾기
        json_files = glob.glob(os.path.join(self.CREDENTIALS_DIR, "*.json"))
        for json_file in json_files:
            if 'google' in json_file.lower() or 'service' in json_file.lower():
                print(f"사용할 credentials 파일: {json_file}")
                return json_file

        if not json_files:
            raise FileNotFoundError("Google Sheets API 키 파일을 찾을 수 없습니다.")

        credentials_file = json_files[0]
        print(f"사용할 credentials 파일: {credentials_file}")
        return credentials_file
        
    def _authenticate_google_sheets(self, credentials_file):
        """Google Sheets 인증 및 클라이언트 설정"""
        # gspread 인증
        creds = Credentials.from_service_account_file(credentials_file, scopes=self.SCOPES)
        self.gc = gspread.authorize(creds)
        
        # Google Sheets API 인증
        api_credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=api_credentials)
        self.sheet = self.gc.open_by_key(self.SPREADSHEET_ID)

    def download_data(self):
        """모든 필요한 데이터 다운로드"""
        print("데이터 다운로드 중...")
        
        self._download_support_data()
        self._download_price_data()
        self._download_product_group_data()
        
    def _download_support_data(self):
        """Support 시트 데이터 다운로드"""
        support_worksheet = self.sheet.worksheet("support")
        # get_all_records() 대신 get_all_values() 사용
        all_values = support_worksheet.get_all_values()
        if len(all_values) > 1:
            headers = all_values[0]
            data = all_values[1:]
            support_data = [dict(zip(headers, row)) for row in data]
            self.support_df = pd.DataFrame(support_data)
        else:
            self.support_df = pd.DataFrame()
        print(f"Support: {len(self.support_df)}개 행")
        
    def _download_price_data(self):
        """Price 시트 데이터 다운로드 (3개 통신사)"""
        price_data = []
        
        for carrier in ['kt', 'lg', 'sk']:
            worksheet = self.sheet.worksheet(f"{carrier}_price")
            data = worksheet.get_all_records()
            
            # 통신사 정보 추가
            for row in data:
                row['carrier'] = carrier.upper()
            price_data.extend(data)
        
        self.price_df = pd.DataFrame(price_data)
        print(f"Price: {len(self.price_df)}개 행")
        
    def _download_product_group_data(self):
        """Product Group 매핑 데이터 다운로드"""
        pg_worksheet = self.sheet.worksheet("product_group_nm")
        pg_data = pg_worksheet.get_all_records()
        self.product_group_df = pd.DataFrame(pg_data)
        print(f"Product_group_nm: {len(self.product_group_df)}개 행")

    def clean_numeric(self, value):
        """숫자 값 정리 (정확한 값만 반환)"""
        if pd.isna(value) or value == '' or value is None:
            return None
        
        try:
            # 문자열인 경우 쉼표 제거 후 숫자 변환
            if isinstance(value, str):
                cleaned = value.replace(',', '').replace('원', '').strip()
                if cleaned:
                    return float(cleaned)
                else:
                    return None
            return float(value)
        except:
            return None

    def get_rate_plan_amount(self, col_name):
        """컬럼명에서 요금제 금액 추출 (69k -> 69000, 79k -> 89000)"""
        parts = col_name.split('_')
        if len(parts) != 3:
            return None

        rate_plan_k = parts[2]  # 110k, 100k, 90k 등

        if rate_plan_k.endswith('k'):
            try:
                # 특별 매핑 케이스들
                if rate_plan_k == '79k':
                    return 89000
                elif rate_plan_k == '50k':
                    return 59000
                elif rate_plan_k == '33k':
                    return 33000
                elif rate_plan_k == '37k':
                    return 37000
                return int(rate_plan_k[:-1]) * 1000
            except:
                return None
        return None

    def build_support_mapping(self):
        """Support 데이터를 product_group_nm별로 매핑"""
        # Product_group_nm에서 device_nm + storage 조합으로 매핑 생성
        device_storage_to_product = {}
        for _, row in self.product_group_df.iterrows():
            device_nm = str(row.get('device_nm', ''))
            product_group_nm = str(row.get('product_group_nm', ''))
            storage = str(row.get('storage', ''))
            # device_nm + storage를 키로 사용
            key = (device_nm, storage)
            device_storage_to_product[key] = product_group_nm
        
        # Support 데이터를 product_group_nm별로 그룹화
        support_by_product_group = {}
        for _, support_row in self.support_df.iterrows():
            support_device_nm = support_row.get('device_nm', '')
            carrier = support_row.get('carrier', '')
            support_storage = str(support_row.get('storage', ''))
            
            # device_nm + storage 조합으로 product_group_nm 찾기
            lookup_key = (support_device_nm, support_storage)
            if lookup_key in device_storage_to_product:
                matched_product_group = device_storage_to_product[lookup_key]
                
                # Support 데이터를 복사하고 매핑된 storage 추가
                support_row_copy = support_row.copy()
                support_row_copy['mapped_storage'] = support_storage
                support_row_copy['mapped_product_group_nm'] = matched_product_group
                
                key = (carrier, matched_product_group)
                if key not in support_by_product_group:
                    support_by_product_group[key] = []
                support_by_product_group[key].append(support_row_copy)
        
        return support_by_product_group

    def find_exact_support_match(self, carrier, product_group_nm, rate_plan_amount, support_by_product_group, storage, join_type):
        """정확한 Support 매칭 찾기 (요금제 금액, storage, 가입유형이 정확히 일치하는 것만)"""
        # 1단계: carrier와 product_group_nm으로 Support 데이터 찾기
        key = (carrier, product_group_nm)
        matching_supports = support_by_product_group.get(key, [])
        
        if not matching_supports:
            return None
            
        # 2단계: storage, 요금제 금액, 가입유형 정확 매칭
        exact_matches = []
        for support_row in matching_supports:
            support_rate_fee = self.clean_numeric(support_row.get('rate_plan_month_fee'))
            # product_group_nm 매핑을 통해 가져온 storage 사용
            support_storage = support_row.get('mapped_storage', support_row.get('storage', ''))
            
            # scrb_type_name에서 가입유형 확인
            support_scrb_type = support_row.get('scrb_type_name', '')
            
            # 가입유형 매칭 확인
            join_type_match = False
            if join_type == '신규가입' and support_scrb_type == '신규가입':
                join_type_match = True
            elif join_type == '번호이동' and support_scrb_type == '번호이동':
                join_type_match = True
            elif join_type == '기기변경' and support_scrb_type == '기기변경':
                join_type_match = True
            
            # storage, 요금제 금액, 가입유형이 모두 일치하는 경우만
            if (support_rate_fee is not None and support_rate_fee == rate_plan_amount and
                support_storage == storage and join_type_match):
                exact_matches.append(support_row)
        
        if not exact_matches:
            return None
            
        # 3단계: 총지원금이 가장 높은 것 선택 (공시/선약 구분 없이)
        best_match = max(exact_matches, key=lambda x: self.clean_numeric(x.get('total_support_fee', 0)))
        return best_match

    def get_storage_from_product_group(self, device_nm):
        """Product_group_nm에서 storage 정보 가져오기 (정확한 매칭만)"""
        matches = self.product_group_df[self.product_group_df['device_nm'] == device_nm]
        if len(matches) > 0:
            storage = matches.iloc[0].get('storage', '')
            if storage and storage.strip():  # 빈 값이 아닌 경우만
                return storage
        return None  # 매칭되지 않으면 None 반환

    def get_product_group_mapping(self, device_nm):
        """device_nm을 product_group_nm으로 매핑 (정확한 매칭만)"""
        matches = self.product_group_df[self.product_group_df['device_nm'] == device_nm]
        if len(matches) > 0:
            product_group_nm = matches.iloc[0].get('product_group_nm', '')
            if product_group_nm and product_group_nm.strip():  # 빈 값이 아닌 경우만
                return product_group_nm
        return None  # 매칭되지 않으면 None 반환

    def format_date(self, date_str):
        """날짜를 yyyy. m. dd 형식으로 변환 (월은 0 제거, 일은 2자리 유지)"""
        if not date_str:
            return ''
        
        try:
            if len(str(date_str)) == 8 and str(date_str).isdigit():
                date_str = str(date_str)
                year = date_str[:4]
                month = str(int(date_str[4:6]))  # 앞의 0 제거
                day = date_str[6:8]              # 일자는 2자리 유지
                return f"{year}. {month}. {day}"
            return str(date_str)
        except:
            return str(date_str)
    
    def calculate_month_rate_plan_price(self, carrier, support_type, original_fee):
        """월 요금제 납부금 계산 (의무사용기간과 표준요금제 고려)
        
        Args:
            carrier: 통신사 (SK, KT, LG)
            support_type: 지원 유형 (공시, 선약)
            original_fee: 원래 요금제 금액
            
        Returns:
            24개월 가중평균 월 요금
        """
        if carrier not in self.RATE_PLAN_CONFIG['MANDATORY_DAYS']:
            return None
            
        # 설정값 가져오기
        mandatory_days = self.RATE_PLAN_CONFIG['MANDATORY_DAYS'][carrier][support_type]
        min_plan_fee = self.RATE_PLAN_CONFIG['MIN_PLAN_FEE'][carrier]
        total_days = self.RATE_PLAN_CONFIG['CONTRACT_DAYS']
        standard_plan = self.RATE_PLAN_CONFIG['STANDARD_PLAN_FEE']
        choice_discount = self.RATE_PLAN_CONFIG['CHOICE_DISCOUNT_RATE']
        
        if original_fee < min_plan_fee:
            # Case 1: 개통요금제가 최소요금제보다 적은 경우
            if support_type == '선약':
                # 선약: 의무사용기간과 남은기간 모두 25% 할인 적용
                mandatory_fee = original_fee * choice_discount
                remaining_fee = standard_plan * choice_discount
            else:
                # 공시: 할인 없음
                mandatory_fee = original_fee
                remaining_fee = standard_plan
                
            remaining_days = total_days - mandatory_days
            weighted_avg = (mandatory_fee * mandatory_days + remaining_fee * remaining_days) / total_days
            
        else:
            # Case 2: 개통요금제가 최소요금제 이상인 경우
            if support_type == '선약':
                # 선약: 의무사용기간은 25% 할인, 남은 기간은 최소요금제의 25% 할인
                mandatory_fee = original_fee * choice_discount
                remaining_fee = min_plan_fee * choice_discount
                remaining_days = total_days - mandatory_days
                weighted_avg = (mandatory_fee * mandatory_days + remaining_fee * remaining_days) / total_days
            else:
                # 공시: 의무사용기간은 원래 요금, 남은 기간은 최소요금제
                mandatory_fee = original_fee
                remaining_fee = min_plan_fee
                remaining_days = total_days - mandatory_days
                weighted_avg = (mandatory_fee * mandatory_days + remaining_fee * remaining_days) / total_days
        
        return round(weighted_avg)
    
    def calculate_margin(self, origin_installment_principal):
        """마진율 계산 (최소 마진액 보장, 최대 마진액 제한)

        Args:
            origin_installment_principal: 원가 할부원금

        Returns:
            최종 마진율 (최소 10만원, 최대 15만원)
        """
        if origin_installment_principal is None or origin_installment_principal == 0:
            return self.MARGIN_CONFIG['DEFAULT_RATE']
            
        # 기본 마진율로 계산한 마진액
        basic_margin_amount = abs(origin_installment_principal) * self.MARGIN_CONFIG['DEFAULT_RATE']
        
        # 최소 마진액 체크
        if basic_margin_amount < self.MARGIN_CONFIG['MIN_AMOUNT']:
            return round(self.MARGIN_CONFIG['MIN_AMOUNT'] / abs(origin_installment_principal), 3)
        else:
            return self.MARGIN_CONFIG['DEFAULT_RATE']

    def create_summary_row(self, price_row, support_row, col_name, dealer_subsidy, storage):
        """Summary 행 생성"""
        # 기본 정보
        parts = col_name.split('_')
        join_type = parts[0]  # 신규가입/번호이동/기기변경
        support_type = parts[1]  # 공시/선약

        # RebateCalculator 적용 (활성화된 경우)
        if self.use_rebate_calculator and self.rebate_calculator:
            carrier = price_row.get('carrier', '')
            dealer = price_row.get('dealer', '')
            device_nm = price_row.get('device_nm', '')

            # product_group_nm 가져오기
            product_group_nm = self.get_product_group_mapping(device_nm)

            # 요금제 정보 (k 단위로 변환)
            rate_plan_fee = self.clean_numeric(support_row.get('rate_plan_month_fee'))
            if rate_plan_fee:
                rate_plan_k = int(rate_plan_fee / 1000)  # 109000 -> 109
            else:
                rate_plan_k = 0

            # 대리점명 생성 (통신사_대리점)
            full_dealer_name = f"{carrier}_{dealer}"

            # RebateCalculator를 사용하여 추가 리베이트 계산
            new_dealer_subsidy, rebate_description = self.rebate_calculator.apply_dealer_rebate(
                dealer_name=full_dealer_name,
                model_name=device_nm,
                rate_plan=rate_plan_k,
                original_value=dealer_subsidy,
                support_type=support_type,
                join_type=join_type,
                product_group_nm=product_group_nm
            )

            # 추가 리베이트가 적용된 경우 통계 업데이트
            additional_rebate = new_dealer_subsidy - dealer_subsidy
            if additional_rebate != 0:
                self.rebate_stats['total_applied'] += 1
                self.rebate_stats['total_rebate_amount'] += additional_rebate

                # 대리점별 통계
                if full_dealer_name not in self.rebate_stats['by_dealer']:
                    self.rebate_stats['by_dealer'][full_dealer_name] = {
                        'count': 0,
                        'total_rebate': 0
                    }
                self.rebate_stats['by_dealer'][full_dealer_name]['count'] += 1
                self.rebate_stats['by_dealer'][full_dealer_name]['total_rebate'] += additional_rebate

                # 설명별 통계
                if rebate_description:
                    if rebate_description not in self.rebate_stats['by_description']:
                        self.rebate_stats['by_description'][rebate_description] = {
                            'count': 0,
                            'total_rebate': 0
                        }
                    self.rebate_stats['by_description'][rebate_description]['count'] += 1
                    self.rebate_stats['by_description'][rebate_description]['total_rebate'] += additional_rebate

                # 20만원 이상 리베이트 항목 저장
                if additional_rebate >= 200000:
                    high_rebate_item = {
                        'dealer': full_dealer_name,
                        'device': device_nm,
                        'join_type': join_type,
                        'support_type': support_type,
                        'rate_plan': rate_plan_k,
                        'rebate_amount': additional_rebate,
                        'description': rebate_description,
                        'date': price_row.get('date', '')
                    }
                    self.rebate_stats['high_rebate_items'].append(high_rebate_item)

                # 디버그 출력 (5만원 이상 또는 -5만원 이하)
                if abs(additional_rebate) >= 50000:
                    print(f"   💡 리베이트 적용: {full_dealer_name} {device_nm[:20]} "
                          f"{join_type} {rate_plan_k}k -> +{additional_rebate:,}원 ({rebate_description})")

            # 적용된 dealer_subsidy 사용
            dealer_subsidy = new_dealer_subsidy
        
        # Support에서 가져올 정보 (컬럼명 수정)
        manufacturer = support_row.get('manufacturer', '')
        rate_plan = support_row.get('rate_plan', '')
        rate_plan_month_fee = self.clean_numeric(support_row.get('rate_plan_month_fee'))
        retail_price = self.clean_numeric(support_row.get('release_price'))  # release_price로 수정
        
        # 선택약정의 경우 총 공시지원금을 0원으로 설정
        if support_type == '선약':
            total_support_fee = 0
        else:
            total_support_fee = self.clean_numeric(support_row.get('total_support_fee'))
        
        # None 값 체크 - 필수 값이 None이면 계산 불가
        if rate_plan_month_fee is None or retail_price is None:
            return None
        
        # 계산
        origin_installment_principal = retail_price - (total_support_fee + dealer_subsidy)
        origin_month_device_price = origin_installment_principal / 24
        
        # 월 요금제 납부금 계산 (의무사용기간과 표준요금제 고려)
        carrier = price_row.get('carrier', '')
        month_rate_plan_price = self.calculate_month_rate_plan_price(carrier, support_type, rate_plan_month_fee)
        if month_rate_plan_price is None:
            return None
            
        origin_month_price = origin_month_device_price + month_rate_plan_price

        # 마진 계산 (최소 10만원 보장, 최대 15만원 제한)
        if origin_installment_principal == 0:
            # 원가 할부원금이 0원이면 기본 마진율 10% 사용
            margin = self.MARGIN_CONFIG['DEFAULT_RATE']
            margin_amount = 0  # 0원에서는 마진액도 0
        else:
            margin = self.calculate_margin(origin_installment_principal)
            margin_amount = abs(origin_installment_principal * margin)
            # 최소/최대 마진액 체크 (이미 calculate_margin에서 처리했지만 안전을 위해)
            margin_amount = max(self.MARGIN_CONFIG['MIN_AMOUNT'], margin_amount)
            margin = margin_amount / abs(origin_installment_principal)
        
        # 최종 가격들 (음수일 경우 0으로 조정 후 마진액 추가)
        installment_principal = max(0, origin_installment_principal) + margin_amount
        month_device_price = installment_principal / 24
        month_price = month_device_price + month_rate_plan_price
        
        # Summary 행 데이터 구조
        summary_data = {
            # 1. 기본 정보
            'date': self.format_date(price_row.get('date', '')),
            'carrier': price_row.get('carrier', ''),
            'manufacturer': manufacturer,
            'device_nm': price_row.get('device_nm', ''),
            'product_group_nm': self.get_product_group_mapping(price_row.get('device_nm', '')),
            'storage': storage,
            'dealer': price_row.get('dealer', ''),
            
            # 2. 개통 정보
            'join_type': join_type,
            'support_type': support_type,
            
            # 3. 요금제 정보
            'rate_plan': rate_plan,
            'rate_plan_month_fee': rate_plan_month_fee,
            
            # 4. 가격 정보
            'retail_price': retail_price,
            'total_support_fee': total_support_fee,
            'dealer_subsidy': dealer_subsidy,
            
            # 5. 원가 계산
            'origin_installment_principal': round(origin_installment_principal, 0),
            'origin_month_device_price': round(origin_month_device_price, 0),
            'origin_month_price': round(origin_month_price, 0),
            
            # 6. 최종 가격
            'month_rate_plan_price': round(month_rate_plan_price, 0),
            'installment_principal': round(installment_principal, 0),
            'month_device_price': round(month_device_price, 0),
            'month_price': round(month_price, 0),
            
            # 7. 마진 정보
            'margin': margin,
            'margin_amount': round(margin_amount, 0)
        }
        
        return summary_data

    def generate_summary(self):
        """Summary 생성"""
        print("Summary 생성 중...")
        
        # Support 매핑 구축
        support_by_product_group = self.build_support_mapping()
        print(f"Support 매핑 구축 완료: {len(support_by_product_group)}개 그룹")
        
        summary_rows = []
        unmapped_devices = set() # 매핑되지 않은 device_nm을 저장할 set
        
        # 매칭 실패 통계
        no_product_group_mapping = set()
        no_storage_info = set()
        no_support_match = {}
        device_to_product_group = {}  # device_nm -> product_group_nm 매핑 저장

        for _, price_row in self.price_df.iterrows():
            device_nm = price_row.get('device_nm', '')
            carrier = price_row.get('carrier', '')
            
            # Product_group_nm 매핑 (정확한 매칭만)
            product_group_nm = self.get_product_group_mapping(device_nm)
            if product_group_nm is None:
                no_product_group_mapping.add((carrier, device_nm))
                continue  # 매핑이 없으면 스킵
            
            device_to_product_group[device_nm] = product_group_nm
                
            storage = self.get_storage_from_product_group(device_nm)
            if storage is None:
                no_storage_info.add((carrier, device_nm))
                continue  # storage 정보가 없으면 스킵
            
            # 요금제 컬럼들 처리
            for col_name in self.price_df.columns:
                if '_' in col_name and col_name not in ['date', 'carrier', 'dealer', 'device_nm']:
                    
                    # 판매금액이 있는 경우만
                    raw_value = price_row[col_name]
                    if pd.isna(raw_value) or str(raw_value).strip() == '':
                        continue
                        
                    dealer_subsidy = self.clean_numeric(raw_value)
                    if dealer_subsidy is None or dealer_subsidy <= 0:
                        continue
                    
                    # 요금제 금액 추출
                    rate_plan_amount = self.get_rate_plan_amount(col_name)
                    if rate_plan_amount is None:
                        continue
                    
                    # 지원 유형 추출
                    parts = col_name.split('_')
                    if len(parts) >= 2:
                        join_type = parts[0]  # 신규가입/번호이동/기기변경
                        support_type = parts[1]  # 공시/선약
                    else:
                        continue
                    
                    # 신규가입 데이터 제외
                    if join_type == '신규가입':
                        continue
                    
                    # 정확한 Support 매칭 찾기
                    support_row = self.find_exact_support_match(carrier, product_group_nm, rate_plan_amount, support_by_product_group, storage, join_type)
                    if support_row is None:
                        key = (carrier, device_nm, support_type, rate_plan_amount)
                        if key not in no_support_match:
                            no_support_match[key] = 0
                        no_support_match[key] += 1
                        continue
                    
                    # Summary 행 생성
                    summary_row = self.create_summary_row(price_row, support_row, col_name, dealer_subsidy, storage)
                    if summary_row is not None:  # None이 아닌 경우만 추가
                        summary_rows.append(summary_row)
        
        # 매칭 실패 통계 출력
        print(f"\n=== 매칭 실패 통계 ===")
        print(f"\n1. product_group_nm 매핑 없음: {len(no_product_group_mapping)}개")
        if no_product_group_mapping:
            for carrier, device in sorted(no_product_group_mapping):
                print(f"   - {carrier}: {device}")
        
        print(f"\n2. storage 정보 없음: {len(no_storage_info)}개")
        if no_storage_info:
            for carrier, device in sorted(no_storage_info):
                print(f"   - {carrier}: {device}")
        
        print(f"\n3. Support 매칭 실패: {len(no_support_match)}개 조합")
        if no_support_match:
            sorted_items = sorted(no_support_match.items(), key=lambda x: x[1], reverse=True)
            print(f"   (상위 10개만 표시)")
            for (carrier, device, support_type, rate_plan), count in sorted_items[:10]:
                print(f"   - {carrier} {device} ({support_type}, {rate_plan//1000}k): {count}회")
            
            # 전체 리스트를 파일로 저장
            import csv
            unmatch_file = "unmatched_products.csv"
            with open(unmatch_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['통신사', '기기명', 'product_group_nm', '지원유형', '요금제', '횟수'])
                for (carrier, device, support_type, rate_plan), count in sorted_items:
                    product_group = device_to_product_group.get(device, '')
                    writer.writerow([carrier, device, product_group, support_type, f"{rate_plan//1000}k", count])
            print(f"\n   전체 리스트가 '{unmatch_file}'에 저장되었습니다.")
        
        return pd.DataFrame(summary_rows)

    def upload_to_sheets(self, summary_df):
        """Google Sheets에 업로드"""
        print(f"Google Sheets에 {len(summary_df)}개 행 업로드 중...")
        
        try:
            summary_worksheet = self.sheet.worksheet("summary")
        except:
            summary_worksheet = self.sheet.add_worksheet(title="summary", rows=10000, cols=25)
        
        # 기존 데이터 클리어
        summary_worksheet.clear()
        
        # 2행 헤더 준비 (한국어 + 영어)
        korean_headers = self.SUMMARY_HEADERS['korean']
        english_headers = self.SUMMARY_HEADERS['english']
        
        # 헤더와 데이터 준비 (2행 헤더 + 데이터)
        values = [korean_headers, english_headers] + summary_df.values.tolist()
        
        # 업로드
        summary_worksheet.update('A1', values)
        print("✅ Google Sheets 업로드 완료 (2행 헤더)")

    def save_archive(self, summary_df):
        """Summary 데이터 아카이브 저장

        Args:
            summary_df: 저장할 Summary DataFrame
        """
        from shared_config.config.paths import PathManager
        pm = PathManager()
        paths = pm.get_summary_output_path()

        # 파일 저장
        files_saved = []

        # Archive CSV 저장 (한글 인코딩)
        summary_df.to_csv(paths['archive_csv'], index=False, encoding='utf-8-sig')
        files_saved.append(paths['archive_csv'])

        # Archive Excel 저장
        with pd.ExcelWriter(paths['archive_excel'], engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        files_saved.append(paths['archive_excel'])

        # Latest CSV 저장
        summary_df.to_csv(paths['latest_csv'], index=False, encoding='utf-8-sig')
        files_saved.append(paths['latest_csv'])

        # Latest Excel 저장
        with pd.ExcelWriter(paths['latest_excel'], engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        files_saved.append(paths['latest_excel'])

        print(f"✅ 아카이브 저장 완료:")
        print(f"   📁 Archive CSV: {paths['archive_csv']}")
        print(f"   📁 Archive Excel: {paths['archive_excel']}")
        print(f"   📁 Latest CSV: {paths['latest_csv']}")
        print(f"   📁 Latest Excel: {paths['latest_excel']}")

    def print_rebate_stats(self):
        """리베이트 적용 통계 출력"""
        if not self.use_rebate_calculator or self.rebate_stats['total_applied'] == 0:
            return

        print("\n" + "="*60)
        print("📊 대리점 추가 리베이트 적용 통계")
        print("="*60)

        print(f"총 적용 건수: {self.rebate_stats['total_applied']:,}건")
        print(f"총 추가 리베이트: {self.rebate_stats['total_rebate_amount']:,}원")
        print(f"평균 추가 리베이트: {self.rebate_stats['total_rebate_amount'] / self.rebate_stats['total_applied']:,.0f}원")

        # 대리점별 통계
        if self.rebate_stats['by_dealer']:
            print("\n📍 대리점별 적용 현황:")
            sorted_dealers = sorted(
                self.rebate_stats['by_dealer'].items(),
                key=lambda x: x[1]['total_rebate'],
                reverse=True
            )
            for dealer, stats in sorted_dealers[:10]:
                avg_rebate = stats['total_rebate'] / stats['count']
                print(f"   {dealer}: {stats['count']}건, "
                      f"총 {stats['total_rebate']:,}원 "
                      f"(평균 {avg_rebate:,.0f}원)")

        # 정책별 통계
        if self.rebate_stats['by_description']:
            print("\n📋 정책별 적용 현황:")
            sorted_policies = sorted(
                self.rebate_stats['by_description'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            for policy, stats in sorted_policies[:10]:
                print(f"   {policy}: {stats['count']}건, "
                      f"총 {stats['total_rebate']:,}원")

        print("="*60)

    def print_high_rebate_report(self):
        """20만원 이상 고액 리베이트 리포트 출력"""
        if not self.use_rebate_calculator or not self.rebate_stats['high_rebate_items']:
            return

        print("\n" + "="*60)
        print("🔥 고액 리베이트 상품 리포트 (20만원 이상)")
        print("="*60)

        # 리베이트 금액 기준 정렬
        sorted_items = sorted(
            self.rebate_stats['high_rebate_items'],
            key=lambda x: x['rebate_amount'],
            reverse=True
        )

        print(f"\n총 {len(sorted_items)}개 상품 검출\n")

        # 테이블 헤더
        print(f"{'대리점':<15} {'기기명':<25} {'가입유형':<10} {'요금제':<8} {'리베이트':<12} {'정책'}")
        print("-" * 100)

        # 각 항목 출력
        for item in sorted_items:
            dealer = item['dealer']
            device = item['device'][:23] + ".." if len(item['device']) > 25 else item['device']
            join_type = item['join_type']
            rate_plan = f"{item['rate_plan']}k"
            rebate = f"+{item['rebate_amount']:,}원"
            description = item['description'][:30] + ".." if len(item['description']) > 30 else item['description']

            print(f"{dealer:<15} {device:<25} {join_type:<10} {rate_plan:<8} {rebate:<12} {description}")

        # 대리점별 집계
        dealer_summary = {}
        for item in sorted_items:
            dealer = item['dealer']
            if dealer not in dealer_summary:
                dealer_summary[dealer] = {'count': 0, 'total': 0}
            dealer_summary[dealer]['count'] += 1
            dealer_summary[dealer]['total'] += item['rebate_amount']

        print("\n" + "-" * 100)
        print("📌 대리점별 고액 리베이트 집계:")
        sorted_dealer_summary = sorted(
            dealer_summary.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )

        for dealer, stats in sorted_dealer_summary:
            avg = stats['total'] / stats['count']
            print(f"   {dealer}: {stats['count']}건, 총 {stats['total']:,}원 (평균 {avg:,.0f}원)")

        # 최고/최저 리베이트 항목
        if sorted_items:
            print("\n" + "-" * 100)
            highest = sorted_items[0]
            print(f"💰 최고 리베이트: {highest['dealer']} - {highest['device']} "
                  f"({highest['join_type']}, {highest['rate_plan']}k) = +{highest['rebate_amount']:,}원")

            if len(sorted_items) > 1:
                lowest = sorted_items[-1]
                print(f"💡 최저 리베이트: {lowest['dealer']} - {lowest['device']} "
                      f"({lowest['join_type']}, {lowest['rate_plan']}k) = +{lowest['rebate_amount']:,}원")

        print("\n⚠️  주의: 고액 리베이트 상품은 판매가 계산에 큰 영향을 미치므로 정확성 검증 필요")
        print("="*60)

    def check_high_dealer_subsidy(self, summary_df):
        """dealer_subsidy가 100만원 이상인 상품 확인 및 출력"""
        print("\n" + "=" * 80)
        print("⚠️  dealer_subsidy가 100만원 이상인 상품 확인")
        print("=" * 80)

        high_subsidy = summary_df[summary_df['dealer_subsidy'] >= 1000000].copy()

        if not high_subsidy.empty:
            high_subsidy_sorted = high_subsidy.sort_values('dealer_subsidy', ascending=False)
            print(f"\n🔍 총 {len(high_subsidy_sorted)}개 상품이 100만원 이상의 dealer_subsidy를 가지고 있습니다.\n")

            for idx, (_, row) in enumerate(high_subsidy_sorted.iterrows(), 1):
                print(f"{idx}. 📱 {row['device_nm']}")
                print(f"   통신사: {row['carrier']} | 대리점: {row['dealer']}")
                print(f"   상품군: {row.get('product_group_nm', 'N/A')} | 지원타입: {row['support_type']}")
                print(f"   가입유형: {row['join_type']} | 요금제: {row.get('rate_plan', 'N/A')}")
                print(f"   💰 dealer_subsidy: {row['dealer_subsidy']:,.0f}원")
                if 'official_subsidy' in row and pd.notna(row['official_subsidy']):
                    print(f"   공시지원금: {row['official_subsidy']:,.0f}원")
                if pd.notna(row.get('rebate_applied')) and row.get('rebate_applied') != '':
                    print(f"   리베이트: {row['rebate_applied']}")
                print()
        else:
            print("\n✅ 100만원 이상의 dealer_subsidy를 가진 상품이 없습니다.")

        print("=" * 80)

    def run(self):
        """전체 프로세스 실행"""
        print("=" * 60)
        print("Clean Summary Creator 시작")
        if self.use_rebate_calculator:
            print("   (RebateCalculator 활성화)")
        print("=" * 60)

        # 1. 데이터 다운로드
        self.download_data()

        # 2. Summary 생성
        summary_df = self.generate_summary()
        print(f"생성된 Summary 행 수: {len(summary_df)}")

        if len(summary_df) == 0:
            print("❌ 생성된 Summary가 없습니다.")
            return

        # 3. 아카이브 저장
        self.save_archive(summary_df)

        # 4. dealer_subsidy가 100만원 이상인 상품 확인
        self.check_high_dealer_subsidy(summary_df)

        # 5. Google Sheets 업로드
        self.upload_to_sheets(summary_df)

        # 5. 리베이트 통계 출력 (활성화된 경우)
        self.print_rebate_stats()

        # 6. 고액 리베이트 리포트 출력 (활성화된 경우)
        self.print_high_rebate_report()

        print("=" * 60)
        print("✅ Clean Summary Creator 완료")
        print("=" * 60)


if __name__ == "__main__":
    creator = CleanSummaryCreator()
    creator.run()