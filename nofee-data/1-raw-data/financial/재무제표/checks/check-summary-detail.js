import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function check() {
  const keyFile = resolve('../../config/google_api_key.json');
  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const sum = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B200',
  });

  const sumRows = sum.data.values || [];
  const parseNum = (str) => {
    if (!str) return 0;
    if (str.includes('(') && str.includes(')')) {
      return -parseFloat(str.replace(/[(),]/g, ''));
    }
    return parseFloat(str.replace(/,/g, '')) || 0;
  };

  let kimCap = 0, office = 0, cash = 0;
  sumRows.forEach((row) => {
    const l = row[0] || '', v = row[1] || '';
    if (l === '자본금 - 김선호') kimCap = parseNum(v);
    if (l === '  사업 운영비 - 사무실') office = parseNum(v);
    if (l === '= 현재 통장 잔액') cash = parseNum(v);
  });

  const raw = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A1:G300',
  });

  let latestDate = '', latestBal = 0;
  raw.data.values.slice(1).forEach((row) => {
    const d = row[0] || '', b = row[3] || '';
    if (d && b && d >= latestDate) {
      latestDate = d;
      latestBal = parseFloat(b.replace(/,/g, '')) || 0;
    }
  });

  console.log('=== 최종 검증 ===\n');
  console.log('【김선호 자본금】');
  console.log('계산: 1,200,000 (기존) + 1,000,000 (개인계약금) + 9,950,000 (입금) - 10,000,000 (상환)');
  console.log('예상: 2,150,000원');
  console.log('실제: ' + kimCap.toLocaleString() + '원');
  console.log(kimCap === 2150000 ? '✅ OK' : '❌ ERROR');
  console.log();

  console.log('【사무실 비용】');
  console.log('계산: 2,291,990 (clear) + 1,000,000 (개인계약금)');
  console.log('예상: 3,291,990원');
  console.log('실제: ' + office.toLocaleString() + '원');
  console.log(office === 3291990 ? '✅ OK' : '❌ ERROR');
  console.log();

  console.log('【통장 잔액】');
  console.log('Summary: ' + cash.toLocaleString() + '원');
  console.log('raw_data: ' + latestBal.toLocaleString() + '원');
  console.log(cash === latestBal ? '✅ OK' : '❌ ERROR');
  console.log();

  if (kimCap === 2150000 && office === 3291990 && cash === latestBal) {
    console.log('✅✅ 전체 검증 성공! ✅✅');
  }
}

check().catch(console.error);
