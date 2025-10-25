#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';

/**
 * 특정 페이지 조회 예제
 * 사용법: npm run get-page "페이지 제목"
 */
async function main() {
  const pageTitle = process.argv[2];

  if (!pageTitle) {
    console.error('사용법: npm run get-page "페이지 제목"');
    process.exit(1);
  }

  try {
    const client = new ConfluenceClient();

    console.log(`"${pageTitle}" 페이지를 찾는 중...`);
    const page = await client.getPageByTitle(pageTitle);

    if (!page) {
      console.error(`❌ "${pageTitle}" 페이지를 찾을 수 없습니다.`);
      process.exit(1);
    }

    console.log('\n✅ 페이지를 찾았습니다!\n');
    console.log(`📄 제목: ${page.title}`);
    console.log(`🆔 ID: ${page.id}`);
    console.log(`📊 버전: ${page.version.number}`);
    console.log(`🔗 URL: ${client.baseUrl}${page._links.webui}`);
    console.log(`\n📝 내용:\n`);
    console.log('─'.repeat(80));
    console.log(page.body.storage.value);
    console.log('─'.repeat(80));

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
