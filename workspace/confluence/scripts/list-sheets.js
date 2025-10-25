import { google } from 'googleapis';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function listSheets() {
  const keyFile = resolve(__dirname, '../../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const spreadsheet = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID,
  });

  console.log('스프레드시트의 모든 시트:\n');
  spreadsheet.data.sheets.forEach(sheet => {
    console.log(`- ${sheet.properties.title} (ID: ${sheet.properties.sheetId})`);
  });
}

listSheets().catch(console.error);
