const { google } = require('googleapis');
const path = require('path');

const credentials = require(path.join(__dirname, '..', 'credentials.json'));

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
    
    console.log('📊 Clear 시트 통장 잔액 확인');
    console.log('='.repeat(60));
    console.log('');
    console.log('총 거래 건수:', rows.length - 1, '건');
    console.log('');
    console.log('첫 거래:');
    console.log('  날짜:', rows[1][0]);
    console.log('  내용:', rows[1][5]);
    console.log('  거래 후 잔액:', rows[1][3]);
    console.log('');
    console.log('마지막 거래:');
    const lastRow = rows[rows.length - 1];
    console.log('  날짜:', lastRow[0]);
    console.log('  내용:', lastRow[5]);
    console.log('  거래 후 잔액:', lastRow[3]);
    console.log('');
    console.log('='.repeat(60));
    console.log('✅ 최종 통장 잔액:', lastRow[3]);
    
  } catch (error) {
    console.error('오류:', error.message);
  }
})();
