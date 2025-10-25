#!/usr/bin/env node
import NotionClient from '../lib/notion-client.js';

/**
 * NoFee Notion 페이지 재구성
 * - 메인 페이지: 팀 설명 + 하위 페이지 목록
 * - 하위 페이지: 프로젝트 상세 설명
 */
async function main() {
  try {
    const notionClient = new NotionClient();

    // 메인 페이지 URL
    const mainPageUrl = 'https://www.notion.so/jacobkim/NoFee-2941d254f8088019aba3fe6126e89874';
    const mainPageId = notionClient.extractPageId(mainPageUrl);

    console.log('NoFee 페이지 구조를 재구성하는 중...\n');

    // 1. 프로젝트 상세 설명 하위 페이지 생성
    console.log('1. "NoFee 프로젝트 소개" 하위 페이지 생성 중...');
    const projectPage = await notionClient.client.pages.create({
      parent: { page_id: mainPageId },
      properties: {
        title: {
          title: [{ text: { content: 'NoFee 프로젝트 소개' } }],
        },
      },
      icon: {
        type: 'emoji',
        emoji: '📱',
      },
    });

    console.log(`   ✅ 프로젝트 소개 페이지 생성 완료: ${projectPage.id}`);

    // 2. 프로젝트 상세 내용 추가
    console.log('2. 프로젝트 상세 내용 추가 중...');
    const projectBlocks = createProjectDetailBlocks();
    await notionClient.replaceBlocks(projectPage.id, projectBlocks);
    console.log('   ✅ 프로젝트 상세 내용 추가 완료');

    // 3. 메인 페이지를 팀 소개 + 하위 페이지 목록으로 재구성
    console.log('3. 메인 페이지 재구성 중...');
    const mainPageBlocks = createMainPageBlocks();
    await notionClient.replaceBlocks(mainPageId, mainPageBlocks);
    console.log('   ✅ 메인 페이지 재구성 완료');

    console.log('\n✅ NoFee 페이지 구조 재구성이 완료되었습니다!');
    console.log(`\n메인 페이지: ${mainPageUrl}`);
    console.log(`프로젝트 소개: ${projectPage.url}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.body) {
      console.error('Error details:', JSON.stringify(error.body, null, 2));
    }
    process.exit(1);
  }
}

/**
 * 메인 페이지 블록 생성 (팀 소개 + 하위 페이지 목록)
 */
function createMainPageBlocks() {
  const client = new NotionClient();

  return [
    // 헤더
    client.createHeading(1, 'NoFee'),

    client.createCallout(
      '휴대폰 요금제 및 인터넷 상품 비교 플랫폼을 만드는 팀입니다.',
      '💡'
    ),

    client.createDivider(),

    // 팀 소개
    client.createHeading(2, '팀 소개'),

    client.createParagraph(
      'NoFee는 사용자가 최저가로 통신 서비스에 가입할 수 있도록 돕는 플랫폼을 개발하는 스타트업 팀입니다. 투명한 가격 정보 제공과 사용자 중심의 서비스를 통해 통신 시장의 새로운 기준을 만들어가고 있습니다.'
    ),

    client.createHeading(3, '팀 미션'),
    client.createBulletedList('통신 서비스 가격의 투명성 제공'),
    client.createBulletedList('사용자가 최적의 선택을 할 수 있도록 돕는 비교 플랫폼 구축'),
    client.createBulletedList('판매점과 고객을 연결하는 신뢰 기반 생태계 조성'),

    client.createHeading(3, '핵심 가치'),
    client.createBulletedList('투명성: 모든 가격과 조건을 명확하게 공개'),
    client.createBulletedList('신뢰성: 실제 사용자 후기 기반의 정보 제공'),
    client.createBulletedList('혁신: 기술을 통한 지속적인 서비스 개선'),

    client.createDivider(),

    // 팀 구성
    client.createHeading(2, '팀 구성'),

    client.createHeading(3, '개발팀'),
    client.createBulletedList('백엔드: Spring Boot 기반 멀티 모듈 아키텍처 개발'),
    client.createBulletedList('프론트엔드: Next.js, React를 활용한 반응형 웹 개발'),
    client.createBulletedList('인프라: AWS 기반 클라우드 운영 및 자동화'),

    client.createHeading(3, '기술 스택'),
    client.createBulletedList('Backend: Spring Boot 3.2.2, Java 17, MyBatis, MariaDB, Redis'),
    client.createBulletedList('Frontend: Next.js 14, React 18, TypeScript, TailwindCSS'),
    client.createBulletedList('Infrastructure: AWS (S3, SES), Docker, Gradle'),
    client.createBulletedList('Collaboration: Notion, Confluence, GitHub, Slack'),

    client.createDivider(),

    // 연락처
    client.createHeading(2, '연락처'),
    client.createCallout(
      '프로젝트 관리자: Jacob\n이메일: shkim.the@gmail.com',
      '📧'
    ),

    client.createDivider(),

    // 하위 페이지 안내
    client.createHeading(2, '주요 문서'),
    client.createParagraph('아래 페이지들에서 더 자세한 정보를 확인하실 수 있습니다:'),
    client.createBulletedList('NoFee 프로젝트 소개 - 서비스 상세 설명 및 기술 아키텍처'),
    client.createBulletedList('재무제표 - 재무 현황 및 관리'),

    client.createDivider(),

    client.createParagraph(`최종 업데이트: ${new Date().toLocaleString('ko-KR')}`),
  ];
}

/**
 * 프로젝트 상세 페이지 블록 생성
 */
function createProjectDetailBlocks() {
  const client = new NotionClient();

  return [
    // 프로젝트 개요
    client.createHeading(1, 'NoFee 프로젝트 소개'),

    client.createCallout(
      '휴대폰 요금제 및 인터넷 상품 비교 플랫폼',
      'ℹ️'
    ),

    client.createHeading(2, '서비스 개요'),
    client.createParagraph(
      'NoFee는 휴대폰 기기와 요금제를 비교하여 최저가 가입을 제공하는 통신사 비교 플랫폼입니다. 사용자는 다양한 휴대폰 상품과 요금제를 비교하고, 전국의 판매점을 통해 최적의 조건으로 가입할 수 있습니다. 실제 사용자 후기와 판매점 평가를 기반으로 신뢰할 수 있는 선택을 돕습니다.'
    ),

    // 핵심 기능
    client.createHeading(2, '핵심 기능'),

    client.createHeading(3, '1. 상품 비교 시스템'),
    client.createBulletedList('휴대폰 상품 비교: SKT, KT, LG U+ 등 통신사별 휴대폰 기기 및 요금제 조합의 월 가격 비교'),
    client.createBulletedList('가격표 조회: 상품별, 요금제별, 통신사 정책별 상세 가격 정보 제공'),
    client.createBulletedList('요금제 정보: 각 통신사의 요금제 상세 정보 및 할인율, 지원금 안내'),
    client.createBulletedList('필터링 및 정렬: 통신사, 제조사, 가격대, 지원 타입별 필터링 및 최저가/인기순 정렬'),

    client.createHeading(3, '2. 견적 신청 프로세스'),
    client.createBulletedList('온라인 견적 신청: 원하는 상품과 요금제 선택 후 견적 신청 등록'),
    client.createBulletedList('개통자 정보 관리: 이름, 전화번호, 생년월일, 주소 등 개인정보 암호화 저장'),
    client.createBulletedList('신분증 업로드: AWS S3 기반 안전한 신분증 파일 관리'),
    client.createBulletedList('신청 상태 추적: 대기, 진행 중, 완료 등 신청 단계별 현황 확인'),
    client.createBulletedList('알림 시스템: Slack, 이메일, SMS를 통한 신청 상태 자동 알림'),

    client.createHeading(3, '3. 커뮤니티 기능'),
    client.createBulletedList('사용자 후기: 가입 완료 후 상품에 대한 평점 및 사진 후기 작성'),
    client.createBulletedList('판매점 평가: 판매점별 리뷰 및 평점 시스템'),
    client.createBulletedList('자유게시판: 사용자 간 정보 교류를 위한 커뮤니티 게시판'),
    client.createBulletedList('좋아요 및 찜: 관심 상품 및 판매점 저장 기능'),

    client.createHeading(3, '4. 캠페인 및 이벤트'),
    client.createBulletedList('이벤트 캠페인: 기간 한정 특별 혜택 및 프로모션'),
    client.createBulletedList('상품별 이벤트: 특정 휴대폰 기기에 대한 추가 할인 및 사은품'),
    client.createBulletedList('캠페인 신청: 이벤트 상품에 대한 별도 신청 프로세스'),

    client.createDivider(),

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

    client.createDivider(),

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

    client.createDivider(),

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

    client.createDivider(),

    // 개발 현황
    client.createHeading(2, '개발 현황'),

    client.createHeading(3, '최근 업데이트'),
    client.createBulletedList('견적 신청 등록 기능 추가'),
    client.createBulletedList('캠페인 이벤트 관련 기능 구현'),
    client.createBulletedList('에이전시 시세표 기능 개발 중'),
    client.createBulletedList('개통 관련 프로세스 변경'),
    client.createBulletedList('상품 그룹 조회수 TOP10 기능'),
    client.createBulletedList('후기 작성 시 스타일 개선 및 이미지 처리 최적화'),
    client.createBulletedList('캠페인 신청 시 지역 불일치 예외처리'),

    client.createDivider(),

    client.createParagraph(`최종 업데이트: ${new Date().toLocaleString('ko-KR')}`),
  ];
}

main();
