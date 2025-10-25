# 네이버 휴대폰 매장 크롤러

네이버 블로그/카페에서 휴대폰 매장 정보를 자동으로 수집하는 크롤러입니다.

## 주요 기능

✅ **자동 검색어 생성**: 전국 주요 지역 + 휴대폰 관련 키워드 자동 조합
✅ **다중 소스**: 네이버 블로그 + 카페 검색 결과 수집
✅ **매장명 자동 추출**: AI 패턴 인식으로 매장명 자동 추출
✅ **Google Sheets 자동 업로드**: 수집 즉시 구글 시트에 자동 업로드
✅ **CSV 저장**: 엑셀에서 바로 열 수 있는 형식으로 저장 (백업용)
✅ **중복 제거**: 동일 링크 자동 제거 (기존 데이터와 비교)
✅ **계속 쌓아나가기**: 실행할 때마다 새로운 데이터만 추가

## 수집 데이터 형식

| 지역명 | 매장명 | 지역명_매장명 | 링크 | 출처 | 제목 |
|--------|--------|---------------|------|------|------|
| 경기 평택 | 휴대폰성지 | 경기 평택_휴대폰성지 | https://... | blog | ... |

**참고**: 개인정보(전화번호, 이메일 등)는 수집하지 않습니다.

## 설치 방법

```bash
cd workspace-sales-crawler/naver-store-crawler

# 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 1. 기본 실행 (자동 업로드 포함)

```bash
cd workspace-sales-crawler/naver-store-crawler
python crawler.py
```

실행하면:
1. 네이버 블로그/카페 크롤링 (기본 5개 지역)
2. CSV 파일 저장 (백업용)
3. **Google Sheets 자동 업로드** (naver 시트에 추가)
4. 중복 제거 (기존 링크와 비교)

### 2. 전체 지역 크롤링

`crawler.py` 파일을 열고 [304번째 줄](crawler.py#L304) 수정:

```python
# 기존 (5개 지역 테스트)
crawler.crawl_all(max_regions=5, max_pages_per_search=2)

# 전체 크롤링으로 변경 (150+ 지역)
crawler.crawl_all(max_regions=None, max_pages_per_search=2)
```

### 3. Google Sheets 설정

크롤러는 자동으로 다음 시트에 업로드합니다:
- **스프레드시트**: `1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo`
- **워크시트**: `naver`
- **인증**: `../../config/google_api_key.json`

다른 시트에 업로드하려면 [313-314번째 줄](crawler.py#L313) 수정:

```python
credentials_path = "../../config/google_api_key.json"
spreadsheet_url = "YOUR_SHEET_URL"
```

### 4. 맞춤 설정

```python
crawler = NaverStoreCrawler()

# 특정 지역만 검색
crawler.crawl_by_region("경기 평택", "휴대폰 매장", max_pages=3)

# 결과 저장
crawler.save_to_csv("my_results.csv")
```

## 파일 구조

```
naver-store-crawler/
├── crawler.py              # 메인 크롤러
├── sheets_uploader.py      # Google Sheets 업로드 모듈
├── regions.py              # 전국 지역 데이터
├── requirements.txt        # 필요 패키지
├── README.md              # 사용 설명서
└── naver_phone_stores_*.csv  # CSV 백업 파일 (실행 후 생성)

../../config/
└── google_api_key.json    # Google API 인증 파일
```

## 크롤링 설정

### regions.py에서 수정 가능

```python
# 지역 추가/제거
REGIONS = [
    "서울 강남구",
    "경기 평택",
    # ... 추가 지역
]

# 검색 키워드 추가/제거
SHOP_KEYWORDS = [
    "휴대폰 매장",
    "핸드폰 판매점",
    # ... 추가 키워드
]
```

## 주의사항

⚠️ **합법적 사용만 허용**
- 네이버 서비스 이용약관 준수
- 과도한 요청으로 서버에 부하를 주지 않도록 요청 간격 설정됨
- 개인정보는 수집하지 않음

⚠️ **크롤링 속도**
- 전체 지역 크롤링 시 시간이 오래 걸립니다 (약 30분~1시간)
- 처음엔 소수 지역으로 테스트 권장

⚠️ **결과 정확도**
- 매장명은 자동 추출되므로 100% 정확하지 않을 수 있음
- 결과 확인 후 수동 보정 필요

## 문제 해결

### Google Sheets 업로드 실패

1. **권한 오류**: Google Sheets에 서비스 계정 이메일 추가
   - 시트 열기 → 공유 → `nofee-price-bot@nofee-price.iam.gserviceaccount.com` 추가
   - 권한: 편집자

2. **인증 파일 없음**: `../../config/google_api_key.json` 경로 확인

3. **시트 이름 오류**: 스프레드시트에 'naver' 워크시트가 있는지 확인 (없으면 자동 생성)

### 결과가 적게 나오는 경우

1. `max_pages_per_search` 값 증가
2. `SHOP_KEYWORDS`에 키워드 추가
3. 네이버 검색 결과 HTML 구조 변경 확인

### 오류 발생 시

- 인터넷 연결 확인
- 패키지 재설치: `pip install -r requirements.txt --upgrade`
- User-Agent 업데이트

## 라이선스

개인 및 상업적 용도 사용 가능 (합법적 범위 내)

## 작동 방식

1. **크롤링**: 전국 지역 × 키워드 조합으로 네이버 검색
2. **데이터 수집**: 블로그/카페 게시글 제목, 링크, 설명 추출
3. **매장명 추출**: 텍스트 패턴 분석으로 매장명 자동 추출
4. **CSV 저장**: 로컬 백업 파일 생성
5. **중복 확인**: Google Sheets의 기존 링크 확인
6. **자동 업로드**: 신규 데이터만 시트에 추가

## 버전

- v1.1.0 - Google Sheets 자동 업로드 추가 (2025-10-16)
- v1.0.0 - 초기 릴리즈 (2025-10-16)
