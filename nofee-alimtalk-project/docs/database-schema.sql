-- ============================================
-- 노피 알림톡 알고리즘 데이터베이스 스키마
-- ============================================

-- 1. 견적신청 메인 테이블
CREATE TABLE quotes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    quote_id VARCHAR(50) UNIQUE NOT NULL COMMENT '견적 고유 ID (예: Q20251010001)',
    customer_phone VARCHAR(20) NOT NULL COMMENT '고객 전화번호',
    customer_name VARCHAR(100) COMMENT '고객명',
    product_id INT NOT NULL COMMENT '상품 ID',
    status ENUM('PENDING', 'COMPLETED', 'CANCELLED') DEFAULT 'PENDING' COMMENT '견적 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '신청 시각',
    completed_at TIMESTAMP NULL COMMENT '개통정보 입력 완료 시각',
    cancelled_at TIMESTAMP NULL COMMENT '취소 시각',
    expires_at TIMESTAMP NULL COMMENT '만료 시각 (created_at + 10분)',
    details JSON NULL COMMENT '개통정보 상세 (입력 완료 시)',

    -- 인덱스
    INDEX idx_status_created (status, created_at),
    INDEX idx_phone_product (customer_phone, product_id),
    INDEX idx_quote_id (quote_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='견적신청 메인 테이블';

-- 2. 재신청 차단 테이블
CREATE TABLE quote_blocklist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_phone VARCHAR(20) NOT NULL COMMENT '고객 전화번호',
    product_id INT NOT NULL COMMENT '상품 ID',
    blocked_until TIMESTAMP NOT NULL COMMENT '차단 해제 시각 (24시간 후)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '차단 등록 시각',
    quote_id VARCHAR(50) NULL COMMENT '취소된 견적 ID (참고용)',

    -- 유니크 키: 동일 전화번호 + 상품 조합은 하나만
    UNIQUE KEY unique_block (customer_phone, product_id),
    INDEX idx_blocked_until (blocked_until),
    INDEX idx_phone (customer_phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='재신청 차단 테이블';

-- 3. 알림톡 발송 로그 테이블
CREATE TABLE alimtalk_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    quote_id VARCHAR(50) NOT NULL COMMENT '견적 ID',
    template_code VARCHAR(50) NOT NULL COMMENT '템플릿 코드 (QUOTE_REMINDER, QUOTE_CANCELLED 등)',
    recipient_phone VARCHAR(20) NOT NULL COMMENT '수신자 전화번호',
    recipient_type ENUM('CUSTOMER', 'SALES') NOT NULL COMMENT '수신자 타입',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '발송 시각',
    status ENUM('SUCCESS', 'FAILED') DEFAULT 'SUCCESS' COMMENT '발송 상태',
    error_message TEXT NULL COMMENT '실패 시 에러 메시지',
    message_content TEXT NULL COMMENT '발송된 메시지 내용 (백업용)',

    INDEX idx_quote_id (quote_id),
    INDEX idx_recipient_phone (recipient_phone),
    INDEX idx_sent_at (sent_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='알림톡 발송 로그';

-- 4. 판매점 견적 테이블 (판매점 DB)
CREATE TABLE sales_quotes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sales_quote_id VARCHAR(50) UNIQUE NOT NULL COMMENT '판매점 견적 ID (예: SQ20251010001)',
    quote_id VARCHAR(50) NOT NULL COMMENT '원본 견적 ID',
    customer_phone VARCHAR(20) NOT NULL COMMENT '고객 전화번호',
    customer_name VARCHAR(100) COMMENT '고객명',
    product_id INT NOT NULL COMMENT '상품 ID',
    details JSON NOT NULL COMMENT '개통정보 상세',
    assigned_sales_rep VARCHAR(100) NULL COMMENT '담당 판매사원',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '접수 시각',
    contacted_at TIMESTAMP NULL COMMENT '고객 연락 완료 시각',
    status ENUM('NEW', 'CONTACTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') DEFAULT 'NEW' COMMENT '처리 상태',

    INDEX idx_quote_id (quote_id),
    INDEX idx_customer_phone (customer_phone),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='판매점 견적 테이블';

-- ============================================
-- 샘플 데이터 (개발/테스트용)
-- ============================================

-- 샘플 견적신청 1: 완료 상태
INSERT INTO quotes (quote_id, customer_phone, customer_name, product_id, status, created_at, completed_at, expires_at, details) VALUES
('Q20251010001', '010-1234-5678', '홍길동', 123, 'COMPLETED',
 '2025-10-10 14:30:00', '2025-10-10 14:35:00', '2025-10-10 14:40:00',
 JSON_OBJECT('id_number', '950101-1******', 'address', '서울시 강남구', 'email', 'hong@example.com'));

-- 샘플 견적신청 2: 취소 상태
INSERT INTO quotes (quote_id, customer_phone, customer_name, product_id, status, created_at, cancelled_at, expires_at) VALUES
('Q20251010002', '010-9876-5432', '김철수', 124, 'CANCELLED',
 '2025-10-10 15:00:00', '2025-10-10 15:10:00', '2025-10-10 15:10:00');

-- 샘플 차단 기록
INSERT INTO quote_blocklist (customer_phone, product_id, blocked_until, quote_id) VALUES
('010-9876-5432', 124, DATE_ADD(NOW(), INTERVAL 24 HOUR), 'Q20251010002');

-- 샘플 알림톡 로그
INSERT INTO alimtalk_logs (quote_id, template_code, recipient_phone, recipient_type, status) VALUES
('Q20251010001', 'QUOTE_REMINDER', '010-1234-5678', 'CUSTOMER', 'SUCCESS'),
('Q20251010001', 'QUOTE_CONFIRMED', '010-1234-5678', 'CUSTOMER', 'SUCCESS'),
('Q20251010001', 'SALES_NEW_QUOTE', '010-1111-2222', 'SALES', 'SUCCESS'),
('Q20251010002', 'QUOTE_REMINDER', '010-9876-5432', 'CUSTOMER', 'SUCCESS'),
('Q20251010002', 'QUOTE_CANCELLED', '010-9876-5432', 'CUSTOMER', 'SUCCESS');

-- ============================================
-- 유용한 쿼리 모음
-- ============================================

-- 1. 만료된 PENDING 견적 조회 (10분 체크용)
SELECT * FROM quotes
WHERE status = 'PENDING'
AND expires_at < NOW();

-- 2. 차단 여부 확인
SELECT * FROM quote_blocklist
WHERE customer_phone = '010-1234-5678'
AND product_id = 123
AND blocked_until > NOW();

-- 3. 오늘의 견적 통계
SELECT
    status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM quotes WHERE DATE(created_at) = CURDATE()) as percentage
FROM quotes
WHERE DATE(created_at) = CURDATE()
GROUP BY status;

-- 4. 5분~10분 사이 입력한 건 (알림톡 효과 측정)
SELECT COUNT(*) as reminder_effect_count
FROM quotes
WHERE status = 'COMPLETED'
AND TIMESTAMPDIFF(SECOND, created_at, completed_at) BETWEEN 300 AND 600;

-- 5. 만료된 차단 기록 삭제 (정리용 크론잡)
DELETE FROM quote_blocklist
WHERE blocked_until < NOW();

-- ============================================
-- 트리거 (자동화)
-- ============================================

-- 견적 생성 시 만료 시각 자동 설정
DELIMITER //
CREATE TRIGGER before_quote_insert
BEFORE INSERT ON quotes
FOR EACH ROW
BEGIN
    IF NEW.expires_at IS NULL THEN
        SET NEW.expires_at = DATE_ADD(NEW.created_at, INTERVAL 10 MINUTE);
    END IF;
END//
DELIMITER ;

-- 견적 완료 시 완료 시각 자동 설정
DELIMITER //
CREATE TRIGGER before_quote_update
BEFORE UPDATE ON quotes
FOR EACH ROW
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status = 'PENDING' AND NEW.completed_at IS NULL THEN
        SET NEW.completed_at = NOW();
    END IF;

    IF NEW.status = 'CANCELLED' AND OLD.status = 'PENDING' AND NEW.cancelled_at IS NULL THEN
        SET NEW.cancelled_at = NOW();
    END IF;
END//
DELIMITER ;
