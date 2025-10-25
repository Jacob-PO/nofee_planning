#!/usr/bin/env node
import NotionClient from '../lib/notion-client.js';

/**
 * NoFee 프로젝트 문서를 Notion에 동기화
 * 사용법: npm run sync-to-notion
 */
async function main() {
  try {
    const notionClient = new NotionClient();

    // Notion 페이지 URL에서 ID 추출
    const pageUrl = 'https://www.notion.so/jacobkim/2941d254f8088019aba3fe6126e89874';
    const pageId = notionClient.extractPageId(pageUrl);

    console.log(`Notion 페이지 ID: ${pageId}`);
    console.log('페이지 정보를 가져오는 중...\n');

    // 페이지 정보 조회
    const page = await notionClient.getPage(pageId);
    console.log(`페이지 제목: ${page.properties?.title?.title?.[0]?.plain_text || '제목 없음'}`);

    // NoFee 프로젝트 문서 블록 생성
    const blocks = createNoFeeDocBlocks();

    console.log('\nNotion 페이지 내용을 업데이트하는 중...');

    // 기존 블록 교체
    await notionClient.replaceBlocks(pageId, blocks);

    console.log('\n✅ Notion 페이지가 성공적으로 업데이트되었습니다!');
    console.log(`🔗 URL: ${pageUrl}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.code === 'object_not_found') {
      console.error('\n페이지를 찾을 수 없습니다. Notion Integration이 해당 페이지에 접근 권한이 있는지 확인하세요.');
      console.error('페이지 우측 상단 "..." → "Add connections" → Integration 추가');
    }
    process.exit(1);
  }
}

/**
 * NoFee 프로젝트 문서 블록 생성
 */
function createNoFeeDocBlocks() {
  const client = new NotionClient();

  return [
    // 제목
    client.createHeading(1, 'NoFee 프로젝트'),

    // 서비스 개요 Callout
    client.createCallout(
      `휴대폰 요금제 및 인터넷 상품 비교 플랫폼\n최종 업데이트: ${new Date().toLocaleString('ko-KR')}`,
      'ℹ️'
    ),

    // 서비스 개요
    client.createHeading(2, '서비스 개요'),
    client.createParagraph(
      'NoFee는 휴대폰 기기와 요금제를 비교하여 최저가 가입을 제공하는 통신사 비교 플랫폼입니다. 사용자는 다양한 휴대폰 상품과 요금제를 비교하고, 전국의 판매점을 통해 최적의 조건으로 가입할 수 있습니다. 실제 사용자 후기와 판매점 평가를 기반으로 신뢰할 수 있는 선택을 돕습니다.'
    ),

    // 핵심 기능
    client.createHeading(2, '핵심 기능'),

    client.createHeading(3, '상품 비교 시스템'),
    client.createBulletedList('휴대폰 상품 비교: SKT, KT, LG U+ 등 통신사별 휴대폰 기기 및 요금제 조합의 월 가격 비교'),
    client.createBulletedList('가격표 조회: 상품별, 요금제별, 통신사 정책별 상세 가격 정보 제공'),
    client.createBulletedList('요금제 정보: 각 통신사의 요금제 상세 정보 및 할인율, 지원금 안내'),
    client.createBulletedList('필터링 및 정렬: 통신사, 제조사, 가격대, 지원 타입별 필터링 및 최저가/인기순 정렬'),

    client.createHeading(3, '견적 신청 프로세스'),
    client.createBulletedList('온라인 견적 신청: 원하는 상품과 요금제 선택 후 견적 신청 등록'),
    client.createBulletedList('개통자 정보 관리: 이름, 전화번호, 생년월일, 주소 등 개인정보 암호화 저장'),
    client.createBulletedList('신분증 업로드: AWS S3 기반 안전한 신분증 파일 관리'),
    client.createBulletedList('신청 상태 추적: 대기, 진행 중, 완료 등 신청 단계별 현황 확인'),
    client.createBulletedList('알림 시스템: Slack, 이메일, SMS를 통한 신청 상태 자동 알림'),

    client.createHeading(3, '커뮤니티 기능'),
    client.createBulletedList('사용자 후기: 가입 완료 후 상품에 대한 평점 및 사진 후기 작성'),
    client.createBulletedList('판매점 평가: 판매점별 리뷰 및 평점 시스템'),
    client.createBulletedList('자유게시판: 사용자 간 정보 교류를 위한 커뮤니티 게시판'),
    client.createBulletedList('좋아요 및 찜: 관심 상품 및 판매점 저장 기능'),

    client.createHeading(3, '캠페인 및 이벤트'),
    client.createBulletedList('이벤트 캠페인: 기간 한정 특별 혜택 및 프로모션'),
    client.createBulletedList('상품별 이벤트: 특정 휴대폰 기기에 대한 추가 할인 및 사은품'),
    client.createBulletedList('캠페인 신청: 이벤트 상품에 대한 별도 신청 프로세스'),

    client.createHeading(3, '판매점 관리'),
    client.createBulletedList('지역별 판매점: 시도, 시군구 단위 판매점 검색'),
    client.createBulletedList('판매점 정보: 영업시간, 위치, 연락처 등 상세 정보'),
    client.createBulletedList('판매점 대시보드: 판매점 전용 관리 시스템 (nofee-agency-front)'),

    // 시스템 아키텍처
    client.createHeading(2, '시스템 아키텍처'),

    client.createHeading(3, '멀티 모듈 백엔드'),
    client.createParagraph('Spring Boot 기반 멀티 모듈 아키텍처:'),
    client.createBulletedList('api - 고객용 API 서버: 상품 조회, 견적 신청, 후기 작성, 회원 관리, 로그인'),
    client.createBulletedList('agency - 판매점 전용 API: 판매점 관리, 신청 현황, 매출 통계, 캠페인 관리'),
    client.createBulletedList('admin - 관리자 백오피스: 시스템 설정, 사용자 관리, 상품 관리, 통계'),
    client.createBulletedList('common - 공통 라이브러리: Entity, Mapper, 인증, 파일 처리, AWS 연동'),
    client.createBulletedList('scheduler - 배치 처리: 정기 알림, 데이터 동기화, 통계 집계'),
    client.createBulletedList('tool - 개발 도구: 유틸리티 및 테스트 도구'),

    client.createHeading(3, '프론트엔드 애플리케이션'),
    client.createBulletedList('nofee-front (일반 고객): 홈, 상품 목록/상세, 견적 신청, 마이페이지, 후기, 로그인/회원가입'),
    client.createBulletedList('nofee-agency-front (판매점): 대시보드, 신청 관리, 판매 현황, 캠페인, 리뷰 관리'),

    // 기술 스택
    client.createHeading(2, '기술 스택'),

    client.createHeading(3, '백엔드'),
    client.createBulletedList('Framework: Spring Boot 3.2.2, Java 17'),
    client.createBulletedList('Database: MariaDB (HikariCP), MyBatis 3.0.3'),
    client.createBulletedList('Cache: Redis (다중 인스턴스)'),
    client.createBulletedList('Cloud: AWS S3 (이미지 저장), AWS SES (이메일 발송)'),
    client.createBulletedList('Authentication: JWT, Kakao OAuth'),
    client.createBulletedList('Build: Gradle'),

    client.createHeading(3, '프론트엔드'),
    client.createBulletedList('Framework: Next.js 14, React 18, TypeScript 5'),
    client.createBulletedList('Styling: TailwindCSS, DaisyUI'),
    client.createBulletedList('State Management: Zustand, React Query'),
    client.createBulletedList('Authentication: NextAuth'),
    client.createBulletedList('Charts: Chart.js'),
    client.createBulletedList('Animation: Framer Motion'),

    // 데이터 모델
    client.createHeading(2, '데이터 모델'),

    client.createHeading(3, '주요 엔티티'),
    client.createBulletedList('User: 회원 정보 (암호화된 개인정보)'),
    client.createBulletedList('Product: 휴대폰 상품 및 상품 그룹'),
    client.createBulletedList('RatePlan: 통신사 요금제'),
    client.createBulletedList('PriceTable: 상품+요금제 조합별 가격'),
    client.createBulletedList('Apply: 견적 신청 정보'),
    client.createBulletedList('ApplyUser: 개통자 정보 (암호화)'),
    client.createBulletedList('Review: 상품 후기 및 평점'),
    client.createBulletedList('Store: 판매점 정보'),
    client.createBulletedList('Campaign: 캠페인 정보'),
    client.createBulletedList('Event: 이벤트 정보'),
    client.createBulletedList('FreeBoard: 자유게시판'),

    client.createHeading(3, '데이터 보안'),
    client.createBulletedList('개인정보 AES 암호화 (이름, 전화번호, 생년월일, 주소, 계좌정보)'),
    client.createBulletedList('외래키 제약조건 제거를 통한 데이터 유연성 확보'),
    client.createBulletedList('논리적 삭제 (deleted_yn) 구현'),
    client.createBulletedList('감시 필드 (created_at, updated_at, deleted_at) 자동 관리'),

    // 주요 API 엔드포인트
    client.createHeading(2, '주요 API 엔드포인트'),

    client.createHeading(3, '상품 관련'),
    client.createBulletedList('POST /product/phone - 휴대폰 상품 목록 조회'),
    client.createBulletedList('POST /product/phone/{productCode} - 상품 상세 조회'),

    client.createHeading(3, '신청 관련'),
    client.createBulletedList('POST /apply/phone/estimate-regist - 견적 신청 등록'),
    client.createBulletedList('POST /apply/phone/estimate/user-regist - 개통자 정보 등록'),
    client.createBulletedList('POST /apply/phone/estimate/user-id-file-regist - 신분증 파일 업로드'),

    client.createHeading(3, '후기 관련'),
    client.createBulletedList('POST /review/phone - 후기 목록 조회'),
    client.createBulletedList('POST /review/phone/regist - 후기 등록'),

    // 개발 워크플로우
    client.createHeading(2, '개발 워크플로우'),

    client.createHeading(3, '최근 업데이트'),
    client.createParagraph('주요 개발 이력:'),
    client.createBulletedList('견적 신청 등록 기능 추가'),
    client.createBulletedList('캠페인 이벤트 관련 기능 구현'),
    client.createBulletedList('에이전시 시세표 기능 개발 중'),
    client.createBulletedList('개통 관련 프로세스 변경'),
    client.createBulletedList('상품 그룹 조회수 TOP10 기능'),
    client.createBulletedList('후기 작성 시 스타일 개선 및 이미지 처리 최적화'),
    client.createBulletedList('캠페인 신청 시 지역 불일치 예외처리'),

    client.createHeading(3, '개발 환경 설정'),
    client.createBulletedList('빌드: ./gradlew build'),
    client.createBulletedList('타입체크: ./gradlew compileJava compileTestJava'),
    client.createBulletedList('코드 스타일: ./gradlew checkstyleMain checkstyleTest'),

    // 외부 연동
    client.createHeading(2, '외부 연동'),
    client.createBulletedList('Confluence: 프로젝트 문서 관리'),
    client.createBulletedList('GitHub: 소스 코드 버전 관리 및 협업'),
    client.createBulletedList('Notion: 작업 관리 및 일정 트래킹'),
    client.createBulletedList('Google Analytics: 사용자 행동 분석 및 트래픽 모니터링'),
    client.createBulletedList('Kakao: 소셜 로그인 OAuth'),
    client.createBulletedList('Slack: 신청 알림 및 팀 커뮤니케이션'),

    // 팀 정보
    client.createHeading(2, '팀 정보'),
    client.createCallout(
      '프로젝트 관리자: Jacob\n연락처: shkim.the@gmail.com',
      '📝'
    ),

    // 구분선
    client.createDivider(),

    // 푸터
    client.createParagraph(`최종 업데이트: ${new Date().toISOString()}`),
    client.createParagraph('이 페이지는 Confluence REST API 및 Notion API를 통해 자동으로 생성되었습니다.'),
  ];
}

main();
