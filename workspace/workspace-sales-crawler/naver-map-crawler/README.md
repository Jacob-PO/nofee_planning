# Naver Map Crawler for Sales Leads

네이버 지도에서 휴대폰 매장 정보를 자동 수집하는 크롤링 시스템입니다.

## 📁 Project Structure

```
workspace-sales-crawler/
├── naver_map_crawler.py           # Main crawler script
├── google_sheets_uploader.py      # Upload results to Google Sheets
├── download_and_backup.py         # Download and backup data
├── load_existing_addresses.py     # Load existing addresses
├── addresses/                     # Address data files
│   └── existing_addresses.txt     # Existing addresses (for deduplication)
├── api_keys/                      # API keys
│   └── google_api_key.json        # Google API credentials
├── results/                       # Output files
│   ├── naver_map_results.csv      # Crawling results (CSV)
│   └── google_sheets_upload.tsv   # Google Sheets upload format
├── google-store-crawler/          # Google search-based crawler
├── naver-store-crawler/           # Naver blog/cafe crawler
├── archive/                       # Archived old versions
├── requirements.txt
└── README.md
```

## 🚀 Features

### Main Features
- **Auto Scrolling**: Automatically scrolls to load all store listings on each page
- **Auto Pagination**: Navigates through all pages until the last page
- **Smart Filtering**: Only collects stores with phone number or website
- **Deduplication**: Prevents duplicate entries based on existing addresses
- **Category Filter**: Excludes phone accessory shops
- **Regional Search**: Searches across all major cities and regions in Korea

### Data Collection
- Crawl Date (크롤링날짜)
- Store Name (매장명)
- Address (주소)
- Phone Number (전화번호)
- Business Type (업종)
- Operating Hours (영업시간)
- Visitor Reviews (방문자리뷰)
- Blog Reviews (블로그리뷰)
- Website (웹사이트)

## 📋 Requirements

- Python 3.8+
- Chrome Browser
- Google API credentials (for Sheets upload)

## 🔧 Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

### 1. Run Naver Map Crawler

```bash
python naver_map_crawler.py
```

The script will:
- Load existing addresses from `addresses/existing_addresses.txt`
- Search for stores across multiple regions and keywords
- Save results to `results/naver_map_results.csv`
- Create TSV file for Google Sheets upload

**Configuration**: Edit the script to modify:
- Search regions (line 296-302)
- Search keywords (line 304)
- Number of regions/keywords to search (line 308-310)

### 2. Upload to Google Sheets

```bash
python google_sheets_uploader.py
```

**Prerequisites**:
- Place `google_api_key.json` in `api_keys/` folder
- Enable Google Sheets API in Google Cloud Console
- Grant edit permission to service account email

### 3. Backup Data

```bash
python download_and_backup.py
```

Downloads current data from Google Sheets and creates a backup.

## 📊 How It Works

### Crawling Process

1. **Load Existing Data**: Reads `addresses/existing_addresses.txt` to avoid duplicates
2. **Generate Search Queries**: Combines regions + keywords
3. **Navigate to Naver Map**: Opens Naver Map and searches for each query
4. **Auto Scroll**: Scrolls through all listings on each page
5. **Collect Details**: Clicks each store to extract detailed information
6. **Filter & Deduplicate**: Applies filters and checks for duplicates
7. **Save Results**: Saves to CSV and TSV files

### Filtering Logic

✅ **Includes**:
- Stores with phone number OR website
- All business types EXCEPT accessories

❌ **Excludes**:
- Duplicate addresses (already in database)
- Phone accessory shops (액세서리)
- Stores without contact information

## 🔑 Google Sheets Setup

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON key file

### 2. Configure Access

1. Rename downloaded file to `google_api_key.json`
2. Move to `api_keys/` folder
3. Copy service account email (e.g., `xxx@xxx.iam.gserviceaccount.com`)
4. Open your Google Sheet
5. Click "Share" and add service account email with Editor permission

### 3. Update Spreadsheet ID

Edit `google_sheets_uploader.py` line 35:
```python
spreadsheet_id = 'YOUR_SPREADSHEET_ID_HERE'
```

## 📝 Configuration

### Search Regions

Edit regions in `naver_map_crawler.py` (line 296-302):

```python
regions = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    # Add more regions...
]
```

### Search Keywords

Edit keywords in `naver_map_crawler.py` (line 304):

```python
search_terms = ["휴대폰 대리점", "휴대폰 판매점", "휴대폰 성지", "스마트폰 매장"]
```

### Limit Searches

Adjust the slicing in `naver_map_crawler.py` (line 308-310):

```python
for region in regions[:20]:        # First 20 regions
    for term in search_terms[:2]:  # First 2 keywords
```

## ⚠️ Important Notes

- **Don't touch browser** while crawling is in progress
- **Rate limiting**: Script includes delays to prevent blocking
- **API credentials**: Required for Google Sheets upload
- **Existing addresses**: File is auto-generated on first run
- **Results folder**: Created automatically if it doesn't exist

## 🐛 Troubleshooting

### Selenium WebDriver Error

```bash
pip install --upgrade selenium
```

### Google Sheets Authentication Failed

- Check `api_keys/google_api_key.json` exists
- Verify Google Sheets API is enabled
- Confirm service account has edit permission on the sheet

### Duplicate Data Collection

- Check `addresses/existing_addresses.txt` is up-to-date
- Run `load_existing_addresses.py` to refresh the address list

### Chrome Driver Issues

The script uses Chrome in automated mode. Make sure:
- Chrome browser is installed
- ChromeDriver is compatible with your Chrome version

## 📂 Output Files

- **CSV Results**: `results/naver_map_results.csv`
- **TSV for Sheets**: `results/google_sheets_upload.tsv`
- **Address List**: `addresses/existing_addresses.txt`

## 🔄 Data Flow

```
Naver Map Search
      ↓
  Crawling
      ↓
results/naver_map_results.csv
      ↓
google_sheets_uploader.py
      ↓
Google Sheets (영업DB)
      ↓
download_and_backup.py
      ↓
addresses/existing_addresses.txt
```

## 📌 Additional Crawlers

- **google-store-crawler/**: Google search-based crawler
- **naver-store-crawler/**: Naver blog/cafe crawler

See their respective folders for documentation.
