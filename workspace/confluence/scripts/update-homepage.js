#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';

/**
 * NoFee 프로젝트 홈페이지 업데이트
 * PM 스페이스의 홈페이지를 NoFee 프로젝트 소개로 업데이트
 */
async function main() {
  try {
    const client = new ConfluenceClient();

    const pageId = '196727'; // Project Management 홈페이지 ID
    const title = 'NoFee 프로젝트';

    const content = `
      <h1>NoFee 프로젝트</h1>

      <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
          <p>휴대폰 요금제 및 인터넷 상품 비교 플랫폼</p>
          <p><strong>최종 업데이트:</strong> ${new Date().toLocaleString('ko-KR')}</p>
        </ac:rich-text-body>
      </ac:structured-macro>

      <h2>서비스 개요</h2>
      <p>NoFee는 휴대폰 기기와 요금제를 비교하여 최저가 가입을 제공하는 통신사 비교 플랫폼입니다. 사용자는 다양한 휴대폰 상품과 요금제를 비교하고, 전국의 판매점을 통해 최적의 조건으로 가입할 수 있습니다. 실제 사용자 후기와 판매점 평가를 기반으로 신뢰할 수 있는 선택을 돕습니다.</p>

      <h2>핵심 기능</h2>

      <h3>상품 비교 시스템</h3>
      <ul>
        <li><strong>휴대폰 상품 비교</strong>: SKT, KT, LG U+ 등 통신사별 휴대폰 기기 및 요금제 조합의 월 가격 비교</li>
        <li><strong>가격표 조회</strong>: 상품별, 요금제별, 통신사 정책별 상세 가격 정보 제공</li>
        <li><strong>요금제 정보</strong>: 각 통신사의 요금제 상세 정보 및 할인율, 지원금 안내</li>
        <li><strong>필터링 및 정렬</strong>: 통신사, 제조사, 가격대, 지원 타입별 필터링 및 최저가/인기순 정렬</li>
      </ul>

      <h3>견적 신청 프로세스</h3>
      <ul>
        <li><strong>온라인 견적 신청</strong>: 원하는 상품과 요금제 선택 후 견적 신청 등록</li>
        <li><strong>개통자 정보 관리</strong>: 이름, 전화번호, 생년월일, 주소 등 개인정보 암호화 저장</li>
        <li><strong>신분증 업로드</strong>: AWS S3 기반 안전한 신분증 파일 관리</li>
        <li><strong>신청 상태 추적</strong>: 대기, 진행 중, 완료 등 신청 단계별 현황 확인</li>
        <li><strong>알림 시스템</strong>: Slack, 이메일, SMS를 통한 신청 상태 자동 알림</li>
      </ul>

      <h3>커뮤니티 기능</h3>
      <ul>
        <li><strong>사용자 후기</strong>: 가입 완료 후 상품에 대한 평점 및 사진 후기 작성</li>
        <li><strong>판매점 평가</strong>: 판매점별 리뷰 및 평점 시스템</li>
        <li><strong>자유게시판</strong>: 사용자 간 정보 교류를 위한 커뮤니티 게시판</li>
        <li><strong>좋아요 및 찜</strong>: 관심 상품 및 판매점 저장 기능</li>
      </ul>

      <h3>캠페인 및 이벤트</h3>
      <ul>
        <li><strong>이벤트 캠페인</strong>: 기간 한정 특별 혜택 및 프로모션</li>
        <li><strong>상품별 이벤트</strong>: 특정 휴대폰 기기에 대한 추가 할인 및 사은품</li>
        <li><strong>캠페인 신청</strong>: 이벤트 상품에 대한 별도 신청 프로세스</li>
      </ul>

      <h3>판매점 관리</h3>
      <ul>
        <li><strong>지역별 판매점</strong>: 시도, 시군구 단위 판매점 검색</li>
        <li><strong>판매점 정보</strong>: 영업시간, 위치, 연락처 등 상세 정보</li>
        <li><strong>판매점 대시보드</strong>: 판매점 전용 관리 시스템 (nofee-agency-front)</li>
      </ul>

      <h2>시스템 아키텍처</h2>

      <h3>멀티 모듈 백엔드</h3>
      <table>
        <thead>
          <tr>
            <th>모듈</th>
            <th>설명</th>
            <th>주요 기능</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>api</strong></td>
            <td>고객용 API 서버</td>
            <td>상품 조회, 견적 신청, 후기 작성, 회원 관리, 로그인</td>
          </tr>
          <tr>
            <td><strong>agency</strong></td>
            <td>판매점 전용 API</td>
            <td>판매점 관리, 신청 현황, 매출 통계, 캠페인 관리</td>
          </tr>
          <tr>
            <td><strong>admin</strong></td>
            <td>관리자 백오피스</td>
            <td>시스템 설정, 사용자 관리, 상품 관리, 통계</td>
          </tr>
          <tr>
            <td><strong>common</strong></td>
            <td>공통 라이브러리</td>
            <td>Entity, Mapper, 인증, 파일 처리, AWS 연동</td>
          </tr>
          <tr>
            <td><strong>scheduler</strong></td>
            <td>배치 처리</td>
            <td>정기 알림, 데이터 동기화, 통계 집계</td>
          </tr>
          <tr>
            <td><strong>tool</strong></td>
            <td>개발 도구</td>
            <td>유틸리티 및 테스트 도구</td>
          </tr>
        </tbody>
      </table>

      <h3>프론트엔드 애플리케이션</h3>
      <table>
        <thead>
          <tr>
            <th>프로젝트</th>
            <th>대상 사용자</th>
            <th>주요 페이지</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>nofee-front</strong></td>
            <td>일반 고객</td>
            <td>홈, 상품 목록/상세, 견적 신청, 마이페이지, 후기, 로그인/회원가입</td>
          </tr>
          <tr>
            <td><strong>nofee-agency-front</strong></td>
            <td>판매점</td>
            <td>대시보드, 신청 관리, 판매 현황, 캠페인, 리뷰 관리</td>
          </tr>
        </tbody>
      </table>

      <h2>기술 스택</h2>

      <h3>백엔드</h3>
      <ul>
        <li><strong>Framework</strong>: Spring Boot 3.2.2, Java 17</li>
        <li><strong>Database</strong>: MariaDB (HikariCP), MyBatis 3.0.3</li>
        <li><strong>Cache</strong>: Redis (다중 인스턴스)</li>
        <li><strong>Cloud</strong>: AWS S3 (이미지 저장), AWS SES (이메일 발송)</li>
        <li><strong>Authentication</strong>: JWT, Kakao OAuth</li>
        <li><strong>Build</strong>: Gradle</li>
      </ul>

      <h3>프론트엔드</h3>
      <ul>
        <li><strong>Framework</strong>: Next.js 14, React 18, TypeScript 5</li>
        <li><strong>Styling</strong>: TailwindCSS, DaisyUI</li>
        <li><strong>State Management</strong>: Zustand, React Query</li>
        <li><strong>Authentication</strong>: NextAuth</li>
        <li><strong>Charts</strong>: Chart.js</li>
        <li><strong>Animation</strong>: Framer Motion</li>
      </ul>

      <h2>데이터 모델</h2>

      <h3>주요 엔티티</h3>
      <ul>
        <li><strong>User</strong>: 회원 정보 (암호화된 개인정보)</li>
        <li><strong>Product</strong>: 휴대폰 상품 및 상품 그룹</li>
        <li><strong>RatePlan</strong>: 통신사 요금제</li>
        <li><strong>PriceTable</strong>: 상품+요금제 조합별 가격</li>
        <li><strong>Apply</strong>: 견적 신청 정보</li>
        <li><strong>ApplyUser</strong>: 개통자 정보 (암호화)</li>
        <li><strong>Review</strong>: 상품 후기 및 평점</li>
        <li><strong>Store</strong>: 판매점 정보</li>
        <li><strong>Campaign</strong>: 캠페인 정보</li>
        <li><strong>Event</strong>: 이벤트 정보</li>
        <li><strong>FreeBoard</strong>: 자유게시판</li>
      </ul>

      <h3>데이터 보안</h3>
      <ul>
        <li>개인정보 AES 암호화 (이름, 전화번호, 생년월일, 주소, 계좌정보)</li>
        <li>외래키 제약조건 제거를 통한 데이터 유연성 확보</li>
        <li>논리적 삭제 (deleted_yn) 구현</li>
        <li>감시 필드 (created_at, updated_at, deleted_at) 자동 관리</li>
      </ul>

      <h2>주요 API 엔드포인트</h2>
      <p>상세한 API 스펙은 <a href="/wiki/spaces/PM/pages/131306/NoFee+API">NoFee API 문서</a>를 참조하세요.</p>

      <h3>상품 관련</h3>
      <ul>
        <li>POST /product/phone - 휴대폰 상품 목록 조회</li>
        <li>POST /product/phone/{productCode} - 상품 상세 조회</li>
      </ul>

      <h3>신청 관련</h3>
      <ul>
        <li>POST /apply/phone/estimate-regist - 견적 신청 등록</li>
        <li>POST /apply/phone/estimate/user-regist - 개통자 정보 등록</li>
        <li>POST /apply/phone/estimate/user-id-file-regist - 신분증 파일 업로드</li>
      </ul>

      <h3>후기 관련</h3>
      <ul>
        <li>POST /review/phone - 후기 목록 조회</li>
        <li>POST /review/phone/regist - 후기 등록</li>
      </ul>

      <h2>개발 워크플로우</h2>

      <h3>최근 업데이트</h3>
      <p>주요 개발 이력:</p>
      <ul>
        <li>견적 신청 등록 기능 추가</li>
        <li>캠페인 이벤트 관련 기능 구현</li>
        <li>에이전시 시세표 기능 개발 중</li>
        <li>개통 관련 프로세스 변경</li>
        <li>상품 그룹 조회수 TOP10 기능</li>
        <li>후기 작성 시 스타일 개선 및 이미지 처리 최적화</li>
        <li>캠페인 신청 시 지역 불일치 예외처리</li>
      </ul>

      <h3>개발 환경 설정</h3>
      <ul>
        <li><strong>빌드</strong>: ./gradlew build</li>
        <li><strong>타입체크</strong>: ./gradlew compileJava compileTestJava</li>
        <li><strong>코드 스타일</strong>: ./gradlew checkstyleMain checkstyleTest</li>
      </ul>

      <h2>프로젝트 문서</h2>
      <ul>
        <li><a href="/wiki/spaces/PM/pages/131306/NoFee+API">API 문서</a> - REST API 엔드포인트 및 요청/응답 스펙</li>
        <li><strong>데이터베이스 스키마</strong> - ERD 및 테이블 정의</li>
        <li><strong>개발 가이드</strong> - 환경 설정, 코딩 컨벤션, 네이밍 규칙</li>
        <li><strong>배포 가이드</strong> - 빌드 및 배포 프로세스</li>
        <li><strong>릴리스 노트</strong> - 버전별 변경 사항 및 이슈 해결 내역</li>
      </ul>

      <h2>외부 연동</h2>
      <table>
        <thead>
          <tr>
            <th>서비스</th>
            <th>용도</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Confluence</td>
            <td><a href="https://nofee-workspace.atlassian.net/wiki/home">프로젝트 문서 관리</a></td>
          </tr>
          <tr>
            <td>GitHub</td>
            <td>소스 코드 버전 관리 및 협업</td>
          </tr>
          <tr>
            <td>Notion</td>
            <td>작업 관리 및 일정 트래킹</td>
          </tr>
          <tr>
            <td>Google Analytics</td>
            <td>사용자 행동 분석 및 트래픽 모니터링</td>
          </tr>
          <tr>
            <td>Kakao</td>
            <td>소셜 로그인 OAuth</td>
          </tr>
          <tr>
            <td>Slack</td>
            <td>신청 알림 및 팀 커뮤니케이션</td>
          </tr>
        </tbody>
      </table>

      <h2>팀 정보</h2>
      <ac:structured-macro ac:name="note">
        <ac:rich-text-body>
          <p><strong>프로젝트 관리자:</strong> Jacob</p>
          <p><strong>연락처:</strong> shkim.the@gmail.com</p>
        </ac:rich-text-body>
      </ac:structured-macro>

      <hr/>
      <p><small>최종 업데이트: ${new Date().toISOString()}</small></p>
      <p><small>이 페이지는 Confluence REST API를 통해 자동으로 생성되었습니다.</small></p>
    `;

    // 기존 페이지 정보 가져오기
    console.log('홈페이지 정보를 가져오는 중...');
    const page = await client.getPage(pageId);

    console.log(`현재 페이지: "${page.title}" (버전 ${page.version.number})`);
    console.log('홈페이지 업데이트 중...');

    const updatedPage = await client.updatePage(
      pageId,
      title,
      content,
      page.version.number
    );

    console.log('\n✅ 홈페이지가 성공적으로 업데이트되었습니다!');
    console.log(`📄 제목: ${updatedPage.title}`);
    console.log(`📊 버전: ${page.version.number} → ${updatedPage.version.number}`);
    console.log(`🔗 URL: ${client.baseUrl}${updatedPage._links.webui}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
