# Google Phone Store Crawler (당근마켓 휴대폰 매장 크롤러)

Google 검색을 통해 당근마켓의 휴대폰 매장 정보를 수집하는 Selenium 기반 크롤러입니다.

## 📁 파일 구조

```
google-phone-store-crawler/
├── crawler.py          # 메인 크롤러 스크립트
├── requirements.txt    # Python 패키지 의존성
├── README.md          # 설명서
├── output/            # 크롤링 결과 CSV 파일 저장
└── venv/              # Python 가상환경
```

## 🎯 기능

- ✅ Google 검색으로 당근마켓 local-profile 페이지 검색
- ✅ 개별 매장 페이지에서 매장명, 전화번호, 지역 정보 추출
- ✅ CSV 파일로 저장
- ✅ Google Sheets 자동 업로드
- ✅ 검색 결과 페이지 필터링 (개별 매장 페이지만 처리)

## 🚀 설치

```bash
# 가상환경 활성화
source ../venv/bin/activate

# 필요한 패키지 설치
pip install selenium pandas gspread google-auth
```

## 📖 사용법

```bash
# 크롤러 실행
python crawler.py
```

## ⚙️ 설정

`crawler.py` 파일의 `main()` 함수에서 다음 설정을 변경할 수 있습니다:

```python
# Google Sheets URL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/..."

# 검색 수 설정 (기본값: 3)
results = crawler.crawl(max_searches=50)

# 브라우저 표시 여부 (headless=True면 숨김)
crawler = DaangnStoreCrawlerSelenium(headless=False)
```

## 📊 출력 형식

CSV 및 Google Sheets에 다음 형식으로 저장됩니다:

| 지역명 | 매장명 | 지역명_매장명 | 전화번호 | 링크 |
|--------|--------|---------------|----------|------|
| 서울 종로구 | 휴대폰 성지 | 서울 종로구_휴대폰 성지 | 010-2131-0374 | https://www.daangn.com/kr/local-profile/... |
| 부산 부산진구 | 휴대폰성지 | 부산 부산진구_휴대폰성지 | 010-6676-8832 | https://www.daangn.com/kr/local-profile/... |

## 🔍 검색 전략

### 검색 지역
서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 경기, 강원, 충북, 충남, 전북, 전남, 경북, 경남, 제주

### 검색 키워드
휴대폰매장, 휴대폰성지, 스마트폰매장, 폰매장, 중고폰, 아이폰

### 검색 쿼리 예시
- "서울 휴대폰매장 site:daangn.com"
- "부산 휴대폰성지 site:daangn.com"
- "대구 스마트폰매장 site:daangn.com"

## ⚠️ 주의사항

- Chrome 브라우저가 설치되어 있어야 합니다
- Google Sheets 업로드를 위해서는 `../../config/google_api_key.json` 파일이 필요합니다
- 검색 결과 페이지(`?in=...&search=...`)는 자동으로 건너뜁니다
- 개별 매장 페이지만 처리합니다
- 크롤링 속도 제한을 위해 요청 간 2-3초 대기 시간이 설정되어 있습니다

## 📁 결과 파일

수집된 데이터는 `output/` 폴더에 저장됩니다:

```
output/
└── daangn_stores_selenium_20251016_170940.csv
```

## 🔧 구조

```python
class DaangnStoreCrawlerSelenium:
    - init_driver()                    # Chrome 드라이버 초기화
    - search_daangn_stores()           # Google에서 당근마켓 링크 검색
    - extract_store_info_from_page()   # 매장 정보 추출
    - crawl()                          # 메인 크롤링 실행
    - save_to_csv()                    # CSV 저장
    - upload_to_sheets()               # Google Sheets 업로드
```
