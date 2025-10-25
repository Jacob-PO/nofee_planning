"""
블로그/카페 상세 페이지 스크래핑 모듈
매장명, 지역, 연락처 등 추출
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse, parse_qs


class BlogDetailScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # 지역 패턴
        self.region_patterns = [
            r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*([가-힣]+(?:시|구|군))',
            r'([가-힣]+(?:시|구))\s+([가-힣]+(?:동|읍|면))',
        ]

        # 매장명 패턴
        self.store_patterns = [
            r'([가-힣A-Za-z0-9\s]+(?:휴대폰|핸드폰|폰|통신|모바일)(?:매장|판매점|대리점|성지|샵|스토어)?)',
            r'((?:휴대폰|핸드폰|폰|통신|모바일)\s*[가-힣A-Za-z0-9\s]+)',
            r'([가-힣]{2,10}(?:성지|폰|매장|샵))',
        ]

    def get_naver_blog_content(self, url):
        """네이버 블로그 본문 추출"""
        try:
            # 블로그 URL에서 logNo 추출
            parsed = urlparse(url)

            if 'blog.naver.com' in url:
                # URL 파싱
                path_parts = parsed.path.split('/')
                if len(path_parts) >= 2:
                    blog_id = path_parts[1]
                    log_no = path_parts[2] if len(path_parts) > 2 else None

                    if not log_no:
                        # 쿼리 파라미터에서 추출
                        query = parse_qs(parsed.query)
                        log_no = query.get('logNo', [None])[0]

                    if log_no:
                        # iframe 본문 URL
                        iframe_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
                        response = requests.get(iframe_url, headers=self.headers, timeout=10)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, 'html.parser')

                        # 본문 추출 (여러 셀렉터 시도)
                        content_selectors = [
                            'div.se-main-container',
                            'div#postViewArea',
                            'div.post-view',
                            'div#content',
                        ]

                        for selector in content_selectors:
                            content = soup.select_one(selector)
                            if content:
                                return soup, content.get_text(separator=' ', strip=True)

            # 일반 페이지 스크래핑
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # UTF-8 인코딩 명시
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # body 텍스트 반환
            return soup, soup.get_text(separator=' ', strip=True)

        except Exception as e:
            print(f"  ⚠️  본문 추출 실패 ({url}): {e}")
            return None, ""

    def extract_regions(self, text):
        """텍스트에서 지역 추출"""
        regions = []

        for pattern in self.region_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    region = ' '.join(match).strip()
                else:
                    region = match.strip()

                if region and len(region) > 2:
                    regions.append(region)

        # 중복 제거 및 가장 구체적인 것 반환
        if regions:
            # 긴 것이 더 구체적
            regions = sorted(set(regions), key=len, reverse=True)
            return regions[0]

        return None

    def extract_store_name_from_daangn(self, soup):
        """당근마켓 페이지에서 매장명 추출"""
        try:
            # XPath: /html/body/main/div[1]/div[2]/div[1]/h1
            # CSS Selector로 변환
            selectors = [
                'body > main > div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(1) > h1',
                'main div h1',  # 더 간단한 셀렉터
                'h1',  # 가장 간단한 셀렉터
            ]

            for selector in selectors:
                h1 = soup.select_one(selector)
                if h1:
                    store_name = h1.get_text(strip=True)
                    if store_name and len(store_name) > 0:
                        return store_name

            return None
        except:
            return None

    def extract_store_names(self, text, soup=None, url=""):
        """텍스트에서 매장명 추출"""
        # 당근마켓이면 h1에서 추출
        if soup and 'daangn.com' in url:
            daangn_store = self.extract_store_name_from_daangn(soup)
            if daangn_store:
                return daangn_store

        # 일반적인 패턴 매칭
        stores = []

        for pattern in self.store_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                store = match.strip() if isinstance(match, str) else match[0].strip()

                # 필터링: 너무 길거나 짧은 것 제외
                if store and 3 <= len(store) <= 30:
                    # 불필요한 단어 제외
                    if not any(x in store for x in ['입니다', '하세요', '있습니다', '해요', '합니다']):
                        stores.append(store)

        # 중복 제거 및 가장 짧은 것 반환 (간결한 매장명)
        if stores:
            stores = sorted(set(stores), key=len)
            return stores[0]

        return None

    def extract_hyphenated_numbers(self, text):
        """010으로 시작하는 전화번호만 추출 (010-####-####)"""
        # 010 휴대폰 번호 패턴만
        phone_pattern = r'010-\d{4}-\d{4}'
        matches = re.findall(phone_pattern, text)

        # 중복 제거
        return list(set(matches))

    def scrape_detail(self, url, max_retries=2):
        """상세 페이지 스크래핑"""
        for attempt in range(max_retries):
            try:
                # 본문 추출
                soup, content = self.get_naver_blog_content(url)

                if not content:
                    return None

                # 데이터 추출
                region = self.extract_regions(content)
                store = self.extract_store_names(content, soup=soup, url=url)
                hyphenated_numbers = self.extract_hyphenated_numbers(content)

                # 하이픈 숫자가 없으면 None 반환 (수집하지 않음)
                if not hyphenated_numbers:
                    return None

                return {
                    'region': region,
                    'store_name': store,
                    'hyphenated_numbers': ', '.join(hyphenated_numbers[:10]) if hyphenated_numbers else '',  # 최대 10개 전화번호
                    'phone_count': len(hyphenated_numbers),
                    'content_length': len(content)
                }

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"  ⚠️  스크래핑 실패: {url}")
                    return None

        return None


def test_scraper():
    """테스트 함수"""
    scraper = BlogDetailScraper()

    test_urls = [
        'https://blog.naver.com/za03aqy0/223805721355',
        'https://blog.naver.com/zigphone_no1',
        'https://cafe.naver.com/siloserver',
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print('='*60)

        result = scraper.scrape_detail(url)

        if result:
            print(f"지역: {result['region']}")
            print(f"매장명: {result['store_name']}")
            print(f"하이픈 텍스트: {result['hyphenated_texts']}")
            print(f"본문 길이: {result['content_length']}자")
        else:
            print("스크래핑 실패")


if __name__ == "__main__":
    test_scraper()
