"""
데이터 병합 및 구글 스프레드시트 업로드 모듈

이 모듈은 다음 기능을 제공합니다:
1. crawlers/data/raw/ 폴더의 모든 CSV 파일 읽기 (kt_*, lg_*, sk_*)
2. 데이터를 하나로 병합
3. 필요한 컬럼 추가: storage, support_type
4. Google Sheets API를 사용해 업로드

Author: Claude Code
Created: 2025-07-08
"""

import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from glob import glob


class DataMerger:
    def __init__(self, raw_data_dir="./data/raw", credentials_dir="../"):
        """
        데이터 병합 클래스 초기화
        
        Args:
            raw_data_dir (str): 원본 데이터 디렉토리 경로
            credentials_dir (str): 서비스 계정 키 파일 디렉토리 경로
        """
        self.raw_data_dir = raw_data_dir
        self.credentials_dir = credentials_dir
        
        # 결과 저장 디렉토리 설정
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        print(f"Results will be saved to: {self.results_dir}")
        
    def extract_storage(self, device_name):
        """
        기기명에서 저장용량 추출 - 개선된 버전
        
        Args:
            device_name (str): 기기명
            
        Returns:
            str: 저장용량 (8GB, 16GB, 32GB, 64GB, 128GB, 256GB, 512GB, 1TB, N/A, Unknown)
        """
        if pd.isna(device_name) or device_name == 'Null':
            return 'Unknown'
        
        device_name = str(device_name)
        
        # 1. 명시적 저장용량 패턴 매칭
        storage_patterns = [
            (r'(1024|1000)\s*GB', '1TB'),  # 1024GB, 1000GB
            (r'1\s*TB', '1TB'),
            (r'1T(?![A-Za-z])', '1TB'),   # 1T (단, 뒤에 문자가 오지 않는 경우)
            (r'512\s*GB?', '512GB'),
            (r'256\s*GB?', '256GB'), 
            (r'128\s*GB?', '128GB'),
            (r'64\s*GB?', '64GB'),
            (r'32\s*GB?', '32GB'),
            (r'16\s*GB?', '16GB'),
            (r'8\s*GB?', '8GB'),
        ]
        
        for pattern, storage in storage_patterns:
            if re.search(pattern, device_name, re.IGNORECASE):
                return storage
        
        # 2. 기기 타입별 기본 저장용량 추정
        device_lower = device_name.lower()
        
        # Apple Watch, 갤럭시 워치 등은 스토리지 개념이 다름
        if any(keyword in device_lower for keyword in ['watch', '워치', '밴드']):
            return 'N/A'
        
        # 키즈폰, 폴더폰 등 기본 저장용량
        if any(keyword in device_lower for keyword in ['키즈폰', '폴더', 'folder']):
            return '8GB'
        
        # 태블릿은 보통 더 큰 용량
        if any(keyword in device_lower for keyword in ['탭', 'tab', 'ipad', '북']):
            return '128GB'
        
        # 중고폰은 모델명에서 추출 시도
        if '중고폰' in device_name:
            # RU-SM-S918N5 같은 패턴에서 원래 모델명 추출 시도
            model_match = re.search(r'S\d{2,3}|A\d{2,3}|Note\s*\d{1,2}', device_name)
            if model_match:
                model = model_match.group()
                # 상위 모델은 기본적으로 더 큰 용량
                if any(m in model for m in ['S9', 'S2', 'Note']):
                    return '256GB'
                else:
                    return '128GB'
        
        # 아이폰 기본 용량 (최신 모델)
        if 'iphone' in device_lower:
            if any(model in device_lower for model in ['16', '15', '14']):
                return '128GB'  # 최신 아이폰 기본 용량
            else:
                return '64GB'   # 구형 아이폰
        
        # 갤럭시 시리즈 기본 용량
        if '갤럭시' in device_name:
            if any(model in device_lower for model in ['s25', 's24', 's23', 'z flip', 'z fold']):
                return '256GB'  # 플래그십 기본 용량
            elif any(model in device_lower for model in ['a36', 'a35', 'a25', 'a16']):
                return '128GB'  # A 시리즈 기본 용량  
            elif 'buddy' in device_lower:
                return '32GB'   # 버디 시리즈
            else:
                return '128GB'  # 기타 갤럭시
        
        # 샤오미
        if any(keyword in device_lower for keyword in ['샤오미', 'xiaomi', 'redmi']):
            if 'note' in device_lower:
                return '128GB'  # 노트 시리즈 기본
            else:
                return '64GB'   # 기타 샤오미
        
        return 'Unknown'
    
    def extract_support_type(self, scrb_type_name):
        """
        가입유형에서 지원 타입 추출
        
        Args:
            scrb_type_name (str): 가입유형
            
        Returns:
            str: 지원 타입 (신규, 기변, 번이, Unknown)
        """
        if pd.isna(scrb_type_name) or scrb_type_name == 'Null':
            return 'Unknown'
        
        scrb_type_name = str(scrb_type_name)
        
        if '신규' in scrb_type_name:
            return '신규'
        elif '기기변경' in scrb_type_name:
            return '기변'
        elif '번호이동' in scrb_type_name:
            return '번이'
        else:
            return 'Unknown'
    
    def read_csv_files(self):
        """
        raw 디렉토리의 최신 CSV 파일들을 읽어서 병합
        각 통신사별로 가장 최신 파일만 선택
        
        Returns:
            pd.DataFrame: 병합된 데이터프레임
        """
        csv_files = glob(os.path.join(self.raw_data_dir, "*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.raw_data_dir}")
        
        # 통신사별로 파일 분류
        carrier_files = {'kt': [], 'lg': [], 'sk': []}
        
        for file in csv_files:
            basename = os.path.basename(file)
            if basename.startswith('kt_'):
                carrier_files['kt'].append(file)
            elif basename.startswith('lg_'):
                carrier_files['lg'].append(file)
            elif basename.startswith('sk_'):
                carrier_files['sk'].append(file)
        
        # 각 통신사별로 파일 선택
        latest_files = []
        for carrier, files in carrier_files.items():
            if files:
                # 파일명의 타임스탬프를 기준으로 정렬 (최신 파일이 마지막)
                files.sort()
                
                if carrier == 'kt':
                    # KT의 경우 동일 날짜의 모든 파일 사용 (가입유형별로 분리되어 있을 수 있음)
                    if files:
                        # 가장 최신 파일의 날짜 추출
                        latest_file = files[-1]
                        basename = os.path.basename(latest_file)
                        # kt_20250813_121050.csv 에서 20250813 추출
                        date_match = re.search(r'kt_(\d{8})_', basename)
                        if date_match:
                            latest_date = date_match.group(1)
                            # 같은 날짜의 모든 파일 추가
                            for f in files:
                                if f'kt_{latest_date}_' in f:
                                    latest_files.append(f)
                                    print(f"KT file: {os.path.basename(f)}")
                        else:
                            latest_files.append(latest_file)
                            print(f"Latest {carrier.upper()} file: {os.path.basename(latest_file)}")
                else:
                    # LG, SK는 기존대로 최신 파일만
                    latest_file = files[-1]
                    latest_files.append(latest_file)
                    print(f"Latest {carrier.upper()} file: {os.path.basename(latest_file)}")
        
        if not latest_files:
            raise ValueError("No carrier CSV files found (kt_*, lg_*, sk_*)")
        
        print(f"\nUsing {len(latest_files)} latest files:")
        
        dataframes = []
        
        for file in latest_files:
            try:
                df = pd.read_csv(file)
                
                # BOM 제거 (첫 번째 컬럼명에 BOM이 있을 수 있음)
                if df.columns[0].startswith('\ufeff'):
                    df.columns = [df.columns[0].replace('\ufeff', '')] + df.columns[1:].tolist()
                
                print(f"  - {os.path.basename(file)}: {len(df)} rows")
                dataframes.append(df)
            except Exception as e:
                print(f"  - Error reading {file}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("No valid CSV files to merge")
        
        # 모든 데이터프레임 병합
        merged_df = pd.concat(dataframes, ignore_index=True)
        print(f"\nTotal merged rows: {len(merged_df)}")
        
        return merged_df
    
    def add_additional_columns(self, df):
        """
        추가 컬럼들을 생성하여 데이터프레임에 추가
        
        Args:
            df (pd.DataFrame): 원본 데이터프레임
            
        Returns:
            pd.DataFrame: 추가 컬럼이 포함된 데이터프레임
        """
        print("Adding additional columns...")
        
        # device_name 컬럼명을 device_nm으로 변경 (추가 컬럼 생성 전에)
        if 'device_name' in df.columns:
            df = df.rename(columns={'device_name': 'device_nm'})
            print("Renamed column: device_name -> device_nm")
        
        # 저장용량 추가
        df['storage'] = df['device_nm'].apply(self.extract_storage)
        
        # 지원 타입 추가
        df['support_type'] = df['scrb_type_name'].apply(self.extract_support_type)
        
        print(f"Added columns: storage, support_type")
        return df
    
    def merge_data(self):
        """
        데이터 병합 및 추가 컬럼 생성
        
        Returns:
            pd.DataFrame: 병합 및 가공된 데이터프레임
        """
        print("Starting data merge process...")
        
        # CSV 파일들 읽기
        merged_df = self.read_csv_files()
        
        # 추가 컬럼 생성
        merged_df = self.add_additional_columns(merged_df)
        
        # monthly_fee 컬럼명을 rate_plan_month_fee로 변경
        if 'monthly_fee' in merged_df.columns:
            merged_df = merged_df.rename(columns={'monthly_fee': 'rate_plan_month_fee'})
            print("Renamed column: monthly_fee -> rate_plan_month_fee")
        
        # plan_name 컬럼명을 rate_plan으로 변경
        if 'plan_name' in merged_df.columns:
            merged_df = merged_df.rename(columns={'plan_name': 'rate_plan'})
            print("Renamed column: plan_name -> rate_plan")
        
        # NaN 값을 'Null'로 변경
        merged_df = merged_df.fillna('Null')
        
        print(f"Data merge completed. Final shape: {merged_df.shape}")
        
        # 병합된 데이터를 로컬에 저장
        self.save_merged_data(merged_df)
        
        return merged_df
    
    def save_merged_data(self, df):
        """
        병합된 데이터를 로컬에 저장
        
        Args:
            df (pd.DataFrame): 저장할 데이터프레임
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV 저장
        csv_file = self.results_dir / f"merged_data_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ CSV 저장: {csv_file}")
        
        # Excel 저장
        excel_file = self.results_dir / f"merged_data_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='merged_data', index=False)
        print(f"✅ Excel 저장: {excel_file}")
        
        return str(csv_file), str(excel_file)


class GoogleSheetsUploader:
    def __init__(self, credentials_dir="../"):
        """
        구글 시트 업로더 초기화
        
        Args:
            credentials_dir (str): 서비스 계정 키 파일 디렉토리 경로
        """
        self.credentials_dir = credentials_dir
        self.spreadsheet_id = '1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4'
        self.sheet_id = 1897433730
        self.service_account_email = 'nofee-price-bot@nofee-price.iam.gserviceaccount.com'
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
    def find_service_account_file(self):
        """
        서비스 계정 키 파일을 찾아서 반환
        
        Returns:
            str: 서비스 계정 키 파일 경로
        """
        # 가능한 파일명들
        possible_files = [
            'google_api_key.json',
            'service-account-key.json',
            'google-service-account.json',
            'nofee-price-service-account-key.json',
            'credentials.json'
        ]
        
        for filename in possible_files:
            file_path = os.path.join(self.credentials_dir, filename)
            if os.path.exists(file_path):
                return file_path
        
        # JSON 파일 모두 찾기
        json_files = glob(os.path.join(self.credentials_dir, "*.json"))
        if json_files:
            return json_files[0]
        
        return None
    
    def upload_to_google_sheets(self, df, sheet_name=None):
        """
        데이터프레임을 구글 시트에 업로드
        
        Args:
            df (pd.DataFrame): 업로드할 데이터프레임
            sheet_name (str, optional): 시트명. 기본값은 'merged_data'
        """
        if sheet_name is None:
            sheet_name = 'merged_data'
        
        # 서비스 계정 파일 찾기
        service_account_file = self.find_service_account_file()
        
        if not service_account_file:
            print("❌ 서비스 계정 키 파일을 찾을 수 없습니다.")
            print(f"credentials 디렉토리: {self.credentials_dir}")
            print("\n서비스 계정 키 파일을 다운로드하여 credentials 폴더에 저장해주세요.")
            print("파일명 예시: service-account-key.json")
            return False
        
        print(f"Using service account file: {service_account_file}")
        
        try:
            # 인증 정보 생성
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.scopes)
            
            # Google Sheets API 서비스 생성
            service = build('sheets', 'v4', credentials=credentials)
            
            # 데이터를 2차원 리스트로 변환
            values = [df.columns.tolist()]  # 헤더
            
            # 데이터 행 추가
            for _, row in df.iterrows():
                row_values = [str(val) for val in row]
                values.append(row_values)
            
            print(f"총 {len(values)}개 행 (헤더 포함) 준비 완료")
            
            # 시트 클리어
            print(f"{sheet_name} 시트 클리어 중...")
            service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:ZZ"
            ).execute()
            
            # 새 데이터 쓰기
            print(f"{sheet_name} 시트에 데이터 쓰는 중...")
            body = {'values': values}
            
            result = service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ 업로드 완료: {result.get('updatedCells')}개 셀 업데이트됨")
            print(f"✅ 업로드 범위: {result.get('updatedRange')}")
            print(f"✅ 스프레드시트 URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            
            return True
            
        except FileNotFoundError:
            print("❌ 서비스 계정 키 파일을 찾을 수 없습니다.")
            print(f"   파일 경로: {service_account_file}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            print("\n확인사항:")
            print("1. 서비스 계정 이메일이 Google Sheets에 편집 권한이 있는지 확인")
            print(f"   서비스 계정: {self.service_account_email}")
            print("2. Google Sheets API가 활성화되어 있는지 확인")
            print("3. 서비스 계정 키 파일이 올바른지 확인")
            
        return False


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("데이터 병합 및 구글 스프레드시트 업로드 프로그램")
    print("=" * 60)
    
    # 현재 스크립트 위치 기준으로 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 프로젝트 루트 찾기 (src/data_processing에서 두 단계 위로)
    project_root = os.path.dirname(os.path.dirname(script_dir))
    raw_data_dir = os.path.join(project_root, "data", "raw")
    credentials_dir = "/Users/jacob_athometrip/Desktop/dev/nofee/workspace_nofee/config"  # Google API 키가 있는 경로
    
    try:
        # 1. 데이터 병합
        merger = DataMerger(raw_data_dir, credentials_dir)
        merged_df = merger.merge_data()
        
        # 2. 구글 시트 업로드
        uploader = GoogleSheetsUploader(credentials_dir)
        success = uploader.upload_to_google_sheets(merged_df, 'support')
        
        if success:
            print("\n✅ 모든 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n❌ 구글 시트 업로드에 실패했습니다.")
            
            # 로컬에 백업 파일 저장
            backup_file = os.path.join(script_dir, f"merged_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            merged_df.to_csv(backup_file, index=False, encoding='utf-8-sig')
            print(f"백업 파일이 저장되었습니다: {backup_file}")
            
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()