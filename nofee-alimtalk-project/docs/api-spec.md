# API 명세서

## 1. 견적신청 생성

### Endpoint
```
POST /api/quotes
```

### Request Body
```json
{
  "phone": "010-1234-5678",
  "customer_name": "홍길동",
  "product_id": 123,
  "user_info": {
    "carrier": "SKT",
    "plan_type": "5G 프리미어 에센셜"
  }
}
```

### Response (201 Created)
```json
{
  "quote_id": "Q20251010001",
  "status": "PENDING",
  "created_at": "2025-10-10T14:30:00Z",
  "expires_at": "2025-10-10T14:40:00Z"
}
```

### Response (403 Blocked)
```json
{
  "error": "BLOCKED",
  "message": "24시간 이내 동일 조건 재신청 불가",
  "blocked_until": "2025-10-11T14:30:00Z"
}
```

---

## 2. 개통정보 입력

### Endpoint
```
PUT /api/quotes/{quote_id}/details
```

### Request Body
```json
{
  "details": {
    "id_number": "950101-1******",
    "address": "서울시 강남구...",
    "email": "example@email.com",
    "delivery_preference": "택배",
    "additional_notes": "오후 배송 희망"
  }
}
```

### Response (200 OK)
```json
{
  "quote_id": "Q20251010001",
  "status": "COMPLETED",
  "completed_at": "2025-10-10T14:35:00Z",
  "message": "개통정보가 정상적으로 접수되었습니다"
}
```

### Response (410 Expired)
```json
{
  "error": "EXPIRED",
  "message": "견적신청이 만료되었습니다",
  "expired_at": "2025-10-10T14:40:00Z"
}
```

---

## 3. 견적 상태 조회

### Endpoint
```
GET /api/quotes/{quote_id}
```

### Response (200 OK)
```json
{
  "quote_id": "Q20251010001",
  "status": "PENDING",
  "customer_phone": "010-1234-5678",
  "customer_name": "홍길동",
  "product_id": 123,
  "created_at": "2025-10-10T14:30:00Z",
  "expires_at": "2025-10-10T14:40:00Z",
  "time_remaining_seconds": 420
}
```

---

## 4. 판매점 DB 전송 (내부 API)

### Endpoint
```
POST /api/sales/quotes
```

### Request Body
```json
{
  "quote_id": "Q20251010001",
  "customer_phone": "010-1234-5678",
  "customer_name": "홍길동",
  "product_id": 123,
  "details": {
    "id_number": "950101-1******",
    "address": "서울시 강남구...",
    "email": "example@email.com"
  },
  "completed_at": "2025-10-10T14:35:00Z"
}
```

### Response (201 Created)
```json
{
  "sales_quote_id": "SQ20251010001",
  "status": "CREATED",
  "assigned_sales_rep": "김판매",
  "message": "판매점에 성공적으로 전달되었습니다"
}
```

---

## 5. 차단 여부 확인 (선택)

### Endpoint
```
POST /api/blocklist/check
```

### Request Body
```json
{
  "phone": "010-1234-5678",
  "product_id": 123
}
```

### Response (200 OK - 차단 없음)
```json
{
  "blocked": false,
  "message": "신청 가능합니다"
}
```

### Response (200 OK - 차단 중)
```json
{
  "blocked": true,
  "blocked_until": "2025-10-11T14:30:00Z",
  "time_remaining_seconds": 86400,
  "message": "24시간 이내 동일 조건 재신청 불가"
}
```

---

## 상태 코드 정리

| 코드 | 설명 |
|------|------|
| 200 | 정상 처리 |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 403 | 차단됨 (재신청 제한) |
| 404 | 견적을 찾을 수 없음 |
| 410 | 만료됨 (10분 초과) |
| 500 | 서버 오류 |

---

## 에러 응답 형식

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "error": "ERROR_CODE",
  "message": "사용자에게 보여질 에러 메시지",
  "details": {
    // 추가 상세 정보 (선택)
  }
}
```
