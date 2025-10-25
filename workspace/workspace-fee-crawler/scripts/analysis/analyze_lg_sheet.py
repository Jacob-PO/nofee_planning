import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path
from collections import Counter

def analyze_lg_sheet():
    """Google Sheets의 lg_price 시트 데이터 분석"""
    
    # Google Sheets API 인증
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SPREADSHEET_ID = '1njdeOI4TLyF2IkggosBUGgg5yKetez8cdcepbsAeEx4'
    SHEET_NAME = 'lg_price'
    
    try:
        # 인증 정보 생성
        project_root = Path(__file__).parent
        key_file = project_root / "src" / "config" / "google_api_key.json"
        
        credentials = service_account.Credentials.from_service_account_file(
            str(key_file), scopes=SCOPES)
        
        # Google Sheets API 서비스 생성
        service = build('sheets', 'v4', credentials=credentials)
        
        # 시트 데이터 읽기
        print(f"Google Sheets에서 {SHEET_NAME} 시트 읽는 중...")
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:ZZ"
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("데이터가 없습니다.")
            return
        
        # DataFrame으로 변환
        headers = values[0]
        data = values[1:]
        df = pd.DataFrame(data, columns=headers[:len(data[0])])
        
        print(f"\n전체 데이터 행 수: {len(df)}")
        print(f"컬럼: {list(df.columns)}")
        
        # dealer 컬럼 분석
        if 'dealer' in df.columns:
            dealer_counts = df['dealer'].value_counts()
            print(f"\n=== Dealer별 데이터 개수 ===")
            print(dealer_counts)
            
            # '비케이' 관련 데이터 필터링
            bk_data = df[df['dealer'].str.contains('비케이', na=False)]
            print(f"\n=== '비케이' 관련 데이터 분석 ===")
            print(f"'비케이' 관련 총 데이터 수: {len(bk_data)}")
            
            # dealer 값의 정확한 구분
            bk_dealers = bk_data['dealer'].unique()
            print(f"\n'비케이' 관련 dealer 종류: {bk_dealers}")
            
            for dealer in bk_dealers:
                dealer_data = bk_data[bk_data['dealer'] == dealer]
                print(f"\n--- {dealer} 분석 ---")
                print(f"데이터 개수: {len(dealer_data)}")
                
                # device_nm 중복 확인
                if 'device_nm' in df.columns:
                    device_counts = dealer_data['device_nm'].value_counts()
                    duplicated = device_counts[device_counts > 1]
                    if len(duplicated) > 0:
                        print(f"\n중복된 기기명 (device_nm):")
                        print(duplicated)
                    else:
                        print("중복된 기기명 없음")
                    
                    # 샘플 데이터 출력
                    print(f"\n{dealer}의 샘플 데이터 (처음 5개):")
                    sample_cols = ['device_nm', 'installment_period', 'disclosure_subsidy', 
                                 'public_subsidy', 'manufacturer_subsidy', 'crawl_date']
                    available_cols = [col for col in sample_cols if col in df.columns]
                    print(dealer_data[available_cols].head())
                
                # 데이터 형식 확인
                print(f"\n{dealer} 데이터 형식 분석:")
                if 'installment_period' in df.columns:
                    periods = dealer_data['installment_period'].unique()
                    print(f"할부 기간 종류: {periods}")
                
                if 'crawl_date' in df.columns:
                    dates = dealer_data['crawl_date'].unique()
                    print(f"크롤링 날짜: {dates[:5]}")  # 처음 5개만
                
                # 공시지원금 분석
                if 'disclosure_subsidy' in df.columns:
                    # 숫자가 아닌 값 확인
                    non_numeric = dealer_data[~dealer_data['disclosure_subsidy'].str.match(r'^\d+$', na=True)]
                    if len(non_numeric) > 0:
                        print(f"\n공시지원금에 숫자가 아닌 값 발견: {len(non_numeric)}개")
                        print(non_numeric[['device_nm', 'disclosure_subsidy']].head())
        
        # 전체 데이터에서 최근 추가된 데이터 확인
        if 'crawl_date' in df.columns:
            print(f"\n=== 최근 크롤링 데이터 확인 ===")
            df['crawl_date_parsed'] = pd.to_datetime(df['crawl_date'], errors='coerce')
            latest_dates = df['crawl_date_parsed'].dropna().nlargest(5).unique()
            
            for date in latest_dates:
                date_data = df[df['crawl_date_parsed'] == date]
                print(f"\n날짜: {date}")
                print(f"데이터 수: {len(date_data)}")
                if 'dealer' in df.columns:
                    dealer_counts = date_data['dealer'].value_counts()
                    print(f"Dealer별 데이터:")
                    print(dealer_counts)
        
        # 데이터 무결성 검사
        print(f"\n=== 데이터 무결성 검사 ===")
        
        # 필수 컬럼 확인
        required_cols = ['device_nm', 'dealer', 'installment_period', 'disclosure_subsidy']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"누락된 필수 컬럼: {missing_cols}")
        
        # 빈 값 확인
        for col in df.columns:
            empty_count = df[col].isna().sum() + (df[col] == '').sum()
            if empty_count > 0:
                print(f"{col} 컬럼의 빈 값: {empty_count}개")
        
        # 이상한 패턴 찾기
        if 'device_nm' in df.columns:
            # 특수문자나 이상한 패턴 확인
            special_chars = df['device_nm'].str.contains(r'[^\w\s\-()]', regex=True, na=False)
            if special_chars.any():
                print(f"\n특수문자가 포함된 기기명: {special_chars.sum()}개")
                print(df[special_chars]['device_nm'].head(10))
        
        return df
        
    except FileNotFoundError:
        print("❌ 서비스 계정 키 파일을 찾을 수 없습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    df = analyze_lg_sheet()