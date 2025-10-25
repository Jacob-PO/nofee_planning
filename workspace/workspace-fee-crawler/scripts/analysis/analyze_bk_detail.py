import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

def analyze_bk_detail():
    """비케이 데이터 상세 분석"""
    
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
        
        # 각 행의 길이를 헤더 길이에 맞추기
        aligned_data = []
        for row in data:
            if len(row) < len(headers):
                row.extend([''] * (len(headers) - len(row)))
            aligned_data.append(row[:len(headers)])
        
        df = pd.DataFrame(aligned_data, columns=headers)
        
        # 비케이 데이터만 필터링
        bk_data = df[df['dealer'] == '비케이'].copy()
        
        print(f"\n=== 비케이 데이터 상세 분석 ===")
        print(f"총 비케이 데이터 수: {len(bk_data)}")
        
        # 날짜별로 그룹화
        if 'date' in bk_data.columns:
            date_groups = bk_data.groupby('date')
            print(f"\n날짜별 데이터 수:")
            for date, group in date_groups:
                print(f"  {date}: {len(group)}개")
                
                # 중복된 기기명 확인
                device_counts = group['device_nm'].value_counts()
                duplicates = device_counts[device_counts > 1]
                if len(duplicates) > 0:
                    print(f"    중복 기기: {', '.join(duplicates.index)}")
        
        # 중복 데이터 상세 분석
        print(f"\n=== 중복 데이터 상세 분석 ===")
        device_counts = bk_data['device_nm'].value_counts()
        duplicated_devices = device_counts[device_counts > 1]
        
        for device in duplicated_devices.index:
            print(f"\n기기명: {device}")
            device_data = bk_data[bk_data['device_nm'] == device]
            
            # 날짜, 번호이동/기기변경 지원금 등 주요 컬럼 표시
            display_cols = ['date', 'device_nm', '번호이동_공시_115k', '번호이동_선약_115k', 
                          '기기변경_공시_115k', '기기변경_선약_115k']
            available_cols = [col for col in display_cols if col in device_data.columns]
            
            print(device_data[available_cols].to_string(index=False))
            
            # 값이 동일한지 확인
            if len(device_data) == 2:
                row1 = device_data.iloc[0]
                row2 = device_data.iloc[1]
                
                different_cols = []
                for col in device_data.columns:
                    if row1[col] != row2[col]:
                        different_cols.append(col)
                
                if different_cols:
                    print(f"  차이나는 컬럼: {', '.join(different_cols)}")
                else:
                    print("  ⚠️ 완전히 동일한 중복 데이터!")
        
        # 데이터 패턴 분석
        print(f"\n=== 데이터 패턴 분석 ===")
        
        # 지원금 값 패턴 확인
        subsidy_cols = [col for col in bk_data.columns if '공시' in col or '선약' in col]
        
        for col in subsidy_cols[:4]:  # 처음 4개 컬럼만 샘플로
            print(f"\n{col} 값 분포:")
            value_counts = bk_data[col].value_counts().head(10)
            print(value_counts)
            
            # 비정상적인 값 확인
            non_numeric = bk_data[col][~bk_data[col].str.match(r'^\d*$', na=True)]
            if len(non_numeric) > 0:
                print(f"  ⚠️ 숫자가 아닌 값 발견: {non_numeric.unique()}")
        
        # 비케이2로 의심되는 데이터 찾기
        print(f"\n=== 비케이2로 의심되는 데이터 확인 ===")
        
        # 최근 추가된 데이터 확인
        if 'date' in bk_data.columns:
            # 날짜를 datetime으로 변환 시도
            try:
                bk_data['date_parsed'] = pd.to_datetime(bk_data['date'], format='%Y-%m-%d', errors='coerce')
                if not bk_data['date_parsed'].isna().all():
                    latest_date = bk_data['date_parsed'].max()
                    latest_data = bk_data[bk_data['date_parsed'] == latest_date]
                    
                    print(f"가장 최근 날짜: {latest_date}")
                    print(f"해당 날짜 데이터 수: {len(latest_data)}")
                    print(f"기기 목록:")
                    print(latest_data['device_nm'].tolist())
            except:
                print("날짜 파싱 실패")
        
        # 엑셀 파일로 저장
        output_file = 'bk_data_analysis.xlsx'
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            bk_data.to_excel(writer, sheet_name='비케이_전체데이터', index=False)
            
            # 중복 데이터만 따로 저장
            duplicated_data = pd.DataFrame()
            for device in duplicated_devices.index:
                device_data = bk_data[bk_data['device_nm'] == device]
                duplicated_data = pd.concat([duplicated_data, device_data])
            
            if not duplicated_data.empty:
                duplicated_data.to_excel(writer, sheet_name='중복데이터', index=False)
        
        print(f"\n분석 결과를 {output_file}에 저장했습니다.")
        
        return bk_data
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    bk_data = analyze_bk_detail()