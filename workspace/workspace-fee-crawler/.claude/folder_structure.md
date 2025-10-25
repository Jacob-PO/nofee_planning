# 📁 Workspace Fee Crawler - 폴더 구조

## 기능별 폴더 구조 (2025-10-15 개편)

사용자 요청에 따라 **기능별로 독립적인 폴더 구조**로 변경되었습니다.

```
workspace-fee-crawler/
├── data/                    # 모든 데이터 (기능별로 분리)
│   │
│   ├── crawler/            # 🔍 크롤러 기능
│   │   ├── raw/           # 크롤링 원본 데이터 (CSV)
│   │   ├── checkpoints/   # 크롤링 체크포인트 (PKL)
│   │   └── logs/          # 크롤러 로그
│   │
│   ├── ocr/               # 📊 OCR 기능
│   │   ├── input/         # OCR 입력 이미지
│   │   ├── output/        # OCR 결과
│   │   │   ├── latest/    # 최신 파일 (항상 최신 버전)
│   │   │   └── archive/   # 날짜별 아카이브 (YYYYMMDD/)
│   │   └── logs/          # OCR 로그
│   │
│   ├── merge/             # 🔀 병합 기능
│   │   ├── output/        # 병합 결과 (Excel)
│   │   │   ├── latest/    # 최신 파일 (kt_merged_latest.xlsx 등)
│   │   │   └── archive/   # 날짜별 아카이브 (YYYYMMDD/)
│   │   └── logs/          # 머지 로그
│   │
│   ├── summary/           # 📋 Summary 기능
│   │   ├── output/        # Summary 결과 (CSV, Excel)
│   │   │   ├── latest/    # 최신 파일
│   │   │   └── archive/   # 날짜별 아카이브 (YYYYMMDD/)
│   │   └── logs/          # Summary 로그
│   │
│   ├── analysis/          # 📈 분석 결과 (공통)
│   │   └── unmatched_products.csv
│   │
│   └── temp/              # 임시 파일
│
├── src/                    # 소스 코드
│   ├── config/            # 설정 파일
│   │   ├── paths.py      # ⭐ PathManager (중앙 경로 관리)
│   │   ├── google_api_key.json
│   │   └── credentials.json
│   │
│   ├── crawlers/          # 크롤러 모듈
│   │   ├── kt_crawler.py
│   │   ├── sk_crawler.py
│   │   ├── lg_crawler.py
│   │   └── all_crawler.py
│   │
│   ├── ocr/               # OCR 모듈
│   │   ├── clova_ocr.py
│   │   ├── extract_text_colors.py
│   │   ├── policy_calculator.py
│   │   └── upload_calculated_to_sheets.py
│   │
│   ├── data_processing/   # 데이터 처리 모듈
│   │   ├── kt_merge.py
│   │   ├── sk_merge.py
│   │   ├── lg_merge.py
│   │   ├── data_merge_main.py
│   │   ├── create_summary_clean.py
│   │   ├── rebate_calculator.py
│   │   └── clean_support_sheet.py
│   │
│   └── utils/             # 유틸리티
│       └── google_sheets_upload.py
│
├── scripts/               # 유틸리티 스크립트
│   ├── analysis/         # 분석 스크립트
│   ├── check/            # 검증 스크립트
│   ├── debug/            # 디버깅 도구
│   └── utils/            # 마이그레이션 등
│
├── run.sh                 # ⭐ 통합 실행 스크립트 (메뉴 방식)
├── .gitignore
└── README.md
```

## 주요 특징

### 1. 기능별 독립 구조
- **크롤러**, **OCR**, **병합**, **Summary** 각각이 독립적인 폴더
- 각 기능마다 자신의 `output/`, `logs/` 폴더 보유
- 기능 추가/제거가 쉬움

### 2. Latest + Archive 패턴
- `latest/`: 항상 최신 파일 (쉬운 접근)
- `archive/YYYYMMDD/`: 날짜별 히스토리 보존

### 3. 중앙 경로 관리 (PathManager)
- 모든 경로는 `src/config/paths.py`에서 관리
- 하드코딩 없음, 유지보수 용이

### 4. 편리한 실행 스크립트
- `./run.sh`: 인터랙티브 메뉴로 모든 기능 실행

## 경로 사용 예시

### Python 코드에서 경로 사용
```python
from src.config.paths import PathManager

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
from src.config.paths import get_log_path
log_file = get_log_path('kt_crawler', category='crawler')
```

## 마이그레이션 내역

### 변경 사항 (2025-10-15)
- ✅ `data/raw` → `data/crawler/raw`
- ✅ `data/checkpoints` → `data/crawler/checkpoints`
- ✅ `logs/crawler` → `data/crawler/logs`
- ✅ `logs/ocr` → `data/ocr/logs`
- ✅ `data/outputs/merged` → `data/merge/output`
- ✅ `logs/merge` → `data/merge/logs`
- ✅ `data/outputs/summary` → `data/summary/output`
- ✅ `logs/general` → `data/summary/logs`
- ✅ `data/analysis` (위치 유지)

### 백업
모든 변경 전 자동 백업 생성:
- `data_backup_before_feature_migration_YYYYMMDD_HHMMSS/`

## 장점

### ✅ 명확한 구조
- 폴더만 봐도 어떤 기능인지 바로 알 수 있음
- 각 기능이 완전히 독립적

### ✅ 쉬운 관리
- 기능별로 독립적으로 관리 가능
- 로그, 출력이 한 곳에 모여있음

### ✅ 확장 용이
- 새 기능 추가 시 새 폴더만 만들면 됨
- 기존 기능에 영향 없음

### ✅ 빠른 접근
- `latest/` 폴더로 항상 최신 파일에 바로 접근
- glob/sort 필요 없음

## 참고

- 전체 프로젝트 문맥: [.claude/project_context.json](.claude/project_context.json)
- 대화 기록: [.claude/conversation_log.md](.claude/conversation_log.md)
