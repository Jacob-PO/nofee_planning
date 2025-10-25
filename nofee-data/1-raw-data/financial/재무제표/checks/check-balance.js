import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkBalance() {
  const keyFile = resolve('../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B200',
  });

  const rows = response.data.values || [];

  let totalRevenue = 0;
  let totalExpenses = 0;
  let operatingIncome = 0;
  let netIncome = 0;
  let capitalIn = 0;
  let borrowings = 0;
  let repayments = 0;
  let deposits = 0;
  let cashBalance = 0;
  let actualCashIncome = 0;
  let kimSunhoCapital = 0;
  let officeExpense = 0;

  const parseNum = (str) => {
    if (!str) return 0;
    if (str.includes('(') && str.includes(')')) {
      return -parseFloat(str.replace(/[(),]/g, ''));
    }
    return parseFloat(str.replace(/,/g, '')) || 0;
  };

  rows.forEach((row) => {
    const label = row[0] || '';
    const value = row[1] || '';

    if (label === '매출 합계') totalRevenue = parseNum(value);
    if (label === '판매비와관리비 합계') totalExpenses = parseNum(value);
    if (label === '영업이익(손실)') operatingIncome = parseNum(value);
    if (label === '당기순이익(손실)') netIncome = parseNum(value);
    if (label === '자본금 입금 합계') capitalIn = parseNum(value);
    if (label.includes('차입금 (빌린 돈)')) borrowings = parseNum(value);
    if (label.includes('차입금 상환')) repayments = -parseNum(value);
    if (label.includes('보증금 지출')) deposits = -parseNum(value);
    if (label === '= 현재 통장 잔액') cashBalance = parseNum(value);
    if (label === '통장 순손익' || label === '= 통장 순손익') actualCashIncome = parseNum(value);
    if (label === '자본금 - 김선호') kimSunhoCapital = parseNum(value);
    if (label === '  사업 운영비 - 사무실') officeExpense = parseNum(value);
  });

  console.log('=== 재무제표 정합성 검증 ===\n');
  console.log('【1. 손익계산서】');
  console.log('매출: ' + totalRevenue.toLocaleString() + '원');
  console.log('판매비와관리비: ' + totalExpenses.toLocaleString() + '원');
  console.log('영업이익: ' + operatingIncome.toLocaleString() + '원');
  const calcOp = totalRevenue - totalExpenses;
  console.log('계산: ' + totalRevenue.toLocaleString() + ' - ' + totalExpenses.toLocaleString() + ' = ' + calcOp.toLocaleString() + '원');
  console.log('✓ 영업이익: ' + (operatingIncome === calcOp ? 'OK' : 'ERROR'));
  console.log();

  console.log('【2. 김선호 자본금】');
  console.log('자본금 - 김선호: ' + kimSunhoCapital.toLocaleString() + '원');
  console.log('예상: 1,200,000 + 9,950,000 - 10,000,000 + 950,000 = 2,100,000원');
  console.log('✓ 김선호 자본금: ' + (kimSunhoCapital === 2100000 ? 'OK' : 'ERROR (' + kimSunhoCapital.toLocaleString() + ')'));
  console.log();

  console.log('【3. 사무실 비용】');
  console.log('사업 운영비 - 사무실: ' + officeExpense.toLocaleString() + '원');
  console.log('예상: 544,500 + 1,000,000 = 1,544,500원');
  console.log('✓ 사무실 비용: ' + (officeExpense === 1544500 ? 'OK' : 'ERROR (' + officeExpense.toLocaleString() + ')'));
  console.log();

  console.log('【4. 현금흐름】');
  const calcCash = capitalIn + borrowings - repayments - deposits + actualCashIncome;
  console.log('자본금: ' + capitalIn.toLocaleString());
  console.log('차입금: ' + borrowings.toLocaleString());
  console.log('상환: ' + repayments.toLocaleString());
  console.log('보증금: ' + deposits.toLocaleString());
  console.log('통장순손익: ' + actualCashIncome.toLocaleString());
  console.log('계산 잔액: ' + calcCash.toLocaleString() + '원');
  console.log('Summary 잔액: ' + cashBalance.toLocaleString() + '원');
  console.log('✓ 통장잔액: ' + (Math.abs(cashBalance - calcCash) < 1 ? 'OK' : 'ERROR'));
  console.log();

  const rawResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A1:D250',
  });

  const rawRows = rawResp.data.values || [];
  let lastBal = 0;
  for (let i = rawRows.length - 1; i >= 0; i--) {
    const bal = rawRows[i][3];
    if (bal) {
      lastBal = parseFloat(bal.replace(/,/g, ''));
      break;
    }
  }

  console.log('【5. raw_data 비교】');
  console.log('Summary: ' + cashBalance.toLocaleString() + '원');
  console.log('raw_data: ' + lastBal.toLocaleString() + '원');
  console.log('✓ 일치: ' + (cashBalance === lastBal ? 'OK' : 'ERROR (차이: ' + (cashBalance - lastBal).toLocaleString() + ')'));
  console.log();

  const checks = [
    operatingIncome === calcOp,
    kimSunhoCapital === 2100000,
    officeExpense === 1544500,
    Math.abs(cashBalance - calcCash) < 1,
    cashBalance === lastBal
  ];

  console.log('===================');
  console.log(checks.every(c => c) ? '✅ 전체 검증 성공!' : '⚠️  일부 오류 있음');
}

checkBalance().catch(console.error);
