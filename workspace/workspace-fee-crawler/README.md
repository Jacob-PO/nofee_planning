# Workspace Fee Crawler

**통신사 요금제 및 기기 가격 자동 수집 · 처리 시스템**

KT, SK, LG 통신사의 요금제와 기기 가격 정보를 자동으로 크롤링하고, OCR 처리, 데이터 병합, Google Sheets 업로드를 수행하는 통합 시스템입니다.

---

## 📁 프로젝트 구조

```
workspace-fee-crawler/
├── price_crawler/         # 🔍 가격 크롤러 (코드 + 데이터 + 로그)
│   ├── kt_crawler.py     # KT 크롤러
│   ├── sk_crawler.py     # SK 크롤러
│   ├── lg_crawler.py     # LG 크롤러
│   ├── data/             # 크롤링 데이터
│   ├── checkpoints/      # 체크포인트
│   └── logs/             # 크롤러 로그
│
├── image_ocr/             # 📊 이미지 OCR (코드 + 데이터 + 로그)
│   ├── clova_ocr.py      # CLOVA OCR 메인
│   ├── extract_text_colors.py
│   ├── policy_calculator.py
│   ├── upload_calculated_to_sheets.py
│   ├── input/            # 입력 이미지
│   ├── output/           # OCR 결과
│   │   ├── latest/       # 최신 파일
│   │   └── archive/      # 날짜별 아카이브
│   └── logs/             # OCR 로그
│
├── data_merge/            # 🔀 데이터 병합 (코드 + 데이터 + 로그)
│   ├── kt_merge.py       # KT 병합
│   ├── sk_merge.py       # SK 병합
│   ├── lg_merge.py       # LG 병합
│   ├── data_merge_main.py    # 병합 메인
│   ├── merge_and_upload.py   # 병합 & 업로드
│   ├── rebate_calculator.py  # 리베이트 계산
│   ├── output/           # 병합 결과
│   │   ├── latest/       # 최신 파일
│   │   └── archive/      # 날짜별 아카이브
│   └── logs/             # 병합 로그
│
├── price_summary/         # 📋 가격 요약 (코드 + 데이터 + 로그)
│   ├── create_summary_clean.py   # Summary 생성
│   ├── clean_support_sheet.py    # 공시지원금 정제
│   ├── output/           # Summary 결과
│   │   ├── latest/       # 최신 파일
│   │   └── archive/      # 날짜별 아카이브
│   └── logs/             # Summary 로그
│
├── shared_config/         # 🔧 공통 코드
│   ├── config/           # 설정
│   │   ├── paths.py      # PathManager (중앙 경로 관리)
│   │   ├── google_api_key.json
│   │   └── credentials.json
│   └── utils/            # 유틸리티
│       └── google_sheets_upload.py
│
├── analysis/              # 📈 분석 결과
├── scripts/               # 유틸리티 스크립트
├── temp/                  # 임시 파일
├── backups/               # 백업 (자동)
├── run.sh                 # 통합 실행 스크립트
├── .gitignore
└── README.md
```

---

## 🚀 빠른 시작

### 1. 통합 실행 스크립트 (추천)

```bash
./run.sh
```

인터랙티브 메뉴에서 원하는 기능을 선택하세요:
- 1) 크롤러 실행 (KT/SK/LG)
- 2) 전체 데이터 업데이트 크롤러
- 3) OCR 실행 (Batch Table)
- 4) 머지 & 업로드 (All)
- 5) Summary 생성
- 6) 공시지원금 데이터 정제
- 7) 전체 파이프라인 (크롤러 → 머지 → Summary)
- 8) 폴더 구조 보기

### 2. 한줄 실행 명령어 (빠른 실행)

```bash
# KT 크롤러 실행
python3 price_crawler/kt_crawler.py

# SK 크롤러 실행
python3 price_crawler/sk_crawler.py

# LG 크롤러 실행
python3 price_crawler/lg_crawler.py

# 전체 크롤러 순차 실행
python3 price_crawler/kt_crawler.py && python3 price_crawler/sk_crawler.py && python3 price_crawler/lg_crawler.py

# OCR 배치 실행 (테이블 인식)
python3 image_ocr/clova_ocr.py batch --table

# KT 데이터 병합
python3 data_merge/kt_merge.py

# SK 데이터 병합
python3 data_merge/sk_merge.py

# LG 데이터 병합
python3 data_merge/lg_merge.py

# 전체 데이터 병합
python3 data_merge/data_merge_main.py all

# Summary 생성
python3 price_summary/create_summary_clean.py

# 공시지원금 정제
python3 price_summary/clean_support_sheet.py

# 전체 파이프라인 (크롤러 → 병합 → Summary)
python3 price_crawler/kt_crawler.py && python3 price_crawler/sk_crawler.py && python3 price_crawler/lg_crawler.py && python3 data_merge/data_merge_main.py all && python3 price_summary/create_summary_clean.py
```

### 3. 개별 실행 (상세)

```bash
# 크롤러 실행
python3 price_crawler/kt_crawler.py
python3 price_crawler/sk_crawler.py
python3 price_crawler/lg_crawler.py

# OCR 실행
python3 image_ocr/clova_ocr.py

# 병합 실행
python3 data_merge/kt_merge.py
python3 data_merge/sk_merge.py
python3 data_merge/lg_merge.py
python3 data_merge/data_merge_main.py all

# Summary 생성
python3 price_summary/create_summary_clean.py
```

---

## 💡 주요 기능

### 1. 가격 크롤러 (price_crawler/)
- **KT, SK, LG 통신사** 웹사이트 자동 크롤링
- Selenium 기반 동적 페이지 처리
- 체크포인트 저장으로 중단/재시작 지원
- **출력**: `price_crawler/data/`

### 2. 이미지 OCR (image_ocr/)
- **CLOVA OCR API** 를 통한 이미지 텍스트 추출
- 통신사 요금 정책 이미지 자동 인식
- 표 구조 인식 및 색상 정보 추출
- **출력**: `image_ocr/output/latest/` (최신), `image_ocr/output/archive/` (히스토리)

### 3. 데이터 병합 (data_merge/)
- 크롤링 데이터와 Google Sheets 데이터 병합
- 리베이트(대리점 지원금) 자동 계산
- 색상 코드 적용으로 가독성 향상
- **출력**: `data_merge/output/latest/` (최신), `data_merge/output/archive/` (히스토리)

### 4. 가격 요약 (price_summary/)
- 전체 통신사 데이터 통합 요약
- Google Sheets 자동 업로드
- CSV/Excel 형식 지원
- **출력**: `price_summary/output/latest/` (최신), `price_summary/output/archive/` (히스토리)

---

## 🏗️ 핵심 설계 원칙

### 1. 기능별 독립 폴더 구조
각 기능이 자신만의 **코드 + 데이터 + 로그**를 한 곳에서 관리합니다.

```
price_crawler/    # 크롤러에 관한 모든 것
image_ocr/        # OCR에 관한 모든 것
data_merge/       # 병합에 관한 모든 것
price_summary/    # Summary에 관한 모든 것
shared_config/    # 공통 코드만
```

### 2. Latest + Archive 패턴
항상 최신 파일에 빠르게 접근하면서도 히스토리를 보존합니다.

```
output/
├── latest/          # 항상 최신 파일 (glob/sort 불필요)
│   └── kt_merged_latest.xlsx
└── archive/         # 날짜별 아카이브
    ├── 20251015/
    └── 20251014/
```

**적용 범위**:
- `image_ocr/output/` - OCR 결과
- `data_merge/output/` - 병합 결과
- `price_summary/output/` - Summary 결과

### 3. 중앙 경로 관리 (PathManager)
모든 경로를 `shared_config/config/paths.py`에서 관리합니다.

```python
from shared_config.config.paths import PathManager

pm = PathManager()
pm.crawler_dir          # price_crawler/
pm.ocr_latest_dir       # image_ocr/output/latest/
pm.merged_latest_dir    # data_merge/output/latest/
pm.summary_latest_dir   # price_summary/output/latest/
```

---

## 📊 데이터 흐름

```
1. 크롤링 (price_crawler/)
   ↓
   크롤링 데이터 저장: price_crawler/data/*.csv

2. OCR (image_ocr/) [선택사항]
   ↓
   이미지 → 텍스트 추출
   ↓
   OCR 결과 저장: image_ocr/output/latest/*.xlsx
                 image_ocr/output/archive/YYYYMMDD/*.xlsx

3. 병합 (data_merge/)
   ↓
   크롤링 데이터 + Google Sheets 데이터 병합
   리베이트 자동 계산
   ↓
   병합 결과 저장: data_merge/output/latest/*.xlsx
                  data_merge/output/archive/YYYYMMDD/*.xlsx

4. Google Sheets 업로드
   ↓
   병합 데이터를 Google Sheets에 업로드

5. Summary 생성 (price_summary/)
   ↓
   전체 통신사 데이터 통합 요약
   ↓
   Summary 결과 저장: price_summary/output/latest/*.csv/xlsx
                     price_summary/output/archive/YYYYMMDD/*.csv/xlsx
   ↓
   Google Sheets 업로드
```

---

## 🔧 설정

### 필수 설정 파일

```
shared_config/config/
├── google_api_key.json      # Google Sheets API 키
└── credentials.json         # Google OAuth 인증 정보
```

### 환경 변수

CLOVA OCR API 사용 시:
- `CLOVA_OCR_API_URL`: CLOVA OCR API 엔드포인트
- `CLOVA_OCR_SECRET_KEY`: CLOVA OCR Secret Key

---

## 📝 명령어 레퍼런스

### 크롤러
```bash
# KT 크롤러
python3 price_crawler/kt_crawler.py

# SK 크롤러
python3 price_crawler/sk_crawler.py

# LG 크롤러
python3 price_crawler/lg_crawler.py
```

### OCR
```bash
# 배치 모드 (테이블 인식)
python3 image_ocr/clova_ocr.py batch --table

# 단일 이미지
python3 image_ocr/clova_ocr.py single image.png
```

### 병합
```bash
# KT 병합
python3 data_merge/kt_merge.py

# SK 병합
python3 data_merge/sk_merge.py

# LG 병합
python3 data_merge/lg_merge.py

# 전체 병합
python3 data_merge/data_merge_main.py all
```

### Summary
```bash
# Summary 생성
python3 price_summary/create_summary_clean.py

# 공시지원금 정제
python3 price_summary/clean_support_sheet.py
```

---

## 🎯 주요 특징

### ✅ 완벽한 단순화
- **src/ 폴더 제거** - 복잡한 중간 폴더 없음
- **기능별 독립 폴더** - 코드와 데이터가 함께
- **직관적 구조** - 폴더명만 봐도 기능 파악

### ✅ 명확한 네이밍 (2단어)
- `price_crawler` - 가격 크롤러
- `image_ocr` - 이미지 OCR
- `data_merge` - 데이터 병합
- `price_summary` - 가격 요약
- `shared_config` - 공통 설정

### ✅ 자동화
- 체크포인트 자동 저장/복구
- Latest + Archive 자동 관리
- Google Sheets 자동 업로드
- 리베이트 자동 계산

### ✅ 안전성
- 모든 변경 전 자동 백업
- 에러 발생 시 체크포인트 복구
- 데이터 무결성 검증

---

## 🛠️ 기술 스택

- **언어**: Python 3.13
- **크롤링**: Selenium WebDriver
- **OCR**: CLOVA OCR API (Naver)
- **데이터 처리**: pandas, openpyxl
- **스토리지**: Google Sheets API, Local Excel/CSV
- **경로 관리**: PathManager (중앙화)

---

## 📂 주요 파일 설명

### price_crawler/
- `kt_crawler.py` - KT 웹사이트 크롤링
- `sk_crawler.py` - SK 웹사이트 크롤링
- `lg_crawler.py` - LG 웹사이트 크롤링
- `data/` - 크롤링 결과 저장

### image_ocr/
- `clova_ocr.py` - CLOVA OCR 메인 로직
- `extract_text_colors.py` - 텍스트 색상 추출
- `policy_calculator.py` - 요금 정책 계산
- `upload_calculated_to_sheets.py` - OCR 결과 업로드
- `output/latest/` - 최신 OCR 결과
- `output/archive/` - OCR 히스토리

### data_merge/
- `kt_merge.py` - KT 데이터 병합
- `sk_merge.py` - SK 데이터 병합
- `lg_merge.py` - LG 데이터 병합
- `data_merge_main.py` - 전체 병합 오케스트레이션
- `rebate_calculator.py` - 리베이트 계산 로직
- `output/latest/` - 최신 병합 결과
- `output/archive/` - 병합 히스토리

### price_summary/
- `create_summary_clean.py` - Summary 생성 및 업로드
- `clean_support_sheet.py` - 공시지원금 데이터 정제
- `output/latest/` - 최신 Summary 결과
- `output/archive/` - Summary 히스토리

### shared_config/
- `config/paths.py` - PathManager (중앙 경로 관리)
- `utils/google_sheets_upload.py` - Google Sheets 업로드 유틸리티

---

## 🔍 폴더 구조의 장점

### 1. 최고의 가시성
- 루트 폴더만 열어도 모든 기능이 한눈에 보임
- `ls` 명령만으로도 전체 구조 파악 가능

### 2. 완벽한 독립성
- 각 기능이 자신만의 독립적인 폴더
- data, output, logs 모두 한 곳에서 관리

### 3. 쉬운 네비게이션
```bash
cd price_crawler/     # 크롤러 관련 모든 것
cd image_ocr/         # OCR 관련 모든 것
cd data_merge/        # 병합 관련 모든 것
cd price_summary/     # Summary 관련 모든 것
```

### 4. 명확한 책임 분리
- 각 폴더가 하나의 기능만 담당
- 크기와 용도를 바로 확인 가능

---

## 💾 백업 정보

모든 중요한 변경 전 자동 백업이 `backups/` 폴더에 생성됩니다:

```
backups/
├── data_backup_before_feature_migration_20251015_120439/
├── data_backup_before_root_migration_20251015_131416/
└── src_backup_before_feature_code_20251015_132239/
```

---

## 📈 프로젝트 통계

- **총 Python 파일**: 25개
- **기능 모듈**: 4개 (크롤러, OCR, 병합, Summary)
- **데이터 크기**: ~185MB (크롤링 데이터)
- **백업 크기**: ~2.8GB

---

## 📝 개발 가이드

### PathManager 사용법

```python
from shared_config.config.paths import PathManager

pm = PathManager()

# 크롤러 경로
raw_data = pm.raw_data_dir / "kt_20251015.csv"
checkpoint = pm.checkpoint_dir / "kt_checkpoint.pkl"

# OCR 경로
ocr_input = pm.ocr_input_dir / "image.png"
ocr_latest = pm.ocr_latest_dir / "result.xlsx"

# 병합 경로
archive_path, latest_path = pm.get_merged_output_path('kt', is_rebated=False)

# Summary 경로
paths = pm.get_summary_output_path()
# paths['latest_csv'], paths['latest_excel'], paths['archive_csv'], ...

# 로그 경로
from shared_config.config.paths import get_log_path
log_file = get_log_path('kt_crawler', category='price_crawler')
```

### Latest + Archive 패턴 사용법

```python
from shared_config.config.paths import PathManager

pm = PathManager()

# 병합 파일 저장 경로 가져오기
archive_path, latest_path = pm.get_merged_output_path('kt', is_rebated=True)

# 파일 저장
df.to_excel(archive_path, index=False)

# Latest에도 자동 복사
pm.save_with_archive(archive_path, archive_path, latest_path)
```

---

## 🐛 문제 해결

### Import 오류
```bash
# Python path에 프로젝트 루트 추가
export PYTHONPATH="${PYTHONPATH}:/path/to/workspace-fee-crawler"
```

### 크롤러 중단 후 재시작
체크포인트가 자동 저장되므로 같은 명령어로 다시 실행하면 이어서 진행됩니다.

### Google Sheets API 인증 오류
1. `shared_config/config/credentials.json` 파일 확인
2. Google Cloud Console에서 API 활성화 확인
3. OAuth 2.0 클라이언트 ID 재생성

---

## 📚 참고 자료

- **Google Sheets API**: https://developers.google.com/sheets/api
- **CLOVA OCR**: https://www.ncloud.com/product/aiService/ocr
- **Selenium**: https://www.selenium.dev/documentation/

---

## 📜 변경사항 타임라인

### 2025-10-15 (전체 구조 개편)

#### Phase 0: 초기 상태 (11:19)
- GitHub 저장소 클론 완료
- Private 저장소 인증 처리
- 3,383개 파일 복사 완료

#### Phase 1: 기본 폴더 구조 정리 (11:26-11:44)
**목표**: 지저분한 폴더 구조 정리 및 PathManager 도입

**변경사항**:
- ✅ `data/outputs/merged/`, `data/outputs/summary/` 생성
- ✅ PathManager 클래스 생성 (`src/config/paths.py`)
- ✅ Latest + Archive 패턴 도입
- ✅ 9개 파일 경로 하드코딩 제거
- ✅ 811개 파일 `results/` → `data/outputs/merged/archive/` 이동
- ✅ `run.sh` 통합 실행 스크립트 생성

**결과**:
```
data/
├── outputs/
│   ├── merged/
│   │   ├── latest/
│   │   └── archive/
│   └── summary/
│       ├── latest/
│       └── archive/
├── raw/
├── checkpoints/
└── analysis/
```

#### Phase 2: 기능별 폴더 구조 (12:04-12:14)
**사용자 요청**: "각 기능별로 폴더를 만들면 안될까?"

**변경사항**:
- ✅ PathManager 재설계 (기능별 독립 폴더)
- ✅ 데이터 마이그레이션 스크립트 작성
- ✅ 9개 경로 이동
- ✅ Import 테스트 통과 (8/8)
- ✅ 백업: `data_backup_before_feature_migration_20251015_120439/`

**결과**:
```
data/
├── crawler/      # 크롤러 기능
│   ├── raw/
│   ├── checkpoints/
│   └── logs/
├── ocr/          # OCR 기능
├── merge/        # 병합 기능
└── summary/      # Summary 기능
```

#### Phase 3: 루트 레벨 기능별 폴더 (13:14)
**사용자 요청**: "루트폴더에 기능 각각의 폴더가 있으면 좋겠어"

**변경사항**:
- ✅ `data/crawler/` → `crawler/` (루트로 이동)
- ✅ `data/ocr/` → `ocr/`
- ✅ `data/merge/` → `merge/`
- ✅ `data/summary/` → `summary/`
- ✅ PathManager 경로 업데이트
- ✅ Import 테스트 통과 (8/8)
- ✅ 백업: `data_backup_before_root_migration_20251015_131416/`

**결과**:
```
workspace-fee-crawler/
├── crawler/      # 루트 레벨
├── ocr/
├── merge/
├── summary/
├── src/          # 소스 코드는 아직 분리
└── data/
```

#### Phase 4: 코드와 데이터 통합 (13:22-13:23)
**사용자 요청**: "폴더 내부가 너무 복잡한데 기능별 폴더만 있게되어야지 코드 경로 전부 수정하고"

**변경사항**:
- ✅ `src/crawlers/*.py` → `crawler/*.py` (4개 파일)
- ✅ `src/ocr/*.py` → `ocr/*.py` (6개 파일)
- ✅ `src/data_processing/*.py` → `merge/*.py` (7개 파일)
- ✅ `src/data_processing/*.py` → `summary/*.py` (3개 파일)
- ✅ `src/config/`, `src/utils/` → `shared/` (공통 코드)
- ✅ 10개 파일 import 자동 수정
- ✅ Import 테스트 통과 (12/12)
- ✅ 백업: `src_backup_before_feature_code_20251015_132239/`

**결과**:
```
각 기능 폴더 = 코드 + 데이터 + 로그

crawler/
├── kt_crawler.py     # 코드
├── sk_crawler.py
├── lg_crawler.py
├── data/             # 데이터
├── checkpoints/
└── logs/             # 로그
```

#### Phase 5: 불필요한 폴더 정리 (13:27)
**사용자 요청**: "니가 말한 파일 구조만 남도록, 필요없는 폴더 및 파일 삭제해줘"

**삭제된 폴더 (7개)**:
- ❌ `src/` (코드 이미 이동)
- ❌ `data/` (데이터 이미 이동)
- ❌ `logs/` (로그 이미 이동)
- ❌ `output/` (출력 이미 이동)
- ❌ `assets/` (사용 안함)
- ❌ `docs/` (사용 안함)
- ❌ `tests/` (사용 안함)

**백업 처리**:
- ✅ 3개 백업 폴더 → `backups/` 이동 (2.8GB)

**결과**:
```
workspace-fee-crawler/
├── crawler/
├── ocr/
├── merge/
├── summary/
├── shared/
├── analysis/
├── scripts/
├── temp/
├── backups/
├── run.sh
└── .gitignore
```

#### Phase 6: 폴더명 명확화 (13:32-13:37)
**사용자 요청**: "모든 폴더명 좀더 자세히 기능을 알 수 있게 써줘 너무 길게는 말고 단어 두개정도"

**폴더명 변경 (2단어)**:
```
crawler/  → price_crawler/     (가격 크롤러)
ocr/      → image_ocr/          (이미지 OCR)
merge/    → data_merge/         (데이터 병합)
summary/  → price_summary/      (가격 요약)
shared/   → shared_config/      (공통 설정)
```

**변경사항**:
- ✅ 5개 폴더 이름 변경
- ✅ PathManager 경로 업데이트
- ✅ 10개 Python 파일 import 수정
- ✅ `run.sh` 경로 업데이트
- ✅ `.gitignore` 경로 업데이트
- ✅ Import 테스트 통과 (12/12)

**최종 결과**:
```
workspace-fee-crawler/
├── price_crawler/         # 가격 크롤러
├── image_ocr/             # 이미지 OCR
├── data_merge/            # 데이터 병합
├── price_summary/         # 가격 요약
├── shared_config/         # 공통 설정
├── analysis/
├── scripts/
├── temp/
├── backups/
├── run.sh
├── .gitignore
└── README.md
```

### 프로젝트 구조 진화 요약

```
[Phase 0] 복잡한 src/ 기반 구조 (856개 results 파일)
   ↓
[Phase 1] data/outputs/ 중앙화 + PathManager 도입
   ↓
[Phase 2] data/ 하위 기능별 폴더 (crawler, ocr, merge, summary)
   ↓
[Phase 3] 루트 레벨 기능별 폴더 (data/ 제거)
   ↓
[Phase 4] 코드 + 데이터 통합 (src/ 제거, 각 기능에 코드 포함)
   ↓
[Phase 5] 불필요한 폴더 제거 (7개 폴더 정리)
   ↓
[Phase 6] 명확한 2단어 폴더명 (최종 완성)
```

### 핵심 성과

**폴더 구조**:
- ✅ **폴더 단순화**: 856개 파일 → 기능별 4개 폴더
- ✅ **코드 통합**: 25개 Python 파일 기능별 재배치
- ✅ **경로 중앙화**: PathManager로 모든 경로 관리
- ✅ **명확한 네이밍**: 2단어 폴더명으로 기능 즉시 파악

**데이터 관리**:
- ✅ **Latest + Archive 패턴**: 3개 기능에 적용 (OCR, Merge, Summary)
- ✅ **자동 백업**: 3개 백업 (총 2.8GB)
- ✅ **히스토리 보존**: 날짜별 아카이브

**코드 품질**:
- ✅ **Import 경로 수정**: 10개 파일 × 3회
- ✅ **검증 완료**: 12개 모듈 import 테스트 통과
- ✅ **설정 파일**: 3개 (run.sh, .gitignore, PathManager)

**변경 통계**:
- Python 파일 수정: 25개
- 폴더 이동/변경: 5개 → 6개 → 4개 (최종)
- 삭제된 폴더: 7개
- 이동된 데이터 파일: 811개
- 이동된 코드 파일: 25개
- 생성된 백업: 3개 (2.8GB)

---

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 프로젝트입니다.

---

## 👤 작성자

**Project**: Workspace Fee Crawler
**Last Updated**: 2025-10-15
**Structure Version**: 6.0 (Final - 명확한 2단어 폴더명)

---

## 🎉 마치며

이 프로젝트는 복잡한 구조에서 시작하여 **6단계의 개선**을 거쳐 현재의 **단순하고 명확한 구조**로 진화했습니다.

### 핵심 원칙

1. **기능별 독립 폴더** - 각 기능이 자신만의 코드 + 데이터 + 로그
2. **명확한 2단어 네이밍** - 폴더명만 봐도 기능 즉시 파악
3. **중앙 경로 관리** - PathManager로 모든 경로 통합 관리
4. **Latest + Archive 패턴** - 최신 파일 빠른 접근 + 히스토리 보존
5. **완벽한 검증** - 모든 변경 후 import 테스트 통과 확인

이제 누구나 폴더 구조만 봐도 프로젝트를 이해할 수 있습니다! 🎊
