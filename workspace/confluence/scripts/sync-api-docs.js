#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';
import fs from 'fs';
import path from 'path';

/**
 * API 문서 자동 동기화 예제
 * Spring Boot 프로젝트의 API 정보를 Confluence 페이지로 동기화
 * 사용법: npm run sync-api-docs
 */
async function main() {
  try {
    const client = new ConfluenceClient();

    // API 문서 생성
    const apiDocs = generateApiDocumentation();

    const title = 'NoFee API 문서';
    const content = `
      <h1>NoFee API 문서</h1>
      <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
          <p>이 문서는 자동으로 생성되었습니다.</p>
          <p><strong>최종 업데이트:</strong> ${new Date().toLocaleString('ko-KR')}</p>
        </ac:rich-text-body>
      </ac:structured-macro>

      <h2>프로젝트 구조</h2>
      <ul>
        <li><strong>nofee-springboot</strong> - Spring Boot 백엔드
          <ul>
            <li>admin - 관리자 모듈</li>
            <li>agency - 에이전시 모듈</li>
            <li>api - API 모듈</li>
            <li>common - 공통 모듈</li>
            <li>scheduler - 스케줄러 모듈</li>
            <li>tool - 유틸리티 모듈</li>
          </ul>
        </li>
        <li><strong>nofee-front</strong> - 프론트엔드</li>
        <li><strong>nofee-agency-front</strong> - 에이전시 프론트엔드</li>
      </ul>

      ${apiDocs}

      <h2>참고 사항</h2>
      <ac:structured-macro ac:name="note">
        <ac:rich-text-body>
          <p>API 문서는 정기적으로 업데이트됩니다.</p>
          <p>최신 정보는 개발팀에 문의하세요.</p>
        </ac:rich-text-body>
      </ac:structured-macro>
    `;

    console.log('API 문서 동기화 중...');
    const page = await client.upsertPage(title, content);

    console.log('\n✅ API 문서가 성공적으로 동기화되었습니다!');
    console.log(`📄 제목: ${page.title}`);
    console.log(`🔗 URL: ${client.baseUrl}${page._links.webui}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

/**
 * API 문서 생성 (예제)
 */
function generateApiDocumentation() {
  return `
    <h2>주요 API 엔드포인트</h2>

    <h3>사용자 관리</h3>
    <table>
      <thead>
        <tr>
          <th>Method</th>
          <th>Endpoint</th>
          <th>설명</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>GET</td>
          <td>/api/users</td>
          <td>사용자 목록 조회</td>
        </tr>
        <tr>
          <td>POST</td>
          <td>/api/users</td>
          <td>사용자 생성</td>
        </tr>
        <tr>
          <td>GET</td>
          <td>/api/users/{id}</td>
          <td>사용자 상세 조회</td>
        </tr>
        <tr>
          <td>PUT</td>
          <td>/api/users/{id}</td>
          <td>사용자 정보 수정</td>
        </tr>
        <tr>
          <td>DELETE</td>
          <td>/api/users/{id}</td>
          <td>사용자 삭제</td>
        </tr>
      </tbody>
    </table>

    <h3>인증</h3>
    <table>
      <thead>
        <tr>
          <th>Method</th>
          <th>Endpoint</th>
          <th>설명</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>POST</td>
          <td>/api/auth/login</td>
          <td>로그인</td>
        </tr>
        <tr>
          <td>POST</td>
          <td>/api/auth/logout</td>
          <td>로그아웃</td>
        </tr>
        <tr>
          <td>POST</td>
          <td>/api/auth/refresh</td>
          <td>토큰 갱신</td>
        </tr>
      </tbody>
    </table>

    <ac:structured-macro ac:name="expand">
      <ac:parameter ac:name="title">상세 API 스펙 보기</ac:parameter>
      <ac:rich-text-body>
        <ac:structured-macro ac:name="code">
          <ac:parameter ac:name="language">json</ac:parameter>
          <ac:plain-text-body><![CDATA[
{
  "endpoint": "/api/users",
  "method": "POST",
  "description": "새로운 사용자 생성",
  "requestBody": {
    "username": "string",
    "email": "string",
    "password": "string"
  },
  "response": {
    "id": "number",
    "username": "string",
    "email": "string",
    "createdAt": "datetime"
  }
}
          ]]></ac:plain-text-body>
        </ac:structured-macro>
      </ac:rich-text-body>
    </ac:structured-macro>
  `;
}

main();
