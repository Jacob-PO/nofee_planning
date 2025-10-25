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
      range: 'summary!A:B'
    });

    const rows = response.data.values;

    console.log('Summary 시트 내용');
    console.log('='.repeat(80));
    console.log('');

    rows.forEach((row, idx) => {
      if (row[0]) {
        const label = row[0];
        const value = row[1] || '';
        const line = idx + 1;
        console.log(`[${line}] ${label.padEnd(50)} ${value}`);
      }
    });

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
