# 휴대폰 성지 카드뉴스 제작 가이드

## 프로젝트 개요
인스타그램용 카드뉴스 콘텐츠 (1000x1000px 정사각형)
전국의 숨겨진 휴대폰 성지 매장을 소개하는 8장 구성

## 파일 구조
```
phone-shops-cardnews/
├── index.html          # 메인 카드뉴스 파일
├── index_old.html      # 이전 버전 백업
└── README.md          # 이 문서
```

## 카드 구성 (총 8장)

### Card 1: 커버
- 배경: 다크 그라데이션 (#000000 → #1a1a2e)
- 메인 카피: "커뮤니티 난리난 전국 성지 6경"
- 서브 카피 (2줄, 28px):
  - "대리점 직원도 몰래 사러 가는 곳"
  - "오픈챗에서만 도는 전설의 리스트"
- 브랜딩: 우측 하단 iMessage 스타일 (프로필 + 말풍선)

### Card 2-7: 매장 소개 (6개)
각 카드 구조:
```
1. 해시태그 2개 (상단)
2. 매장명 (68px, 굵게)
3. 정보 라인: 지역 | 특징1 | 특징2
4. 제품 이미지 (400x400px)
5. 제품명 (42px)
6. 가격: 정가 → 할인가 (숫자만 토스블루 #3182F6)
7. 브랜딩 말풍선 (우측 하단)
```

**현재 등록된 매장:**
1. 띵동폰 동대문점 - 아이폰 17
2. 조이모바일 - 갤럭시 Z 폴드7
3. 성공모바일 - 아이폰 16 Pro
4. 지산모바일 - 갤럭시 S25
5. 용인휴대폰성지 - 갤럭시 S25 Ultra
6. 폰여기요 - 갤럭시 Z 플립7

### Card 8: 브랜드 마무리
- 배경: 보라색 그라데이션 (#667eea → #764ba2)
- 로고 + 메인 메시지
- CTA: "우리동네 휴대폰 성지 노피가 찾아드려요"
- 지역 태그: 서울, 경기, 인천, 부산, 대구, 전국

## 디자인 시스템

### 폰트
```css
font-family: 'SUIT Variable', sans-serif;
/* CDN: https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/variable/woff2/SUIT-Variable.css */
```

### 컬러 팔레트
```css
/* 배경 */
커버: #000000 → #1a1a2e (그라데이션)
매장카드: #FFFFFF
마무리: #667eea → #764ba2 (그라데이션)

/* 강조색 */
골드: #FFD700
토스블루: #3182F6
iMessage블루: #007AFF

/* 태그 */
배경: #FFF4E0
텍스트: #D97706
```

### 타이포그래피
```css
커버 메인: 88px, 900 weight
매장명: 68px, 900 weight
제품명: 42px, 900 weight
가격(할인후): 72px, 900 weight
가격(할인전): 36px, 900 weight (취소선)
태그: 17px, 700 weight
정보라인: 24px, 700 weight
```

### 브랜딩 요소
```css
/* iMessage 스타일 말풍선 */
위치: Card 1 - bottom: 70px, right: 40px
     Card 2-7 - bottom: 160px, right: 100px

프로필: 48px 원형, 화이트 배경
말풍선: #007AFF 배경, 둥근 모서리
텍스트: "동네성지 찾아줘요, 노피"
```

## 새 매장 추가 방법

### 1. CSS 스타일 추가
```css
/* Card N: 동일한 스타일 */
.card-N {
    background: #FFFFFF;
    padding: 70px;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.card-N .brand-footer {
    position: absolute;
    bottom: 160px;
    right: 100px;
    transform: none;
}

.card-N .profile-image {
    display: none;
}

.card-N .imessage-bubble {
    background: #007AFF;
    opacity: 0.95;
    border-radius: 20px 20px 20px 4px;
}
```

### 2. HTML 카드 추가
```html
<!-- Card N: 매장명 -->
<div class="card card-N">
    <div>
        <div class="tags">
            <div class="tag">#키워드1</div>
            <div class="tag">#키워드2</div>
        </div>

        <h2 class="store-title">매장명</h2>

        <div class="store-info-line">
            <span>지역명</span>
            <span class="info-divider">|</span>
            <span>특징1</span>
            <span class="info-divider">|</span>
            <span>특징2</span>
        </div>

        <div class="product-image-section">
            <img src="제품이미지URL" alt="제품명">
        </div>

        <div class="product-name-title">제품명</div>

        <div class="price-section">
            <div class="price-before">정가</div>
            <div class="price-arrow">→</div>
            <div class="price-after"><span class="price-number">숫자</span>만원</div>
        </div>
    </div>

    <!-- 브랜드 푸터 -->
    <div class="brand-footer">
        <div class="profile-image">
            <img src="https://admin.nofee.team/image/company/logo.svg" alt="노피">
        </div>
        <div class="imessage-bubble">동네성지 찾아줘요, 노피</div>
    </div>
</div>
```

### 3. 후기 기반 태그 추출 가이드
후기에서 가장 많이 언급된 키워드 2개를 해시태그로 만들기

예시:
- 친절 → #친절_최고
- 케이스 증정 → #케이스필름증정
- 투명한 가격 → #시세표_투명
- 말장난 없음 → #말장난_없음

## 디자인 컨셉

### 커버 전략
- "커뮤니티 입소문" 느낌 강조
- 비밀 정보 공유하는 느낌
- FOMO(놓치면 안 되는) 자극
- 인스타그래머블한 카피

### 매장 카드 전략
- 토스 스타일: 심플, 볼드, 클린
- 가격 임팩트 극대화 (숫자만 컬러)
- 정사각형 최적화 레이아웃
- 실제 후기 기반 태그로 신뢰성

### 브랜딩 전략
- 비침습적 브랜딩 (iMessage 스타일)
- 프랜차이즈 느낌 제거
- 커뮤니티 친화적 톤앤매너

## 이미지 소스
- 제품 이미지: https://image.nofee.team/product-group/phone/
- 로고: https://admin.nofee.team/image/company/logo.svg

## 브라우저에서 확인
```bash
open index.html
```

## 수정 시 주의사항
1. 카드는 반드시 1000x1000px 유지
2. 폰트는 SUIT Variable 사용 (CDN 로드 필수)
3. 가격 숫자만 토스블루 적용 (#3182F6)
4. 브랜딩 말풍선 위치 일관성 유지
5. 태그는 후기 기반으로 실제 특징 반영

## 버전 히스토리
- v1.0 (2025-10-10): 초기 버전, 6개 매장 카드뉴스 완성
