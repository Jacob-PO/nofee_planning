"""
네이버 블로그/카페 검색 크롤러
휴대폰 매장 정보 수집 (개인정보 제외)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import quote, unquote
from datetime import datetime
from regions import REGIONS, SHOP_KEYWORDS
from sheets_uploader import GoogleSheetsUploader
from blog_scraper import BlogDetailScraper
import os


class NaverStoreCrawler:
    def __init__(self, enable_detail_scraping=True):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
        self.enable_detail_scraping = enable_detail_scraping
        self.detail_scraper = BlogDetailScraper() if enable_detail_scraping else None
        self.seen_links = set()  # 링크 중복 체크용
        self.seen_phones = set()  # 전화번호 중복 체크용

    def search_naver_blog(self, keyword, max_pages=3):
        """네이버 블로그 검색"""
        blog_results = []

        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            url = f"https://search.naver.com/search.naver?where=blog&query={quote(keyword)}&start={start}"

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # 블로그 검색 결과 추출 (개선된 로직)
                items = soup.select('.api_subject_bx')

                for item in items:
                    try:
                        # 첫 번째 유효한 링크 찾기
                        links = item.find_all('a', href=True)

                        title = None
                        link = None

                        for link_elem in links:
                            href = link_elem.get('href', '')

                            # Keep, 지도, 플레이스, 빈 링크 제외
                            if any(x in href for x in ['keep.naver.com', 'map.naver.com', 'place.naver.com', '#']):
                                continue

                            # 당근마켓 링크만 필터링
                            if href.startswith('http') and 'daangn.com' in href:
                                text = link_elem.get_text(strip=True)
                                if text and len(text) > 3:
                                    title = text
                                    link = href
                                    break

                        if not title or not link:
                            continue

                        # 설명 찾기
                        desc_elem = item.select_one('.api_txt_lines.dsc_txt_wrap')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""

                        blog_results.append({
                            'title': title,
                            'link': link,
                            'description': description,
                            'source': 'blog'
                        })
                    except Exception as e:
                        continue

                time.sleep(0.5)  # 요청 간격

            except Exception as e:
                print(f"블로그 검색 오류 ({keyword}, 페이지 {page}): {e}")
                continue

        return blog_results

    def search_naver_cafe(self, keyword, max_pages=3):
        """네이버 카페 검색"""
        cafe_results = []

        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            url = f"https://search.naver.com/search.naver?where=article&query={quote(keyword)}&start={start}"

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # 카페 검색 결과 추출 (개선된 로직)
                items = soup.select('.api_subject_bx')

                for item in items:
                    try:
                        # 첫 번째 유효한 링크 찾기
                        links = item.find_all('a', href=True)

                        title = None
                        link = None

                        for link_elem in links:
                            href = link_elem.get('href', '')

                            # Keep, 지도, 플레이스, 빈 링크 제외
                            if any(x in href for x in ['keep.naver.com', 'map.naver.com', 'place.naver.com', '#']):
                                continue

                            # 당근마켓 링크만 필터링
                            if href.startswith('http') and 'daangn.com' in href:
                                text = link_elem.get_text(strip=True)
                                if text and len(text) > 3:
                                    title = text
                                    link = href
                                    break

                        if not title or not link:
                            continue

                        # 설명 찾기
                        desc_elem = item.select_one('.api_txt_lines.dsc_txt_wrap')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""

                        cafe_results.append({
                            'title': title,
                            'link': link,
                            'description': description,
                            'source': 'cafe'
                        })
                    except Exception as e:
                        continue

                time.sleep(0.5)

            except Exception as e:
                print(f"카페 검색 오류 ({keyword}, 페이지 {page}): {e}")
                continue

        return cafe_results

    def extract_store_name(self, text):
        """텍스트에서 매장명 추출"""
        # 일반적인 매장명 패턴
        patterns = [
            r'([가-힣A-Za-z0-9]+\s*(?:휴대폰|핸드폰|폰|통신|모바일)(?:매장|판매점|대리점|성지|샵|스토어)?)',
            r'((?:휴대폰|핸드폰|폰|통신|모바일)\s*[가-힣A-Za-z0-9]+)',
            r'([가-힣]{2,10}(?:성지|매장|샵|스토어))',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 가장 구체적인 매장명 반환
                return matches[0].strip()

        # 패턴 매칭 실패 시 키워드 주변 텍스트 추출
        words = text.split()
        for i, word in enumerate(words):
            if any(kw in word for kw in ['휴대폰', '핸드폰', '매장', '판매점']):
                # 앞뒤 단어 조합
                if i > 0:
                    return f"{words[i-1]} {word}".strip()
                elif i < len(words) - 1:
                    return f"{word} {words[i+1]}".strip()

        return "매장명 미상"

    def crawl_by_region(self, region, keyword, max_pages=2):
        """특정 지역 + 키워드로 크롤링"""
        search_query = f"{region} {keyword}"
        print(f"검색 중: {search_query}")

        # 블로그 + 카페 검색
        blog_results = self.search_naver_blog(search_query, max_pages)
        cafe_results = self.search_naver_cafe(search_query, max_pages)

        all_results = blog_results + cafe_results

        # 결과 처리
        for result in all_results:
            # 링크 중복 체크
            if result['link'] in self.seen_links:
                continue

            store_name = self.extract_store_name(result['title'] + ' ' + result['description'])

            # 상세 스크래핑 (옵션)
            if self.enable_detail_scraping and self.detail_scraper:
                try:
                    detail = self.detail_scraper.scrape_detail(result['link'])

                    # 하이픈 숫자가 없으면 스킵 (수집하지 않음)
                    if not detail or not detail.get('hyphenated_numbers'):
                        print(f"  ⊘ 하이픈 숫자 없음: {result['title'][:30]}... - 스킵")
                        continue

                    # 전화번호 중복 체크
                    phone_numbers = detail.get('hyphenated_numbers', '').split(', ')
                    unique_phones = [p for p in phone_numbers if p and p not in self.seen_phones]

                    if not unique_phones:
                        print(f"  ⊘ 전화번호 중복: {result['title'][:30]}... - 스킵")
                        continue

                    # 중복되지 않은 전화번호만 저장
                    for phone in unique_phones:
                        self.seen_phones.add(phone)

                    # 상세 스크래핑에서 얻은 매장명이 있으면 우선 사용
                    final_store_name = detail.get('store_name') or store_name

                    # 하이픈 숫자가 있는 경우만 데이터 저장
                    item = {
                        '지역명': region,
                        '매장명': final_store_name,
                        '지역명_매장명': f"{region}_{final_store_name}",
                        '전화번호': ', '.join(unique_phones),
                        '링크': result['link']
                    }

                    self.seen_links.add(result['link'])
                    self.results.append(item)
                    print(f"  ✓ 수집 완료: {result['title'][:30]}... ({len(unique_phones)}개 전화번호)")

                    time.sleep(0.3)  # 상세 스크래핑 딜레이
                except Exception as e:
                    pass  # 상세 스크래핑 실패해도 계속 진행
            else:
                # 상세 스크래핑 비활성화 시 기본 데이터만 저장
                item = {
                    '지역명': region,
                    '매장명': store_name,
                    '지역명_매장명': f"{region}_{store_name}",
                    '링크': result['link'],
                    '출처': result['source'],
                    '제목': result['title']
                }
                self.results.append(item)

        print(f"  → {len(all_results)}개 결과 수집")
        return len(all_results)

    def crawl_all(self, max_regions=None, max_pages_per_search=2):
        """전체 지역 크롤링"""
        print("=" * 60)
        print("네이버 휴대폰 매장 크롤러 시작")
        print("=" * 60)

        regions_to_crawl = REGIONS[:max_regions] if max_regions else REGIONS
        total_count = 0

        for i, region in enumerate(regions_to_crawl, 1):
            print(f"\n[{i}/{len(regions_to_crawl)}] {region}")

            # 각 지역에 대해 여러 키워드로 검색
            for keyword in SHOP_KEYWORDS[:2]:  # 처음 2개 키워드만 사용
                count = self.crawl_by_region(region, keyword, max_pages_per_search)
                total_count += count
                time.sleep(1)  # 지역 간 대기

        print("\n" + "=" * 60)
        print(f"크롤링 완료! 총 {total_count}개 결과 수집")
        print("=" * 60)

    def save_to_csv(self, filename=None):
        """결과를 CSV로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"naver_phone_stores_{timestamp}.csv"

        df = pd.DataFrame(self.results)

        # CSV 저장 (중복은 이미 크롤링 단계에서 제거됨)
        df.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"\n✓ CSV 저장 완료: {filename}")
        print(f"✓ 총 {len(df)}개 항목")
        print(f"✓ 유니크 전화번호: {len(self.seen_phones)}개")

        return filename

    def upload_to_google_sheets(self, credentials_file, spreadsheet_url, worksheet_name='naver'):
        """
        Google Sheets에 결과 업로드 (기존 데이터에 추가)

        Args:
            credentials_file: Google API 인증 파일 경로
            spreadsheet_url: 구글 시트 URL
            worksheet_name: 워크시트 이름 (기본값: 'naver')
        """
        if not self.results:
            print("⚠️  업로드할 데이터가 없습니다.")
            return False

        print("\n" + "=" * 60)
        print("Google Sheets 업로드 시작")
        print("=" * 60)

        # DataFrame 생성
        df = pd.DataFrame(self.results)

        # 업로더 초기화
        uploader = GoogleSheetsUploader(credentials_file)

        # 연결
        if not uploader.connect():
            return False

        # 시트 열기
        if not uploader.open_sheet(spreadsheet_url, worksheet_name):
            return False

        # 기존 링크 가져오기 (중복 방지)
        existing_links = uploader.get_existing_links('링크')

        if existing_links:
            # 중복 제거
            df_new = df[~df['링크'].isin(existing_links)]
            print(f"✓ 중복 제거: {len(df) - len(df_new)}개 (기존 데이터와 중복)")
        else:
            df_new = df

        if len(df_new) == 0:
            print("⚠️  업로드할 신규 데이터가 없습니다. (모두 중복)")
            return False

        # 업로드 (추가 모드)
        success = uploader.upload_dataframe(df_new, append_mode=True)

        if success:
            print("=" * 60)
            print(f"✓ Google Sheets 업로드 완료!")
            print(f"✓ {len(df_new)}개 항목 추가됨")
            print("=" * 60)

        return success

    def get_results_summary(self):
        """결과 요약"""
        if not self.results:
            return "수집된 데이터가 없습니다."

        df = pd.DataFrame(self.results)

        summary = f"""

수집 결과 요약:
{'=' * 50}
전체 항목 수: {len(df)}
지역 수: {df['지역명'].nunique()}
출처 - 블로그: {len(df[df['출처'] == 'blog'])}개
출처 - 카페: {len(df[df['출처'] == 'cafe'])}개

상위 5개 지역:
{df['지역명'].value_counts().head().to_string()}
{'=' * 50}
        """

        return summary


def main():
    """메인 실행 함수"""
    # 상세 스크래핑 활성화 (블로그 내용에서 전화번호 추출)
    crawler = NaverStoreCrawler(enable_detail_scraping=True)

    # 부산 지역 전체 크롤링 (17개 구)
    # 전체 크롤링: max_regions=None
    crawler.crawl_all(max_regions=17, max_pages_per_search=2)

    # 결과 요약 출력
    print(crawler.get_results_summary())

    # CSV 저장 (백업용)
    crawler.save_to_csv()

    # Google Sheets 업로드
    credentials_path = "../../config/google_api_key.json"
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo/edit"

    if os.path.exists(credentials_path):
        crawler.upload_to_google_sheets(
            credentials_file=credentials_path,
            spreadsheet_url=spreadsheet_url,
            worksheet_name='naver'
        )
    else:
        print(f"\n⚠️  인증 파일을 찾을 수 없습니다: {credentials_path}")
        print("Google Sheets 업로드를 건너뜁니다.")


if __name__ == "__main__":
    main()
