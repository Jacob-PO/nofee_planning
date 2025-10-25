#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * raw_data를 정제하여 clear 시트에 카테고리 분류 추가
 * clear 데이터를 기반으로 Summary 시트에 재무제표 작성
 */
async function main() {
  try {
    console.log('Google Sheets 재무 데이터 처리 시작...\n');

    const credentialsPath = path.resolve(__dirname, '../../../config/google_api_key.json');
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

    // 1단계: raw_data 가져오기
    console.log('1단계: raw_data 시트 데이터 가져오는 중...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'raw_data!A1:Z1000',
    });

    const rows = response.data.values || [];
    if (rows.length === 0) {
      console.log('데이터가 없습니다.');
      return;
    }

    console.log(`   총 ${rows.length - 1}개 거래 내역 확인\n`);

    // 2단계: 거래 내역 분류 및 clear 시트 작성
    console.log('2단계: 거래 내역 분류 및 clear 시트 작성 중...');
    const categorizedData = categorizeTransactions(rows);
    await writeClearSheet(sheets, spreadsheetId, categorizedData);

    console.log(`   수익: ${categorizedData.revenue.length}건`);
    console.log(`   비용: ${categorizedData.expenses.length}건`);
    console.log(`   기타: ${categorizedData.others.length}건\n`);

    // 3단계: clear 시트 데이터 읽어오기
    console.log('3단계: clear 시트 데이터 읽어오는 중...');
    const clearResponse = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'clear!A1:Z1000',
    });

    const clearRows = clearResponse.data.values || [];
    console.log(`   ${clearRows.length - 1}개 정제된 데이터 확인\n`);

    // 4단계: Summary 시트에 재무제표 작성
    console.log('4단계: Summary 시트에 재무제표 작성 중...');
    await writeSummarySheet(sheets, spreadsheetId, categorizedData);

    console.log('\n✅ 재무 데이터 처리 완료!');
    console.log(`🔗 Clear 시트: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit#gid=clear`);
    console.log(`🔗 Summary 시트: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit#gid=Summary`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.response?.data) {
      console.error('상세:', JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }
}

/**
 * 거래 내역 분류
 */
function categorizeTransactions(rows) {
  const headers = rows[0];
  const transactions = {
    revenue: [],    // 수익
    expenses: [],   // 비용
    others: [],     // 기타 (환불 등)
  };

  const summary = {
    totalRevenue: 0,
    totalExpenses: 0,
    categoryRevenue: {},
    categoryExpenses: {},
  };

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row || row.length === 0) continue;

    const transaction = {
      date: row[0] || '',          // 거래일시
      type: row[1] || '',          // 구분 (입금/출금)
      amount: parseAmount(row[2]), // 거래금액
      balance: parseAmount(row[3]), // 거래 후 잔액
      transType: row[4] || '',     // 거래구분
      description: row[5] || '',   // 내용
      memo: row[6] || '',          // 메모
    };

    // 금액이 0이면 스킵
    if (transaction.amount === 0) continue;

    // 카테고리 분류
    const category = categorizeTransaction(transaction);
    transaction.category = category;

    // 입금/출금에 따라 분류
    if (transaction.type === '입금') {
      if (category !== '환불' && category !== '기타') {
        transactions.revenue.push(transaction);
        summary.totalRevenue += transaction.amount;

        if (!summary.categoryRevenue[category]) {
          summary.categoryRevenue[category] = 0;
        }
        summary.categoryRevenue[category] += transaction.amount;
      } else {
        transactions.others.push(transaction);
      }
    } else if (transaction.type === '출금') {
      const absAmount = Math.abs(transaction.amount);

      if (category !== '환불' && category !== '기타') {
        transactions.expenses.push(transaction);
        summary.totalExpenses += absAmount;

        if (!summary.categoryExpenses[category]) {
          summary.categoryExpenses[category] = 0;
        }
        summary.categoryExpenses[category] += absAmount;
      } else {
        transactions.others.push(transaction);
      }
    }
  }

  transactions.summary = summary;
  return transactions;
}

/**
 * 거래 카테고리 분류
 */
function categorizeTransaction(transaction) {
  const desc = transaction.description.toLowerCase();
  const transType = transaction.transType;

  // 수익 분류
  if (transaction.type === '입금') {
    // 이자
    if (transType.includes('이자') || desc.includes('이자')) {
      return '이자 수익';
    }
    // 캐시백
    if (transType.includes('캐시백') || desc.includes('캐시백')) {
      return '캐시백';
    }
    // 환불
    if (desc.includes('환불')) {
      return '환불';
    }
    // 투자금/자본금 (사람 이름)
    if (isPersonName(transaction.description)) {
      return '투자금/자본금';
    }
    // 기타 입금
    return '기타 수익';
  }

  // 비용 분류
  if (transaction.type === '출금') {
    // 마케팅/광고
    if ((desc.includes('카카오') && desc.includes('광고')) ||
        desc.includes('facebook') || desc.includes('fb.me/ads') ||
        desc.includes('meta') || desc.includes('facebk')) {
      return '마케팅/광고비';
    }

    // 세금/공과금
    if (transType.includes('공과금') || desc.includes('지로') ||
        desc.includes('지방세') || desc.includes('세금')) {
      return '세금/공과금';
    }

    // 식비
    if (desc.includes('맥도날드') || desc.includes('빙츄르') ||
        desc.includes('카페') || desc.includes('음식') ||
        desc.includes('식당') || desc.includes('치킨') ||
        desc.includes('피자')) {
      return '식비';
    }

    // 교통비
    if (desc.includes('주유') || desc.includes('택시') ||
        desc.includes('버스') || desc.includes('지하철')) {
      return '교통비';
    }

    // 통신비
    if (desc.includes('통신') || desc.includes('인터넷') ||
        desc.includes('전화')) {
      return '통신비';
    }

    // 사무용품/소모품
    if (desc.includes('문구') || desc.includes('사무')) {
      return '사무용품비';
    }

    // 환불
    if (desc.includes('환불')) {
      return '환불';
    }

    // 카드 결제는 내용으로 재분류 시도, 실패시 일반 카드결제로
    if (transType.includes('카드')) {
      return '기타 카드결제';
    }

    // 일반 이체
    if (transType.includes('이체')) {
      return '기타 이체';
    }

    return '기타 비용';
  }

  return '기타';
}

/**
 * 사람 이름인지 판단 (한글 2-4자)
 */
function isPersonName(str) {
  const koreanNamePattern = /^[가-힣]{2,4}$/;
  return koreanNamePattern.test(str.trim());
}

/**
 * 금액 파싱
 */
function parseAmount(value) {
  if (!value) return 0;
  const cleaned = String(value).replace(/[,원₩\s]/g, '');
  const number = parseFloat(cleaned);
  return isNaN(number) ? 0 : number;
}

/**
 * 숫자 포맷팅
 */
function formatNumber(num) {
  return new Intl.NumberFormat('ko-KR').format(Math.abs(num));
}

/**
 * clear 시트 작성 (1차 정제 데이터)
 */
async function writeClearSheet(sheets, spreadsheetId, transactions) {
  const { revenue, expenses, others } = transactions;

  // 모든 거래를 하나의 배열로 합치고 날짜순 정렬
  const allTransactions = [...revenue, ...expenses, ...others]
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  const clearData = [
    ['거래일시', '구분', '거래금액', '거래 후 잔액', '거래구분', '내용', '메모', '카테고리', '수익/비용 구분'],
    ...allTransactions.map(t => [
      t.date,
      t.type,
      t.amount,
      t.balance,
      t.transType,
      t.description,
      t.memo,
      t.category,
      t.type === '입금' ? '수익' : '비용'
    ])
  ];

  // clear 시트 확인 및 생성
  try {
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
    const clearSheet = spreadsheet.data.sheets.find(
      s => s.properties.title === 'clear'
    );

    if (clearSheet) {
      await sheets.spreadsheets.values.clear({
        spreadsheetId,
        range: 'clear!A1:Z10000',
      });
    } else {
      // clear 시트 생성
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        resource: {
          requests: [{
            addSheet: {
              properties: {
                title: 'clear',
              },
            },
          }],
        },
      });
    }
  } catch (error) {
    console.error('clear 시트 준비 중 오류:', error.message);
  }

  // 데이터 작성
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: 'clear!A1',
    valueInputOption: 'RAW',
    resource: {
      values: clearData,
    },
  });

  console.log('   ✅ clear 시트 업데이트 완료');
}

/**
 * Summary 시트 작성 (재무제표)
 */
async function writeSummarySheet(sheets, spreadsheetId, transactions) {
  const { summary } = transactions;

  // 수익 카테고리별 합계 정렬
  const revenueCategorySummary = Object.entries(summary.categoryRevenue)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  // 비용 카테고리별 합계 정렬
  const expenseCategorySummary = Object.entries(summary.categoryExpenses)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  // 순이익/손실
  const netIncome = summary.totalRevenue - summary.totalExpenses;

  const summaryData = [
    ['NoFee 재무제표'],
    ['생성일시', new Date().toLocaleString('ko-KR')],
    ['기준 데이터', 'clear 시트 (raw_data 1차 정제)'],
    [],
    ['=== 재무 요약 ==='],
    ['총 수익', formatNumber(summary.totalRevenue) + ' 원'],
    ['총 비용', formatNumber(summary.totalExpenses) + ' 원'],
    ['순이익/손실', formatNumber(netIncome) + ' 원'],
    [],
    ['=== 수익 카테고리별 상세 ==='],
    ['카테고리', '금액 (원)'],
    ...revenueCategorySummary,
    ['합계', formatNumber(summary.totalRevenue)],
    [],
    ['=== 비용 카테고리별 상세 ==='],
    ['카테고리', '금액 (원)'],
    ...expenseCategorySummary,
    ['합계', formatNumber(summary.totalExpenses)],
    [],
    ['=== 재무비율 분석 ==='],
    ['비용/수익 비율', summary.totalRevenue > 0 ? `${((summary.totalExpenses / summary.totalRevenue) * 100).toFixed(2)}%` : 'N/A'],
    ['순이익률', summary.totalRevenue > 0 ? `${((netIncome / summary.totalRevenue) * 100).toFixed(2)}%` : 'N/A'],
  ];

  // Summary 시트 확인 및 생성
  try {
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
    const summarySheet = spreadsheet.data.sheets.find(
      s => s.properties.title === 'Summary'
    );

    if (summarySheet) {
      await sheets.spreadsheets.values.clear({
        spreadsheetId,
        range: 'Summary!A1:Z10000',
      });
    } else {
      // Summary 시트 생성
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        resource: {
          requests: [{
            addSheet: {
              properties: {
                title: 'Summary',
              },
            },
          }],
        },
      });
    }
  } catch (error) {
    console.error('Summary 시트 준비 중 오류:', error.message);
  }

  // 데이터 작성
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: 'Summary!A1',
    valueInputOption: 'RAW',
    resource: {
      values: summaryData,
    },
  });

  console.log('   ✅ Summary 시트 업데이트 완료');
}

main();
