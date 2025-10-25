import { google } from 'googleapis';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkClearData() {
  const keyFile = resolve(__dirname, '../../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:E20',
  });

  const data = response.data.values || [];

  console.log('clear 시트 데이터 (처음 20행):');
  console.log(`총 ${data.length}개 행\n`);

  data.forEach((row, idx) => {
    console.log(`${idx + 1}: ${row.join(' | ')}`);
  });
}

checkClearData().catch(console.error);
