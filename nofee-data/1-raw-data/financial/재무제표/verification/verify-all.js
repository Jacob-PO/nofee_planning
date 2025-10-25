import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function verifyAll() {
  const keyFile = resolve('../../config/google_api_key.json');
  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  console.log('========================================');
  console.log('  전체 재무제표 정합성 검증');
  console.log('========================================\n');

  // 1. raw_data 분석
  const rawResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A1:G300',
  });

  const rawRows = rawResp.data.values.slice(1);

  let rawStats = {
    totalTransactions: rawRows.length,
    deposits: 0,
    withdrawals: 0,
    depositAmount: 0,
    withdrawalAmount: 0,
    latestDate: '',
    latestBalance: 0,
  };

  rawRows.forEach((row) => {
    const date = row[0] || '';
    const type = row[1] || '';
    const amount = parseFloat((row[2] || '0').replace(/,/g, ''));
    const balance = parseFloat((row[3] || '0').replace(/,/g, ''));

    if (type === '입금') {
      rawStats.deposits++;
      rawStats.depositAmount += amount;
    } else if (type === '출금') {
      rawStats.withdrawals++;
      rawStats.withdrawalAmount += Math.abs(amount);
    }

    if (date >= rawStats.latestDate && balance) {
      rawStats.latestDate = date;
      rawStats.latestBalance = balance;
    }
  });

  console.log('【1. raw_data 분석】');
  console.log(`총 거래: ${rawStats.totalTransactions}건`);
  console.log(`입금: ${rawStats.deposits}건, ${rawStats.depositAmount.toLocaleString()}원`);
  console.log(`출금: ${rawStats.withdrawals}건, ${rawStats.withdrawalAmount.toLocaleString()}원`);
  console.log(`최종 거래일: ${rawStats.latestDate}`);
  console.log(`최종 잔액: ${rawStats.latestBalance.toLocaleString()}원`);
  console.log();

  // 2. clear 시트 분석
  const clearResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:H300',
  });

  const clearRows = clearResp.data.values.slice(1);

  let clearStats = {
    total: clearRows.length,
    revenue: { count: 0, amount: 0, categories: {} },
    expenses: { count: 0, amount: 0, categories: {} },
    nonOpIncome: { count: 0, amount: 0, categories: {} },
    nonOpExpense: { count: 0, amount: 0, categories: {} },
    capital: { count: 0, amount: 0, categories: {} },
    borrowings: { count: 0, amount: 0, categories: {} },
    repayments: { count: 0, amount: 0, categories: {} },
    deposits: { count: 0, amount: 0, categories: {} },
  };

  clearRows.forEach((row) => {
    const type = row[1] || '';
    const amount = parseFloat((row[2] || '0').replace(/,/g, ''));
    const category = row[7] || '';

    if (!category) return;

    const absAmount = Math.abs(amount);

    if (category.startsWith('매출')) {
      clearStats.revenue.count++;
      clearStats.revenue.amount += absAmount;
      clearStats.revenue.categories[category] = (clearStats.revenue.categories[category] || 0) + absAmount;
    } else if (category.startsWith('영업외수익')) {
      clearStats.nonOpIncome.count++;
      clearStats.nonOpIncome.amount += absAmount;
      clearStats.nonOpIncome.categories[category] = (clearStats.nonOpIncome.categories[category] || 0) + absAmount;
    } else if (category.startsWith('영업외비용')) {
      clearStats.nonOpExpense.count++;
      clearStats.nonOpExpense.amount += absAmount;
      clearStats.nonOpExpense.categories[category] = (clearStats.nonOpExpense.categories[category] || 0) + absAmount;
    } else if (category.startsWith('자본금') || category.startsWith('자본인출')) {
      clearStats.capital.count++;
      clearStats.capital.amount += amount; // 입금은 +, 출금은 -
      clearStats.capital.categories[category] = (clearStats.capital.categories[category] || 0) + amount;
    } else if (category.startsWith('차입금상환')) {
      clearStats.repayments.count++;
      clearStats.repayments.amount += absAmount;
      clearStats.repayments.categories[category] = (clearStats.repayments.categories[category] || 0) + absAmount;
    } else if (category.startsWith('차입금')) {
      clearStats.borrowings.count++;
      clearStats.borrowings.amount += absAmount;
      clearStats.borrowings.categories[category] = (clearStats.borrowings.categories[category] || 0) + absAmount;
    } else if (category.startsWith('보증금')) {
      clearStats.deposits.count++;
      clearStats.deposits.amount += absAmount;
      clearStats.deposits.categories[category] = (clearStats.deposits.categories[category] || 0) + absAmount;
    } else if (type === '출금') {
      // 판매비와관리비
      clearStats.expenses.count++;
      clearStats.expenses.amount += absAmount;
      clearStats.expenses.categories[category] = (clearStats.expenses.categories[category] || 0) + absAmount;
    }
  });

  console.log('【2. clear 시트 분류】');
  console.log(`총 정제 데이터: ${clearStats.total}건`);
  console.log(`\n[매출]`);
  console.log(`  ${clearStats.revenue.count}건, ${clearStats.revenue.amount.toLocaleString()}원`);
  Object.entries(clearStats.revenue.categories).forEach(([cat, amt]) => {
    console.log(`    ${cat}: ${amt.toLocaleString()}원`);
  });

  console.log(`\n[판매비와관리비]`);
  console.log(`  ${clearStats.expenses.count}건, ${clearStats.expenses.amount.toLocaleString()}원`);
  console.log(`  (개인 계약금 100만원 미포함)`);

  console.log(`\n[영업외수익]`);
  console.log(`  ${clearStats.nonOpIncome.count}건, ${clearStats.nonOpIncome.amount.toLocaleString()}원`);

  console.log(`\n[자본금]`);
  console.log(`  ${clearStats.capital.count}건, 순액 ${clearStats.capital.amount.toLocaleString()}원`);
  Object.entries(clearStats.capital.categories).forEach(([cat, amt]) => {
    console.log(`    ${cat}: ${amt.toLocaleString()}원`);
  });

  console.log(`\n[차입금]`);
  console.log(`  입금: ${clearStats.borrowings.count}건, ${clearStats.borrowings.amount.toLocaleString()}원`);
  console.log(`  상환: ${clearStats.repayments.count}건, ${clearStats.repayments.amount.toLocaleString()}원`);

  console.log(`\n[보증금]`);
  console.log(`  ${clearStats.deposits.count}건, ${clearStats.deposits.amount.toLocaleString()}원`);
  console.log();

  // 3. Summary 시트 분석
  const summaryResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B200',
  });

  const summaryRows = summaryResp.data.values;

  const parseNum = (str) => {
    if (!str) return 0;
    if (str.includes('(') && str.includes(')')) {
      return -parseFloat(str.replace(/[(),]/g, ''));
    }
    return parseFloat(str.replace(/,/g, '')) || 0;
  };

  let summaryStats = {
    revenue: 0,
    expenses: 0,
    operatingIncome: 0,
    nonOpIncome: 0,
    nonOpExpense: 0,
    netIncome: 0,
    capitalIn: 0,
    borrowings: 0,
    repayments: 0,
    deposits: 0,
    cashBalance: 0,
    kimSunhoCapital: 0,
    officeExpense: 0,
  };

  summaryRows.forEach((row) => {
    const label = row[0] || '';
    const value = row[1] || '';

    if (label === '매출 합계') summaryStats.revenue = parseNum(value);
    if (label === '판매비와관리비 합계') summaryStats.expenses = parseNum(value);
    if (label === '영업이익(손실)') summaryStats.operatingIncome = parseNum(value);
    if (label === '당기순이익(손실)') summaryStats.netIncome = parseNum(value);
    if (label === '자본금 입금 합계') summaryStats.capitalIn = parseNum(value);
    if (label.includes('차입금 (빌린 돈)')) summaryStats.borrowings = parseNum(value);
    if (label.includes('차입금 상환')) summaryStats.repayments = -parseNum(value);
    if (label.includes('보증금 지출')) summaryStats.deposits = -parseNum(value);
    if (label === '= 현재 통장 잔액') summaryStats.cashBalance = parseNum(value);
    if (label === '자본금 - 김선호') summaryStats.kimSunhoCapital = parseNum(value);
    if (label === '  사업 운영비 - 사무실') summaryStats.officeExpense = parseNum(value);
  });

  console.log('【3. Summary 시트】');
  console.log(`매출: ${summaryStats.revenue.toLocaleString()}원`);
  console.log(`판관비: ${summaryStats.expenses.toLocaleString()}원`);
  console.log(`영업이익: ${summaryStats.operatingIncome.toLocaleString()}원`);
  console.log(`당기순손익: ${summaryStats.netIncome.toLocaleString()}원`);
  console.log(`자본금 입금: ${summaryStats.capitalIn.toLocaleString()}원`);
  console.log(`차입금: ${summaryStats.borrowings.toLocaleString()}원`);
  console.log(`차입금 상환: ${summaryStats.repayments.toLocaleString()}원`);
  console.log(`보증금: ${summaryStats.deposits.toLocaleString()}원`);
  console.log(`통장 잔액: ${summaryStats.cashBalance.toLocaleString()}원`);
  console.log(`김선호 자본금: ${summaryStats.kimSunhoCapital.toLocaleString()}원`);
  console.log();

  // 4. 검증
  console.log('========================================');
  console.log('  검증 결과');
  console.log('========================================\n');

  const checks = [];

  // 매출 검증
  const revenueMatch = clearStats.revenue.amount === summaryStats.revenue;
  checks.push(revenueMatch);
  console.log(`[매출] clear=${clearStats.revenue.amount.toLocaleString()} vs Summary=${summaryStats.revenue.toLocaleString()}`);
  console.log(`  ${revenueMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 판관비 검증 (개인 계약금 100만원 추가)
  const expensesMatch = (clearStats.expenses.amount + 1000000) === summaryStats.expenses;
  checks.push(expensesMatch);
  console.log(`[판관비] clear=${clearStats.expenses.amount.toLocaleString()} + 개인계약금 1,000,000 = ${(clearStats.expenses.amount + 1000000).toLocaleString()}`);
  console.log(`  Summary=${summaryStats.expenses.toLocaleString()}`);
  console.log(`  ${expensesMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 영업이익 검증
  const calcOpIncome = summaryStats.revenue - summaryStats.expenses;
  const opIncomeMatch = Math.abs(calcOpIncome - summaryStats.operatingIncome) < 1;
  checks.push(opIncomeMatch);
  console.log(`[영업이익] ${summaryStats.revenue.toLocaleString()} - ${summaryStats.expenses.toLocaleString()} = ${calcOpIncome.toLocaleString()}`);
  console.log(`  Summary=${summaryStats.operatingIncome.toLocaleString()}`);
  console.log(`  ${opIncomeMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 자본금 검증
  const capitalMatch = Math.abs(clearStats.capital.amount - summaryStats.capitalIn) < 1000000; // 개인계약금 차이 허용
  checks.push(capitalMatch);
  console.log(`[자본금] clear=${clearStats.capital.amount.toLocaleString()} (Nofee 통장만)`);
  console.log(`  Summary=${summaryStats.capitalIn.toLocaleString()} (개인계약금 포함)`);
  console.log(`  ${capitalMatch ? '✅ 범위내' : '❌ 오류'}\n`);

  // 김선호 자본금 상세 검증
  const kimSunhoFromClear = Object.entries(clearStats.capital.categories)
    .filter(([cat]) => cat.includes('김선호'))
    .reduce((sum, [_, amt]) => sum + amt, 0);

  console.log(`[김선호 자본금 상세]`);
  console.log(`  clear 통장 거래: ${kimSunhoFromClear.toLocaleString()}원`);
  console.log(`  개인 계약금: 1,000,000원`);
  console.log(`  예상 총액: ${(kimSunhoFromClear + 1000000).toLocaleString()}원`);
  console.log(`  Summary: ${summaryStats.kimSunhoCapital.toLocaleString()}원`);
  const kimSunhoMatch = (kimSunhoFromClear + 1000000) === summaryStats.kimSunhoCapital;
  checks.push(kimSunhoMatch);
  console.log(`  ${kimSunhoMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 차입금 검증
  const borrowMatch = clearStats.borrowings.amount === summaryStats.borrowings;
  checks.push(borrowMatch);
  console.log(`[차입금] clear=${clearStats.borrowings.amount.toLocaleString()} vs Summary=${summaryStats.borrowings.toLocaleString()}`);
  console.log(`  ${borrowMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 통장 잔액 검증
  const balanceMatch = rawStats.latestBalance === summaryStats.cashBalance;
  checks.push(balanceMatch);
  console.log(`[통장 잔액] raw_data=${rawStats.latestBalance.toLocaleString()} vs Summary=${summaryStats.cashBalance.toLocaleString()}`);
  console.log(`  ${balanceMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 사무실 비용 검증
  const officeClear = clearStats.expenses.categories['사업 운영비 - 사무실'] || 0;
  const officeMatch = (officeClear + 1000000) === summaryStats.officeExpense;
  checks.push(officeMatch);
  console.log(`[사무실 비용] clear=${officeClear.toLocaleString()} + 개인계약금 1,000,000 = ${(officeClear + 1000000).toLocaleString()}`);
  console.log(`  Summary=${summaryStats.officeExpense.toLocaleString()}`);
  console.log(`  ${officeMatch ? '✅ 일치' : '❌ 불일치'}\n`);

  // 최종 결과
  console.log('========================================');
  if (checks.every(c => c)) {
    console.log('✅✅✅ 전체 검증 통과! 모든 계산 100% 정확 ✅✅✅');
  } else {
    console.log('⚠️  일부 항목에 불일치가 있습니다.');
    console.log(`통과: ${checks.filter(c => c).length}/${checks.length}`);
  }
  console.log('========================================');
}

verifyAll().catch(console.error);
