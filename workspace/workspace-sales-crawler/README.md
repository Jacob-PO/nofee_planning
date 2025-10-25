# Sales Crawler Workspace

휴대폰 매장 영업 정보를 수집하는 크롤러 모음입니다.

## 📁 Project Structure

```
workspace-sales-crawler/
├── naver-map-crawler/        # 네이버 지도 크롤러 (메인)
├── naver-store-crawler/      # 네이버 블로그/카페 크롤러
├── google-store-crawler/     # Google 검색 크롤러
└── venv/                     # Python 가상환경
```

## 🎯 Crawlers Overview

### 1. Naver Map Crawler (메인 크롤러)
**위치**: `naver-map-crawler/`

네이버 지도에서 매장 정보를 자동 수집하는 메인 크롤러입니다.

**주요 기능**:
- Selenium 기반 자동 크롤링
- 전국 지역별 자동 검색
- 중복 제거 (기존 주소 기반)
- Google Sheets 자동 업로드
- 전화번호/웹사이트 필터링

**수집 데이터**:
- 매장명, 주소, 전화번호
- 업종, 영업시간
- 방문자리뷰, 블로그리뷰
- 웹사이트

📖 **상세 문서**: [naver-map-crawler/README.md](naver-map-crawler/README.md)

### 2. Naver Store Crawler
**위치**: `naver-store-crawler/`

네이버 블로그/카페 검색을 통해 매장 정보를 수집합니다.

**주요 기능**:
- 블로그/카페 검색 크롤링
- 전국 주요 지역 자동 검색
- 매장명 자동 추출 (정규식 패턴)

📖 **상세 문서**: [naver-store-crawler/README.md](naver-store-crawler/README.md)

### 3. Google Store Crawler
**위치**: `google-store-crawler/`

Google 검색 결과에서 매장 정보를 추출합니다.

**주요 기능**:
- Google 검색 결과 크롤링
- 17개 광역시도 × 세부 지역 검색
- 웹페이지 파싱 및 정보 추출

📖 **상세 문서**: [google-store-crawler/README.md](google-store-crawler/README.md)

## 🚀 Quick Start

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 2. 메인 크롤러 실행

```bash
cd naver-map-crawler
python naver_map_crawler.py
```

### 3. Google Sheets 업로드

```bash
cd naver-map-crawler
python google_sheets_uploader.py
```

## 📋 Requirements

- Python 3.8+
- Chrome Browser (Naver Map Crawler용)
- Google API credentials (Sheets 업로드용)

## 🔧 Installation

각 크롤러 폴더에서:

```bash
pip install -r requirements.txt
```

## 📊 Data Flow

```
Naver Map Search → naver-map-crawler
       ↓
  Crawling & Filtering
       ↓
  results/naver_map_results.csv
       ↓
  google_sheets_uploader.py
       ↓
  Google Sheets (영업DB)
```

## 🗂️ Recommended Workflow

1. **메인 크롤러 실행**: `naver-map-crawler`로 네이버 지도 데이터 수집
2. **데이터 업로드**: Google Sheets에 자동 업로드
3. **보조 크롤러**: 필요시 `naver-store-crawler`, `google-store-crawler` 사용
4. **데이터 병합**: 각 크롤러 결과를 통합

## 📌 Important Notes

- **메인 크롤러**: `naver-map-crawler`를 주로 사용
- **중복 방지**: `addresses/existing_addresses.txt`로 자동 관리
- **API 키**: `api_keys/google_api_key.json` 필수 (Sheets 업로드)
- **결과 파일**: 각 크롤러의 `results/` 폴더에 저장

## 🔗 Links

- [Naver Map Crawler 상세 문서](naver-map-crawler/README.md)
- [Naver Store Crawler 상세 문서](naver-store-crawler/README.md)
- [Google Store Crawler 상세 문서](google-store-crawler/README.md)

## 📝 License

Private use only
