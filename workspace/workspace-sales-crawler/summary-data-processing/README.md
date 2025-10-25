# Summary Data Processing

영업DB summary 시트 데이터 가공 및 처리 스크립트 모음

## 폴더 구조

```
summary-data-processing/
├── 1-sheets-merge/          # 단계 1: 시트 데이터 통합
│   ├── merge_all_to_summary.py      # daangn, naver, google → summary 통합 스크립트
│   └── daangn_to_summary.py         # daangn 단독 처리 스크립트 (레거시)
│
├── 2-data-processing/       # 단계 2: summary 데이터 가공
│   └── (앞으로 추가될 가공 스크립트)
│
└── utils/                   # 유틸리티 스크립트
    └── check_summary_structure.py   # 시트 구조 확인 도구
```

## 작업 단계

### 1단계: 시트 데이터 통합 (완료)

**목적:** daangn, naver, google 워크시트의 데이터를 하나의 summary 워크시트로 통합

**실행 파일:** `1-sheets-merge/merge_all_to_summary.py`

**처리 내용:**
- daangn, naver, google 시트에서 데이터 읽기
- 전화번호 없는 데이터 필터링
- 지역명_매장명 + 전화번호 기준 중복 제거
- 같은 전화번호가 여러 매장을 가진 경우 _1, _2... 넘버링
- 지역명_매장명 기준 오름차순 정렬
- summary 시트에 업로드

**결과:**
- 총 8,282개 행 → 중복 제거 → 1,568개 행
- 컬럼: 지역명_매장명, 매장명, 지역명, 전화번호, 링크

**실행 방법:**
```bash
cd workspace-sales-crawler/summary-data-processing/1-sheets-merge
python3 merge_all_to_summary.py
```

### 2단계: Summary 데이터 가공 (진행 예정)

**목적:** summary 워크시트의 데이터를 추가로 가공 및 분석

**처리 예정 내용:**
- (앞으로 정의될 가공 작업)

## 유틸리티 도구

### 시트 구조 확인 도구
**파일:** `utils/check_summary_structure.py`

**기능:** summary 및 daangn 워크시트의 구조와 데이터 샘플 확인

**실행 방법:**
```bash
cd workspace-sales-crawler/summary-data-processing/utils
python3 check_summary_structure.py
```

## Google Sheets 정보

**Spreadsheet ID:** `1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo`

**URL:** https://docs.google.com/spreadsheets/d/1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo/edit

**워크시트:**
- `daangn`: 당근 매장 데이터
- `naver`: 네이버 매장 데이터
- `google`: 구글 매장 데이터
- `summary`: 통합 및 가공된 최종 데이터

## 설정

**인증 파일 위치:** `../../config/google_api_key.json`

Google Sheets API 인증을 위한 서비스 계정 키 파일이 필요합니다.

## 데이터 처리 규칙

1. **전화번호 필터링**: 전화번호가 없는 데이터는 제외
2. **중복 제거**: 지역명_매장명 + 전화번호 조합이 같으면 중복으로 간주 (첫 번째 항목만 유지)
3. **넘버링 규칙**: 같은 전화번호가 여러 지역명_매장명을 가진 경우
   - 예: `서울 강남구_A매장`, `서울 서초구_A매장` → `서울 강남구_A매장_1`, `서울 서초구_A매장_2`
4. **정렬**: 지역명_매장명 기준 오름차순 (가나다순)

## 업데이트 이력

- **2024-10-20**: 초기 버전 생성
  - daangn, naver, google 시트 통합 기능 구현
  - 중복 제거 및 넘버링 로직 추가
  - 폴더 구조 정리
