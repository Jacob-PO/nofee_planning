# Scripts - Nofee 재무 관리 스크립트

## 📁 현재 스크립트 목록 (15개)

### 🔥 주요 스크립트 (재무 처리)

#### `process-financial-data-v3.js` ⭐ **현재 사용 중**
- **용도**: raw_data → clear → Summary 재무제표 생성
- **기능**:
  - 거래 내역 자동 분류 (매출/비용/기타)
  - 한국 재무제표 기준 계정과목 분류
  - 김선호 개인 계약금 1,000,000원 자동 반영
  - Summary 시트에 손익계산서 생성
- **실행**: `node scripts/process-financial-data-v3.js`

#### `process-financial-data-v2.js`
- **용도**: 이전 버전 (백업)
- **상태**: 사용 안 함

#### `process-financial-data.js`
- **용도**: 최초 버전 (백업)
- **상태**: 사용 안 함

---

### 📊 분석 스크립트

#### `analyze-raw-data.js`
- **용도**: raw_data 기본 분석
- **기능**: 거래 내역 통계, 입출금 합계

#### `create-financial-database.js`
- **용도**: 재무 데이터베이스 생성
- **기능**: 구조화된 재무 DB 구축

---

### 📄 Notion 연동 스크립트

#### `sync-to-notion.js`
- **용도**: 데이터를 Notion에 동기화
- **실행**: `npm run sync-to-notion`

#### `create-financial-statement-notion.js`
- **용도**: Notion에 재무제표 페이지 생성

#### `restructure-notion-pages.js`
- **용도**: Notion 페이지 구조 재정리
- **실행**: `npm run restructure-notion`

#### `create-page.js`
- **용도**: Notion 페이지 생성
- **실행**: `npm run create-page`

#### `update-page.js`
- **용도**: Notion 페이지 업데이트

#### `get-page.js`
- **용도**: Notion 페이지 조회

#### `list-pages.js`
- **용도**: Notion 페이지 목록 조회
- **실행**: `npm run list-pages`

#### `sync-api-docs.js`
- **용도**: API 문서 동기화
- **실행**: `npm run sync-api-docs`

#### `update-homepage.js`
- **용도**: 홈페이지 업데이트
- **실행**: `npm run update-homepage`

---

### 🔍 유틸리티

#### `list-sheets.js`
- **용도**: Google Sheets 목록 조회

---

## 📦 재무제표 폴더

검증 및 확인용 스크립트는 `../재무제표/` 폴더로 이동되었습니다:
- `재무제표/checks/` - 24개 데이터 확인 스크립트
- `재무제표/verification/` - 2개 검증 스크립트
- `재무제표/docs/` - 2개 문서

자세한 내용은 [재무제표/README.md](../재무제표/README.md) 참조

---

## 🎯 주요 사용 시나리오

### 1. 재무제표 생성 및 업데이트
```bash
node scripts/process-financial-data-v3.js
```

### 2. Notion에 동기화
```bash
npm run sync-to-notion
```

### 3. 전체 데이터 검증
```bash
node 재무제표/verification/verify-all.js
```

### 4. 김선호 거래 확인
```bash
node 재무제표/checks/check-kim-sunho.js
```

---

## 📝 최근 주요 변경사항 (2025.10.22)

### process-financial-data-v3.js
1. **개인 계약금 반영** (650-657번 줄)
   - 김선호 개인 지출 1,000,000원 자동 추가
   - 사업 운영비 - 사무실에 포함

2. **자본금 조정** (752-763번 줄)
   - 김선호 자본금에 개인 계약금 1,000,000원 추가
   - 차입금상환 처리 개선

3. **재무제표 주석** (794번 줄)
   - 판매비와관리비 상세에 개인 지출 항목 표시
   - "사업 운영비 - 사무실 (개인지출)" 라인 추가

---

## 🔗 관련 파일

- `../config/google_api_key.json` - Google Sheets API 인증
- `../재무제표/docs/김선호_자본금_계산식.md` - 정산 계산식
- `../재무제표/docs/김선호_개인거래내역.md` - 개인 거래 내역

---

**최종 업데이트**: 2025.10.22
