const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CREDENTIALS_PATH = path.resolve(__dirname, '../../../config/google_api_key.json');
const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));

const auth = new google.auth.GoogleAuth({
  credentials,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
});

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

(async () => {
  try {
    const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: 'clear!A:I'
    });

    const rows = response.data.values;

    console.log('='.repeat(80));
    console.log('📊 Nofee 재무제표 정합성 검증');
    console.log('='.repeat(80));
    console.log('');

    // 1. 매출 검증
    console.log('[ 1. 매출 검증 ]');
    console.log('-'.repeat(80));
    const 매출 = {};
    let 매출합계 = 0;

    rows.forEach((row, idx) => {
      if (idx === 0) return;
      const 계정타입 = row[8] || '';
      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정타입 === '매출') {
        if (!매출[계정과목]) 매출[계정과목] = 0;
        매출[계정과목] += 금액;
        매출합계 += 금액;
      }
    });

    Object.entries(매출).sort((a, b) => b[1] - a[1]).forEach(([계정, 금액]) => {
      console.log(`  ${계정.padEnd(30)} ${금액.toLocaleString().padStart(15)}원`);
    });
    console.log('-'.repeat(80));
    console.log(`  합계${' '.repeat(30)} ${매출합계.toLocaleString().padStart(15)}원`);
    console.log('  Summary 시트 매출:          5,800,000원');
    console.log(`  차이:                       ${(매출합계 - 5800000).toLocaleString()}원`);
    console.log(매출합계 === 5800000 ? '  ✅ 매출 검증 통과' : '  ❌ 매출 불일치');
    console.log('');

    // 2. 비용 검증
    console.log('[ 2. 비용 검증 ]');
    console.log('-'.repeat(80));
    const 비용 = {};
    let 비용합계 = 0;

    rows.forEach((row, idx) => {
      if (idx === 0) return;
      const 계정타입 = row[8] || '';
      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정타입 === '비용') {
        if (!비용[계정과목]) 비용[계정과목] = 0;
        비용[계정과목] += Math.abs(금액);
        비용합계 += Math.abs(금액);
      }
    });

    // 대분류별 집계
    const 대분류 = {};
    Object.entries(비용).forEach(([계정, 금액]) => {
      const 분류 = 계정.split(' - ')[0];
      if (!대분류[분류]) 대분류[분류] = 0;
      대분류[분류] += 금액;
    });

    Object.entries(대분류).sort((a, b) => b[1] - a[1]).forEach(([분류, 금액]) => {
      console.log(`  ${분류.padEnd(30)} ${금액.toLocaleString().padStart(15)}원`);
    });
    console.log('-'.repeat(80));
    console.log(`  합계${' '.repeat(30)} ${비용합계.toLocaleString().padStart(15)}원`);
    console.log('  Summary 시트 비용:         12,694,364원');
    console.log(`  차이:                       ${(비용합계 - 12694364).toLocaleString()}원`);
    console.log(비용합계 === 12694364 ? '  ✅ 비용 검증 통과' : '  ❌ 비용 불일치');
    console.log('');

    // 3. 영업손익 검증
    console.log('[ 3. 영업손익 검증 ]');
    console.log('-'.repeat(80));
    const 영업이익 = 매출합계 - 비용합계;
    console.log(`  매출:                       ${매출합계.toLocaleString().padStart(15)}원`);
    console.log(`  비용:                       ${비용합계.toLocaleString().padStart(15)}원`);
    console.log(`  영업이익(계산):             ${영업이익.toLocaleString().padStart(15)}원`);
    console.log('  Summary 영업이익:          -6,894,364원');
    console.log(`  차이:                       ${(영업이익 - (-6894364)).toLocaleString()}원`);
    console.log(영업이익 === -6894364 ? '  ✅ 영업이익 검증 통과' : '  ❌ 영업이익 불일치');
    console.log('');

    // 4. 영업외수익 검증
    console.log('[ 4. 영업외수익 검증 ]');
    console.log('-'.repeat(80));
    const 영업외수익 = {};
    let 영업외수익합계 = 0;

    rows.forEach((row, idx) => {
      if (idx === 0) return;
      const 계정타입 = row[8] || '';
      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정타입 === '영업외수익') {
        if (!영업외수익[계정과목]) 영업외수익[계정과목] = 0;
        영업외수익[계정과목] += 금액;
        영업외수익합계 += 금액;
      }
    });

    Object.entries(영업외수익).sort((a, b) => b[1] - a[1]).forEach(([계정, 금액]) => {
      console.log(`  ${계정.padEnd(30)} ${금액.toLocaleString().padStart(15)}원`);
    });
    console.log('-'.repeat(80));
    console.log(`  합계${' '.repeat(30)} ${영업외수익합계.toLocaleString().padStart(15)}원`);
    console.log('  Summary 영업외수익:          347,986원');
    console.log(`  차이:                       ${(영업외수익합계 - 347986).toLocaleString()}원`);
    console.log(영업외수익합계 === 347986 ? '  ✅ 영업외수익 검증 통과' : '  ❌ 영업외수익 불일치');
    console.log('');

    // 5. 당기순손익 검증
    console.log('[ 5. 당기순손익 검증 ]');
    console.log('-'.repeat(80));
    const 당기순이익 = 영업이익 + 영업외수익합계;
    console.log(`  영업이익:                   ${영업이익.toLocaleString().padStart(15)}원`);
    console.log(`  영업외수익:                 ${영업외수익합계.toLocaleString().padStart(15)}원`);
    console.log(`  당기순이익(계산):           ${당기순이익.toLocaleString().padStart(15)}원`);
    console.log('  Summary 당기순이익:        -6,546,378원');
    console.log(`  차이:                       ${(당기순이익 - (-6546378)).toLocaleString()}원`);
    console.log(당기순이익 === -6546378 ? '  ✅ 당기순이익 검증 통과' : '  ❌ 당기순이익 불일치');
    console.log('');

    // 6. 차입금 검증
    console.log('[ 6. 차입금 검증 ]');
    console.log('-'.repeat(80));
    const 차입금 = {};
    const 차입금상환 = {};

    rows.forEach((row, idx) => {
      if (idx === 0) return;
      const 계정타입 = row[8] || '';
      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정타입 === '차입금') {
        if (계정과목.includes('차입금상환')) {
          if (!차입금상환[계정과목]) 차입금상환[계정과목] = 0;
          차입금상환[계정과목] += Math.abs(금액);
        } else {
          if (!차입금[계정과목]) 차입금[계정과목] = 0;
          차입금[계정과목] += 금액;
        }
      }
    });

    console.log('  [차입금]');
    Object.entries(차입금).forEach(([계정, 금액]) => {
      console.log(`    ${계정.padEnd(28)} ${금액.toLocaleString().padStart(15)}원`);
    });
    const 차입금합계 = Object.values(차입금).reduce((sum, amt) => sum + amt, 0);
    console.log(`    합계${' '.repeat(28)} ${차입금합계.toLocaleString().padStart(15)}원`);
    console.log('    Summary 차입금 합계:        34,950,000원');
    console.log(`    차이:                       ${(차입금합계 - 34950000).toLocaleString()}원`);

    console.log('  [차입금 상환]');
    Object.entries(차입금상환).forEach(([계정, 금액]) => {
      console.log(`    ${계정.padEnd(28)} ${금액.toLocaleString().padStart(15)}원`);
    });
    const 상환합계 = Object.values(차입금상환).reduce((sum, amt) => sum + amt, 0);
    console.log(`    합계${' '.repeat(28)} ${상환합계.toLocaleString().padStart(15)}원`);
    console.log('    Summary 상환 합계:          20,000,000원');
    console.log(`    차이:                       ${(상환합계 - 20000000).toLocaleString()}원`);

    const 순차입금 = 차입금합계 - 상환합계;
    console.log(`  순차입금:                   ${순차입금.toLocaleString().padStart(15)}원`);
    console.log('  Summary 순차입금:           14,950,000원');
    console.log(순차입금 === 14950000 ? '  ✅ 차입금 검증 통과' : '  ❌ 차입금 불일치');
    console.log('');

    // 7. 자본금 검증
    console.log('[ 7. 자본금 검증 ]');
    console.log('-'.repeat(80));
    const 자본금 = {};

    rows.forEach((row, idx) => {
      if (idx === 0) return;
      const 계정타입 = row[8] || '';
      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정타입 === '자본거래' && 계정과목.includes('자본금')) {
        if (!자본금[계정과목]) 자본금[계정과목] = 0;
        자본금[계정과목] += 금액;
      }
    });

    Object.entries(자본금).forEach(([계정, 금액]) => {
      console.log(`  ${계정.padEnd(30)} ${금액.toLocaleString().padStart(15)}원`);
    });
    const 자본금합계 = Object.values(자본금).reduce((sum, amt) => sum + amt, 0);
    console.log('-'.repeat(80));
    console.log(`  Clear 시트 합계:            ${자본금합계.toLocaleString().padStart(15)}원`);
    console.log('  Summary 자본금(조정):        5,100,000원');
    console.log('  Summary 자본금(실제):        5,150,000원');
    console.log(`  김선호 차입금 이득:                       50,000원`);
    console.log(자본금합계 === 5150000 ? '  ✅ 자본금 검증 통과' : '  ❌ 자본금 불일치');
    console.log('');

    // 8. 통장 잔액 검증
    console.log('[ 8. 통장 잔액 최종 검증 ]');
    console.log('-'.repeat(80));
    console.log(`  기초 잔액:                            0원`);
    console.log(`  + 자본금(실제):             ${자본금합계.toLocaleString().padStart(15)}원`);
    console.log(`  + 차입금:                   ${차입금합계.toLocaleString().padStart(15)}원`);
    console.log(`  - 차입금 상환:              ${(-상환합계).toLocaleString().padStart(15)}원`);
    console.log(`  - 보증금:                   ${(-9000000).toLocaleString().padStart(15)}원`);
    console.log(`  + 매출:                     ${매출합계.toLocaleString().padStart(15)}원`);
    console.log(`  - 비용:                     ${(-비용합계).toLocaleString().padStart(15)}원`);
    console.log(`  + 영업외수익:               ${영업외수익합계.toLocaleString().padStart(15)}원`);
    console.log('-'.repeat(80));

    const 계산잔액 = 자본금합계 + 차입금합계 - 상환합계 - 9000000 + 매출합계 - 비용합계 + 영업외수익합계;
    console.log(`  계산 잔액:                  ${계산잔액.toLocaleString().padStart(15)}원`);
    console.log('  실제 잔액:                   4,553,622원');
    console.log(`  차이:                       ${(계산잔액 - 4553622).toLocaleString()}원`);
    console.log(계산잔액 === 4553622 ? '  ✅ 통장 잔액 검증 통과' : '  ❌ 통장 잔액 불일치');
    console.log('');

    console.log('='.repeat(80));
    console.log('✅ 전체 검증 완료');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
