# 알림톡 메시지 템플릿

## 템플릿 등록 가이드
카카오 비즈니스 메시지 관리자 센터에서 각 템플릿을 등록해야 합니다.

---

## 1. QUOTE_REMINDER (5분 리마인더 - 고객용)

### 템플릿 코드
```
QUOTE_REMINDER
```

### 메시지 내용
```
안녕하세요, #{고객명}님!

노피 견적신청이 접수되었습니다.

견적 처리를 위해 개통정보를 입력해주세요.
⏰ 남은 시간: 5분

10분 이내 미입력 시 자동 취소되며,
24시간 동안 재신청이 제한됩니다.
```

### 버튼
- **버튼명**: 개통정보 입력하기
- **버튼 타입**: 웹 링크
- **버튼 URL**: `https://nofee.co.kr/quote/#{견적ID}/details`

### 치환 변수
| 변수명 | 설명 | 예시 |
|--------|------|------|
| #{고객명} | 고객 이름 | 홍길동 |
| #{견적ID} | 견적 고유 ID | Q20251010001 |

### 발송 시점
- 견적신청 후 **정확히 5분 경과 시**
- 상태가 `PENDING`인 경우에만 발송

---

## 2. QUOTE_CANCELLED (자동 취소 안내 - 고객용)

### 템플릿 코드
```
QUOTE_CANCELLED
```

### 메시지 내용
```
안녕하세요, #{고객명}님.

견적신청이 자동 취소되었습니다.

📌 취소 사유: 10분 이내 개통정보 미입력
📌 재신청 가능 시간: #{재신청가능시각}

동일한 조건으로 24시간 이내 재신청이 제한됩니다.
다른 상품은 즉시 신청 가능합니다.
```

### 버튼
- **버튼명**: 다른 상품 보기
- **버튼 타입**: 웹 링크
- **버튼 URL**: `https://nofee.co.kr/products`

### 치환 변수
| 변수명 | 설명 | 예시 |
|--------|------|------|
| #{고객명} | 고객 이름 | 홍길동 |
| #{재신청가능시각} | 차단 해제 시각 | 2025.10.11 14:30 |

### 발송 시점
- 견적신청 후 **10분 경과 시**
- 상태가 `PENDING`인 경우 (개통정보 미입력)

---

## 3. QUOTE_CONFIRMED (견적 확인 - 고객용)

### 템플릿 코드
```
QUOTE_CONFIRMED
```

### 메시지 내용
```
안녕하세요, #{고객명}님!

개통정보가 정상적으로 접수되었습니다. ✅

담당 판매점에서 곧 연락드릴 예정입니다.
빠른 상담을 위해 전화를 받아주세요!

📞 예상 연락 시간: 10분 이내
```

### 버튼
- 버튼 없음 (정보성 메시지)

### 치환 변수
| 변수명 | 설명 | 예시 |
|--------|------|------|
| #{고객명} | 고객 이름 | 홍길동 |

### 발송 시점
- 개통정보 입력 완료 후
- 10분 체크포인트에서 상태가 `COMPLETED`인 경우

---

## 4. SALES_NEW_QUOTE (신규 견적 알림 - 판매점용)

### 템플릿 코드
```
SALES_NEW_QUOTE
```

### 메시지 내용
```
[노피] 신규 견적이 접수되었습니다.

👤 고객명: #{고객명}
📞 연락처: #{전화번호}
📦 상품: #{상품명}
🏢 통신사: #{통신사}

✅ 개통정보 입력 완료
지금 바로 상담 진행해주세요!
```

### 버튼
- **버튼명**: 견적 상세보기
- **버튼 타입**: 웹 링크
- **버튼 URL**: `https://sales.nofee.co.kr/quotes/#{견적ID}`

### 치환 변수
| 변수명 | 설명 | 예시 |
|--------|------|------|
| #{고객명} | 고객 이름 | 홍길동 |
| #{전화번호} | 고객 전화번호 | 010-1234-5678 |
| #{상품명} | 선택한 상품명 | 5G 프리미어 에센셜 |
| #{통신사} | 통신사명 | SKT |
| #{견적ID} | 견적 고유 ID | Q20251010001 |

### 발송 시점
- **중요**: 10분 내에 개통정보 입력 완료된 경우에만 발송
- 10분 체크포인트에서 상태가 `COMPLETED`인 경우

---

## 5. QUOTE_BLOCKED (재신청 차단 안내 - 고객용, 선택)

### 템플릿 코드
```
QUOTE_BLOCKED
```

### 메시지 내용
```
안녕하세요, #{고객명}님.

동일한 조건으로 재신청이 제한되어 있습니다.

📌 제한 사유: 이전 견적신청 미완료
📌 재신청 가능 시간: #{재신청가능시각}

다른 상품은 즉시 신청 가능합니다.
```

### 버튼
- **버튼명**: 다른 상품 보기
- **버튼 타입**: 웹 링크
- **버튼 URL**: `https://nofee.co.kr/products`

### 치환 변수
| 변수명 | 설명 | 예시 |
|--------|------|------|
| #{고객명} | 고객 이름 | 홍길동 |
| #{재신청가능시각} | 차단 해제 시각 | 2025.10.11 14:30 |

### 발송 시점
- 차단된 상태에서 재신청 시도 시 (선택적)
- API 응답으로 에러 메시지 전달로 대체 가능

---

## 개발 구현 예시

### Node.js (카카오 알림톡 API)

```javascript
// 알림톡 발송 함수
async function sendAlimtalk(phone, templateCode, variables) {
  const apiUrl = 'https://alimtalk-api.bizmsg.kr/v2/sender/send';

  const requestBody = {
    senderKey: process.env.KAKAO_SENDER_KEY,
    templateCode: templateCode,
    recipientList: [
      {
        recipientNo: phone,
        templateParameter: variables,
        buttons: getButtons(templateCode, variables)
      }
    ]
  };

  const response = await axios.post(apiUrl, requestBody, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.KAKAO_API_TOKEN}`
    }
  });

  // 로그 저장
  await logAlimtalk({
    quote_id: variables.견적ID,
    template_code: templateCode,
    recipient_phone: phone,
    status: response.data.success ? 'SUCCESS' : 'FAILED'
  });

  return response.data;
}

// 버튼 설정
function getButtons(templateCode, variables) {
  const buttonMap = {
    'QUOTE_REMINDER': [
      {
        name: '개통정보 입력하기',
        type: 'WL',
        url_mobile: `https://nofee.co.kr/quote/${variables.견적ID}/details`,
        url_pc: `https://nofee.co.kr/quote/${variables.견적ID}/details`
      }
    ],
    'QUOTE_CANCELLED': [
      {
        name: '다른 상품 보기',
        type: 'WL',
        url_mobile: 'https://nofee.co.kr/products',
        url_pc: 'https://nofee.co.kr/products'
      }
    ],
    'SALES_NEW_QUOTE': [
      {
        name: '견적 상세보기',
        type: 'WL',
        url_mobile: `https://sales.nofee.co.kr/quotes/${variables.견적ID}`,
        url_pc: `https://sales.nofee.co.kr/quotes/${variables.견적ID}`
      }
    ]
  };

  return buttonMap[templateCode] || [];
}

// 사용 예시
await sendAlimtalk('010-1234-5678', 'QUOTE_REMINDER', {
  고객명: '홍길동',
  견적ID: 'Q20251010001'
});
```

---

## 테스트 체크리스트

### 고객 알림톡 테스트
- [ ] QUOTE_REMINDER: 5분 경과 시 정상 발송
- [ ] QUOTE_CANCELLED: 10분 미입력 시 정상 발송
- [ ] QUOTE_CONFIRMED: 개통정보 입력 완료 시 정상 발송
- [ ] 버튼 링크 클릭 시 정상 이동
- [ ] 치환 변수 정상 표시

### 판매점 알림톡 테스트
- [ ] SALES_NEW_QUOTE: 10분 내 완료 시만 발송
- [ ] 10분 초과 완료 건은 발송 안 됨
- [ ] 미입력 취소 건은 발송 안 됨
- [ ] 고객 정보 정확히 표시

---

## 주의사항

1. **템플릿 검수**: 카카오 비즈니스 메시지에서 사전 검수 필수
2. **발송 제한**: 광고성 메시지 아님을 명확히 표시
3. **개인정보**: 전화번호 마스킹 처리 (예: 010-1234-****)
4. **발송 시간**: 야간 (21:00~08:00) 발송 지양
5. **재시도**: 발송 실패 시 최대 3회 재시도
