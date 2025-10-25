# NoFee Workspace

**통합 프로젝트 레파지토리 - 통신 요금, 광고, 분석, 영업 자동화**

NoFee 서비스 운영에 필요한 모든 자동화 도구와 분석 시스템을 하나의 레파지토리에서 관리합니다.

---

## 📁 프로젝트 구조

```
workspace_nofee/
├── workspace-fee-crawler/      # 통신사 요금 크롤러
├── workspace-ads/              # 광고 및 캠페인 관리
├── workspace-sales-crawler/    # 영업 데이터 수집
├── workspace_analytics/        # GA4 분석 대시보드
├── workspace_planning/         # 기획 문서
└── config/                     # 공통 설정 (API 키 등)
```

---

## 🚀 주요 워크스페이스

### 1️⃣ [workspace-fee-crawler](workspace-fee-crawler/) - 통신사 요금 크롤러

**통신사 요금제 및 기기 가격 자동 수집 · 처리 시스템**

KT, SK, LG 통신사의 요금제와 기기 가격 정보를 자동으로 크롤링하고, OCR 처리, 데이터 병합, Google Sheets 업로드를 수행합니다.

**주요 기능:**
- 🔍 가격 크롤러 (KT/SK/LG)
- 📊 이미지 OCR (CLOVA OCR API)
- 🔀 데이터 병합 및 리베이트 계산
- 📋 가격 요약 및 Google Sheets 업로드

**빠른 시작:**
```bash
cd workspace-fee-crawler
./run.sh
```

**상세 문서:** [workspace-fee-crawler/README.md](workspace-fee-crawler/README.md)

---

### 2️⃣ [workspace-ads](workspace-ads/) - 광고 및 캠페인 관리

**광고 소재, 캠페인 가격표, 주간 리포트 생성 도구**

노피 서비스의 마케팅 캠페인, 가격표, 주간 실적 리포트를 자동으로 생성합니다.

**주요 기능:**
- 📱 Instagram 콘텐츠 생성
- 💰 캠페인 가격표 자동 생성
- 📊 주간 실적 리포트 (Toss 스타일)
- 🏬 핸드폰 매장 카드뉴스

**주요 파일:**
```
workspace-ads/
├── campaign_price_toss_style.py     # 캠페인 가격표 생성
├── weekly_report/                   # 주간 리포트
│   ├── toss_style_report.py        # Toss 스타일 리포트
│   ├── period_report.py             # 기간별 리포트
│   └── dashboard.py                 # 대시보드 생성
├── instagram-content/               # Instagram 콘텐츠
└── phone-shops-cardnews/            # 매장 카드뉴스
```

**실행 예시:**
```bash
cd workspace-ads

# 캠페인 가격표 생성
python campaign_price_toss_style.py

# 주간 리포트 생성
python weekly_report/toss_style_report.py
```

---

### 3️⃣ [workspace-sales-crawler](workspace-sales-crawler/) - 영업 데이터 수집

**네이버 지도 크롤링을 통한 영업 대상 매장 데이터 수집**

핸드폰 대리점 정보를 자동으로 수집하고 중복 제거, Google Sheets 업로드를 수행합니다.

**주요 기능:**
- 🗺️ 네이버 지도 크롤링
- 🔄 중복 주소 자동 제거
- 📊 Google Sheets 자동 업로드
- 💾 백업 및 버전 관리

**주요 파일:**
```
workspace-sales-crawler/
├── full_pagination_crawler_no_duplicates.py  # 메인 크롤러
├── google_sheets_uploader.py                 # Sheets 업로드
├── merge_duplicates_advanced.py              # 중복 제거
└── download_and_backup.py                    # 백업
```

**실행 예시:**
```bash
cd workspace-sales-crawler

# 크롤링 실행
python full_pagination_crawler_no_duplicates.py

# Google Sheets 업로드
python google_sheets_uploader.py
```

---

### 4️⃣ [workspace_analytics](workspace_analytics/) - GA4 분석 대시보드

**Google Analytics 4 데이터 수집 및 시각화**

GA4 데이터를 자동으로 수집하고 Chart.js 기반 대시보드로 시각화합니다.

**주요 기능:**
- 📈 GA4 데이터 자동 수집
- 📊 Chart.js 대시보드
- 💼 회사 소개 페이지
- 🎯 Pitch Deck (한/영)

**주요 파일:**
```
workspace_analytics/
├── ga4_data_fetcher.py              # GA4 데이터 수집
├── generate_integrated_dashboard.py  # 대시보드 생성
├── index.html                        # 메인 대시보드
└── company_intro/                    # 회사 소개
    ├── pitch-deck-ko.html           # 한글 Pitch Deck
    ├── pitch-deck-en.html           # 영문 Pitch Deck
    └── sales-guide.html             # 영업 가이드
```

**빠른 시작:**
```bash
cd workspace_analytics

# GA4 데이터 수집
python ga4_data_fetcher.py

# 통합 대시보드 생성
python generate_integrated_dashboard.py

# 대시보드 확인
open index.html
```

**상세 문서:** [workspace_analytics/README.md](workspace_analytics/README.md)

---

### 5️⃣ [workspace_planning](workspace_planning/) - 기획 문서

**서비스 기획 문서 및 제안서**

노피 서비스의 기획 문서와 제안서를 관리합니다.

**주요 문서:**
- 📋 견적 신청 10분 룰 기획안
- 📊 시세표 기능 기획안
- 🏘️ 동네성지 랜딩페이지 기획안
- 📝 서비스 소개 문서

---

## ⚙️ 공통 설정

### [config/](config/) - API 키 및 설정

모든 워크스페이스에서 사용하는 API 키와 설정 파일을 관리합니다.

**설정 파일:**
```
config/
├── google_api_key.json                      # Google API 키
├── github-token.json                        # GitHub 토큰
├── clova_ocr_api_key.json                  # CLOVA OCR API 키
└── CLOVA_OCR_CUSTOM_API_EXTERNAL_V1.1.json # CLOVA OCR 설정
```

---

## 🛠️ 기술 스택

### 백엔드
- **Python 3.13** - 메인 언어
- **Selenium** - 웹 크롤링
- **pandas** - 데이터 처리
- **openpyxl** - Excel 파일 처리

### API & 서비스
- **Google Sheets API** - 데이터 저장 및 공유
- **Google Analytics 4 API** - 분석 데이터 수집
- **CLOVA OCR API** - 이미지 텍스트 추출
- **GitHub API** - 버전 관리

### 프론트엔드
- **Chart.js** - 데이터 시각화
- **HTML/CSS/JavaScript** - 대시보드 및 광고 페이지

---

## 📊 데이터 흐름

```
1. 데이터 수집
   ├── workspace-fee-crawler    → 통신사 요금 크롤링
   ├── workspace-sales-crawler  → 영업 대상 매장 크롤링
   └── workspace_analytics      → GA4 데이터 수집

2. 데이터 처리
   ├── OCR 처리 (이미지 → 텍스트)
   ├── 데이터 병합 및 정제
   └── 리베이트 자동 계산

3. 데이터 저장 & 공유
   ├── Google Sheets 업로드
   ├── Excel/CSV 파일 저장
   └── 백업 (날짜별 아카이브)

4. 시각화 & 리포트
   ├── 주간 실적 리포트
   ├── 캠페인 가격표
   ├── GA4 대시보드
   └── Pitch Deck
```

---

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/Jacob-PO/workspace_nofee.git
cd workspace_nofee
```

### 2. 설정 파일 준비

```bash
# config 폴더에 API 키 설정 파일 추가
# - google_api_key.json
# - clova_ocr_api_key.json
# 등
```

### 3. 각 워크스페이스별 실행

```bash
# 통신사 요금 크롤러
cd workspace-fee-crawler
./run.sh

# 광고 캠페인 생성
cd workspace-ads
python campaign_price_toss_style.py

# 영업 데이터 수집
cd workspace-sales-crawler
python full_pagination_crawler_no_duplicates.py

# GA4 대시보드
cd workspace_analytics
python generate_integrated_dashboard.py
```

---

## 📝 워크스페이스별 의존성 설치

각 워크스페이스는 독립적인 requirements.txt를 가지고 있습니다.

```bash
# workspace-fee-crawler
cd workspace-fee-crawler
pip install -r requirements.txt

# workspace-ads
cd workspace-ads
pip install -r requirements.txt

# workspace-sales-crawler
cd workspace-sales-crawler
pip install -r requirements.txt

# workspace_analytics
cd workspace_analytics
pip install -r requirements.txt
```

---

## 🔒 보안 주의사항

### API 키 관리
- ✅ 모든 API 키는 `config/` 폴더에 저장
- ✅ Git에 커밋되어 있음 (Private 레파지토리)
- ⚠️ 공개 레파지토리로 전환 시 `.gitignore`에 `config/` 추가 필수

### 환경 변수
각 워크스페이스에서 필요한 환경 변수:
- `CLOVA_OCR_API_URL` - CLOVA OCR API 엔드포인트
- `CLOVA_OCR_SECRET_KEY` - CLOVA OCR Secret Key

---

## 📈 프로젝트 통계

- **워크스페이스**: 5개
- **총 Python 파일**: 100+ 개
- **데이터 파일**: 300+ 개
- **지원 통신사**: 3개 (KT, SK, LG)
- **API 연동**: 4개 (Google Sheets, GA4, CLOVA OCR, GitHub)

---

## 🗂️ 레파지토리 이력

### 2025-10-16 - 통합 레파지토리 생성

**통합된 레파지토리:**
- `workspace_analytics` → 통합
- `workspace-fee-crawler` → 통합
- `nofee_planning` → 통합
- `workspace-ads` → 추가
- `workspace-sales-crawler` → 추가

**아카이브된 레파지토리 (9개):**
- Jacob-PO/workspace_analytics (private, archived)
- Jacob-PO/workspace-fee-crawler (private, archived)
- Jacob-PO/nofee_planning (private, archived)
- Jacob-PO/nofee_event (private, archived)
- Jacob-PO/workspace-fee-crawler_v2 (private, archived)
- Jacob-PO/workspace-plota (private, archived)
- Jacob-PO/nofee-webflow (private, archived)
- Jacob-PO/nofee_chat (private, archived)
- Jacob-PO/my_store_app (private, archived)

**통합 이점:**
- ✅ 단일 레파지토리로 관리 용이
- ✅ 공통 설정 파일 통합 (`config/`)
- ✅ 워크스페이스 간 코드 재사용 쉬움
- ✅ CI/CD 파이프라인 통합 가능

---

## 🤝 기여 가이드

이 프로젝트는 NoFee 팀 내부용 프로젝트입니다.

**워크스페이스별 담당:**
- `workspace-fee-crawler` - 요금 데이터 수집 및 처리
- `workspace-ads` - 마케팅 및 광고
- `workspace-sales-crawler` - 영업 데이터 관리
- `workspace_analytics` - 데이터 분석 및 대시보드
- `workspace_planning` - 서비스 기획

---

## 📄 라이선스

이 프로젝트는 NoFee 팀의 내부 프로젝트입니다.

---

## 👥 팀

**Organization**: Jacob-PO
**Repository**: workspace_nofee
**Type**: Private
**Last Updated**: 2025-10-16

---

## 🔗 관련 링크

- [GitHub Repository](https://github.com/Jacob-PO/workspace_nofee)
- [노피 웹사이트](https://nofee.team)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Google Analytics 4 API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [CLOVA OCR](https://www.ncloud.com/product/aiService/ocr)

---

## 📞 문의

프로젝트 관련 문의사항은 팀 내부 채널을 통해 문의해주세요.

---

**workspace_nofee** - NoFee 서비스 운영의 모든 것을 하나로
