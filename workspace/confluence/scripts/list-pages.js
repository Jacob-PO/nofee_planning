#!/usr/bin/env node
import ConfluenceClient from '../lib/confluence-client.js';

/**
 * 스페이스의 페이지 목록 조회 예제
 * 사용법: npm run list-pages
 */
async function main() {
  try {
    const client = new ConfluenceClient();

    console.log(`스페이스 "${client.spaceKey}"의 페이지 목록을 조회하는 중...\n`);
    const pages = await client.listPages();

    if (pages.length === 0) {
      console.log('📭 페이지가 없습니다.');
      return;
    }

    console.log(`📚 총 ${pages.length}개의 페이지를 찾았습니다:\n`);

    pages.forEach((page, index) => {
      console.log(`${index + 1}. ${page.title}`);
      console.log(`   🆔 ID: ${page.id}`);
      console.log(`   📊 버전: ${page.version.number}`);
      console.log(`   🔗 ${client.baseUrl}${page._links.webui}`);
      console.log('');
    });

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
