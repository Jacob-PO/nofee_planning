#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';

/**
 * 페이지 업데이트 예제
 * 사용법: npm run update-page
 */
async function main() {
  const pageTitle = process.argv[2];

  if (!pageTitle) {
    console.error('사용법: npm run update-page "페이지 제목"');
    process.exit(1);
  }

  try {
    const client = new ConfluenceClient();

    // 페이지 검색
    console.log(`"${pageTitle}" 페이지를 찾는 중...`);
    const page = await client.getPageByTitle(pageTitle);

    if (!page) {
      console.error(`❌ "${pageTitle}" 페이지를 찾을 수 없습니다.`);
      process.exit(1);
    }

    console.log(`✅ 페이지를 찾았습니다. (ID: ${page.id})`);

    // 페이지 업데이트
    const updatedContent = `
      <h1>${pageTitle}</h1>
      <p><strong>최근 업데이트:</strong> ${new Date().toLocaleString('ko-KR')}</p>
      <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
          <p>이 페이지는 Confluence REST API를 통해 자동으로 업데이트되었습니다.</p>
        </ac:rich-text-body>
      </ac:structured-macro>
      <h2>업데이트 내역</h2>
      <p>이전 버전: ${page.version.number}</p>
      <p>현재 버전: ${page.version.number + 1}</p>
    `;

    console.log('페이지 업데이트 중...');
    const updatedPage = await client.updatePage(
      page.id,
      pageTitle,
      updatedContent,
      page.version.number
    );

    console.log('\n✅ 페이지가 성공적으로 업데이트되었습니다!');
    console.log(`📄 제목: ${updatedPage.title}`);
    console.log(`📊 버전: ${updatedPage.version.number}`);
    console.log(`🔗 URL: ${client.baseUrl}${updatedPage._links.webui}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
