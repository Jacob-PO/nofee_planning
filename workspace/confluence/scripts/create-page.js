#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';

/**
 * 새 페이지 생성 예제
 * 사용법: npm run create-page
 */
async function main() {
  try {
    const client = new ConfluenceClient();

    const title = '테스트 페이지 - ' + new Date().toISOString();
    const content = `
      <h1>환영합니다!</h1>
      <p>이것은 자동으로 생성된 테스트 페이지입니다.</p>
      <h2>프로젝트 정보</h2>
      <ul>
        <li>프로젝트: NoFee Workspace</li>
        <li>생성일시: ${new Date().toLocaleString('ko-KR')}</li>
        <li>API를 통해 생성됨</li>
      </ul>
      <h2>코드 예제</h2>
      <ac:structured-macro ac:name="code">
        <ac:parameter ac:name="language">javascript</ac:parameter>
        <ac:plain-text-body><![CDATA[
function hello() {
  console.log('Hello from Confluence API!');
}
        ]]></ac:plain-text-body>
      </ac:structured-macro>
    `;

    console.log('페이지 생성 중...');
    const page = await client.createPage(title, content);

    console.log('\n✅ 페이지가 성공적으로 생성되었습니다!');
    console.log(`📄 제목: ${page.title}`);
    console.log(`🆔 페이지 ID: ${page.id}`);
    console.log(`🔗 URL: ${client.baseUrl}${page._links.webui}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
