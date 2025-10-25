# 재무제표 - 김선호 자본금 정산 관련 파일

## 📁 폴더 구조

```
재무제표/
├── checks/          # 데이터 확인 스크립트 (26개)
├── verification/    # 검증 및 추적 스크립트
├── docs/           # 문서 (계산식, 거래내역 등)
└── README.md       # 이 파일
```

---

## 📂 checks/ - 데이터 확인 스크립트

### 통장 잔고 관련
- `check-balance.js` - 통장 잔고 확인
- `check-raw-balance.js` - raw_data 잔고 확인

### 김선호 관련
- `check-kim-sunho.js` - 김선호 거래 내역 확인
- `check-kimsh-borrowing.js` - 김선호 차입금 확인

### 송호빈 관련
- `check-songhobin-out.js` - 송호빈 출금 내역 확인

### 자본금 관련
- `check-capital-deposit.js` - 자본금 입금 확인
- `check-capital-flow.js` - 자본금 흐름 확인

### 차입금 관련
- `check-borrowings.js` - 차입금 내역 확인

### 비용 관련
- `check-expenses.js` - 비용 내역 확인
- `check-total-expenses.js` - 총 비용 확인
- `check-office.js` - 사무실 비용 확인
- `check-office-expense.js` - 사무실 비용 상세

### 매출 관련
- `check-revenue-expense.js` - 매출/비용 확인

### 기타 거래
- `check-others.js` - 기타 거래 확인
- `check-10m-transactions.js` - 1천만원 거래 확인
- `check-interest.js` - 이자 확인
- `check-naverpay.js` - 네이버페이 거래 확인

### 데이터 시트 관련
- `check-raw-data.js` - raw_data 시트 확인
- `check-clear-data.js` - clear 시트 확인
- `check-summary-detail.js` - Summary 시트 상세
- `check-summary-full.js` - Summary 시트 전체

### 특수 확인
- `check-aws-test.js` - AWS 테스트 거래 확인
- `check-name-normalization.js` - 이름 정규화 확인
- `check-sheet-formatting.js` - 시트 포맷팅 확인

---

## 📂 verification/ - 검증 및 추적 스크립트

### 전체 검증
- `verify-all.js` - 전체 재무제표 정합성 검증
  - raw_data vs clear vs Summary 일치 여부
  - 매출, 판관비, 자본금, 통장 잔고 검증
  - 8개 항목 자동 검증

### 계산 추적
- `trace-office-calculation.js` - 사무실 비용 계산 과정 추적
  - raw_data → clear → Summary 단계별 확인
  - 개인 계약금 포함 여부 검증

---

## 📂 docs/ - 문서

### 김선호 관련 문서
- `김선호_개인거래내역.md` - 개인 거래 내역 정리
  - 2025.05.23 사무실 계약금 1,000,000원 (김선호→박환성)
  - 노피 통장 거래 전체 내역
  - 회계 처리 옵션

- `김선호_자본금_계산식.md` - 자본금 계산 및 정산 방안
  - 통장 거래: 1,150,000원
  - 개인 지출: 1,000,000원
  - 총 자본금: 2,150,000원
  - 정산 방법: 노피→김선호 1,000,000원, 김선호→노피 550,000원
  - 회계 분개 포함

---

## 🎯 주요 파일 사용 가이드

### 1. 전체 검증이 필요할 때
```bash
node 재무제표/verification/verify-all.js
```

### 2. 김선호 거래 확인
```bash
node 재무제표/checks/check-kim-sunho.js
```

### 3. 사무실 비용 계산 추적
```bash
node 재무제표/verification/trace-office-calculation.js
```

### 4. 통장 잔고 확인
```bash
node 재무제표/checks/check-balance.js
```

---

## 📊 최종 결론 (2025.10.22)

### 현재 상황
- **김선호 통장 자본금**: 1,150,000원
- **김선호 개인 지출**: 1,000,000원 (2025.05.23 사무실 계약금)
- **김선호 총 자본금**: 2,150,000원

### 목표
- **3명 균등 자본금**: 각 1,700,000원

### 정산 방법 (투명 방식)
```
1. 노피 → 김선호: 1,000,000원 (개인 지출 보전)
2. 김선호 → 노피: 550,000원 (초과분 반환)
```

### 정산 후
- **김선호 자본금**: 1,700,000원 ✅
- **통장 잔고**: 4,553,622원
- **3명 모두 동일**: 1,700,000원 ✅

---

## 📝 재무제표 반영 상태

### process-financial-data-v3.js
- ✅ 비용: 사무실 계약금 1,000,000원 추가
- ✅ 자본금: 김선호 1,000,000원 추가
- ✅ 재무제표 주석: "사업 운영비 - 사무실 (개인지출)" 항목 표시

### Summary 시트
```
[판매비와관리비 상세]
  사업 운영비 - 사무실 (개인지출)    1,000,000원 (김선호→박환성 2025.05.23, 정산필요)

자본금 - 김선호:                    2,150,000원
```

---

**보관일**: 2025.10.22
**목적**: 김선호 자본금 정산 관련 모든 검증 및 계산 과정 기록
