# 1단계: 시트 데이터 통합

daangn, naver, google 워크시트의 데이터를 summary 워크시트로 통합하는 스크립트

## 스크립트 파일

### merge_all_to_summary.py (메인 스크립트)
**목적:** 세 개의 워크시트(daangn, naver, google)를 하나의 summary 워크시트로 통합

**처리 과정:**
1. daangn, naver, google 시트에서 데이터 읽기
2. 각 시트별로 전화번호 없는 데이터 필터링
3. 모든 데이터를 하나로 통합
4. 지역명_매장명 + 전화번호 기준 중복 제거
5. 같은 전화번호가 여러 매장을 가진 경우 _1, _2... 넘버링
6. 지역명_매장명 기준 오름차순 정렬
7. summary 시트에 업로드 (기존 데이터 덮어쓰기)

**실행 방법:**
```bash
python3 merge_all_to_summary.py
```

**출력 결과:**
- 컬럼: 지역명_매장명, 매장명, 지역명, 전화번호, 링크
- 정렬: 지역명_매장명 오름차순

---

### daangn_to_summary.py (레거시)
**목적:** daangn 워크시트만 summary로 복사하는 단일 시트 처리 스크립트

**참고:** 현재는 `merge_all_to_summary.py` 사용을 권장합니다.
