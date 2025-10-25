#!/usr/bin/env node
import NotionClient from '../lib/notion-client.js';

/**
 * 재무제표 데이터베이스 생성
 * 사용법: npm run create-financial-db
 */
async function main() {
  try {
    const notionClient = new NotionClient();

    // 부모 페이지 URL (팀스페이스 또는 특정 페이지)
    // 기본적으로 노피 소개 페이지 하위에 생성
    const parentPageUrl = 'https://www.notion.so/jacobkim/2941d254f8088019aba3fe6126e89874';
    const parentPageId = notionClient.extractPageId(parentPageUrl);

    console.log('재무제표 데이터베이스를 생성하는 중...\n');

    // 재무제표 속성 정의
    const properties = {
      // 제목 (필수)
      '항목': {
        title: {},
      },

      // 구분 (자산, 부채, 자본, 수익, 비용 등)
      '구분': {
        select: {
          options: [
            { name: '자산', color: 'blue' },
            { name: '부채', color: 'red' },
            { name: '자본', color: 'green' },
            { name: '수익', color: 'purple' },
            { name: '비용', color: 'orange' },
            { name: '기타', color: 'gray' },
          ],
        },
      },

      // 금액
      '금액': {
        number: {
          format: 'won',
        },
      },

      // 날짜/기간
      '날짜': {
        date: {},
      },

      // 분기
      '분기': {
        select: {
          options: [
            { name: '2025 Q1', color: 'blue' },
            { name: '2025 Q2', color: 'green' },
            { name: '2025 Q3', color: 'yellow' },
            { name: '2025 Q4', color: 'red' },
            { name: '2024 Q1', color: 'blue' },
            { name: '2024 Q2', color: 'green' },
            { name: '2024 Q3', color: 'yellow' },
            { name: '2024 Q4', color: 'red' },
          ],
        },
      },

      // 담당자
      '담당자': {
        people: {},
      },

      // 상태
      '상태': {
        select: {
          options: [
            { name: '확정', color: 'green' },
            { name: '예상', color: 'yellow' },
            { name: '검토중', color: 'blue' },
            { name: '수정필요', color: 'red' },
          ],
        },
      },

      // 메모
      '메모': {
        rich_text: {},
      },

      // 증빙서류
      '증빙서류': {
        files: {},
      },

      // 생성일
      '생성일': {
        created_time: {},
      },

      // 최종 수정일
      '최종 수정일': {
        last_edited_time: {},
      },
    };

    // 데이터베이스 생성
    const database = await notionClient.createDatabase(
      parentPageId,
      '재무제표',
      properties
    );

    console.log('✅ 재무제표 데이터베이스가 성공적으로 생성되었습니다!\n');
    console.log(`데이터베이스 ID: ${database.id}`);
    console.log(`URL: ${database.url}`);

    // 샘플 데이터 추가
    console.log('\n샘플 데이터를 추가하는 중...');

    const sampleData = [
      {
        항목: '현금 및 현금성 자산',
        구분: '자산',
        금액: 50000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '보통예금 및 단기예금',
      },
      {
        항목: '매출채권',
        구분: '자산',
        금액: 30000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '고객 미수금',
      },
      {
        항목: '단기차입금',
        구분: '부채',
        금액: 20000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '운영자금 대출',
      },
      {
        항목: '자본금',
        구분: '자본',
        금액: 100000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '납입자본금',
      },
      {
        항목: '서비스 매출',
        구분: '수익',
        금액: 15000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '플랫폼 이용료 및 수수료',
      },
      {
        항목: '광고 수익',
        구분: '수익',
        금액: 5000000,
        분기: '2025 Q1',
        상태: '예상',
        메모: '캠페인 광고 수익',
      },
      {
        항목: '인건비',
        구분: '비용',
        금액: 8000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: '직원 급여 및 복리후생비',
      },
      {
        항목: '서버 운영비',
        구분: '비용',
        금액: 2000000,
        분기: '2025 Q1',
        상태: '확정',
        메모: 'AWS 인프라 비용',
      },
      {
        항목: '마케팅 비용',
        구분: '비용',
        금액: 3000000,
        분기: '2025 Q1',
        상태: '예상',
        메모: '온라인 광고 및 프로모션',
      },
    ];

    for (const data of sampleData) {
      const properties = {
        '항목': {
          title: [
            {
              text: {
                content: data.항목,
              },
            },
          ],
        },
        '구분': {
          select: {
            name: data.구분,
          },
        },
        '금액': {
          number: data.금액,
        },
        '분기': {
          select: {
            name: data.분기,
          },
        },
        '상태': {
          select: {
            name: data.상태,
          },
        },
        '메모': {
          rich_text: [
            {
              text: {
                content: data.메모,
              },
            },
          ],
        },
      };

      await notionClient.createDatabasePage(database.id, properties);
      console.log(`  - ${data.항목} 추가 완료`);

      // API rate limit 방지
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    console.log('\n✅ 샘플 데이터 추가 완료!');
    console.log(`\n재무제표 데이터베이스를 확인하세요: ${database.url}`);

    // 데이터베이스 ID를 파일로 저장
    console.log(`\n데이터베이스 ID를 기록해두세요: ${database.id}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.code === 'object_not_found') {
      console.error('\n페이지를 찾을 수 없습니다. Notion Integration이 해당 페이지에 접근 권한이 있는지 확인하세요.');
    }
    process.exit(1);
  }
}

main();
