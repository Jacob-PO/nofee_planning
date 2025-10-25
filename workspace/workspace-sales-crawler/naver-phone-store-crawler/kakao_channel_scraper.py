"""
카카오톡 채널 검색 및 스크래핑
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote


class KakaoChannelScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_kakao_channel_name(self, kakao_url):
        """카카오톡 채널 URL에서 매장명 추출"""
        try:
            response = requests.get(kakao_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # XPath: /html/body/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/strong
            # CSS Selector로 변환
            selectors = [
                'body > div > div:nth-of-type(2) > div:nth-of-type(2) > div > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(1) > div:nth-of-type(1) > div > strong',
                'strong',  # 간단한 셀렉터도 시도
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    if name and len(name) > 0:
                        return name

            return None

        except Exception as e:
            print(f"  ⚠️  카카오톡 채널명 추출 실패 ({kakao_url}): {e}")
            return None

    def search_kakao_channels(self, keyword, max_pages=3):
        """카카오톡 채널 검색 (네이버 통합 검색 활용)"""
        results = []

        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            # 네이버에서 카카오톡 채널 검색
            search_query = f"{keyword} 카카오톡 채널"
            url = f"https://search.naver.com/search.naver?where=blog&query={quote(search_query)}&start={start}"

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                items = soup.select('.api_subject_bx')

                for item in items:
                    try:
                        links = item.find_all('a', href=True)

                        for link_elem in links:
                            href = link_elem.get('href', '')

                            # 블로그/카페 링크만 수집 (카카오톡 채널 정보가 포함된)
                            if href.startswith('http') and any(x in href for x in ['blog.naver.com', 'cafe.naver.com']):
                                text = link_elem.get_text(strip=True)
                                if text and len(text) > 3:
                                    desc_elem = item.select_one('.api_txt_lines.dsc_txt_wrap')
                                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                                    # 설명에 카카오톡 채널 관련 키워드가 있는지 확인
                                    if any(kw in (text + description) for kw in ['카카오톡', '채널', 'pf.kakao.com']):
                                        results.append({
                                            'title': text,
                                            'link': href,
                                            'description': description
                                        })
                                        break

                    except Exception as e:
                        continue

                time.sleep(0.5)

            except Exception as e:
                print(f"카카오톡 채널 검색 오류 ({keyword}, 페이지 {page}): {e}")
                continue

        return results

    def extract_kakao_channel_info(self, url):
        """블로그/카페 페이지에서 카카오톡 채널 정보 추출"""
        try:
            from urllib.parse import urlparse, parse_qs

            # 네이버 블로그는 iframe 구조
            if 'blog.naver.com' in url:
                parsed = urlparse(url)
                path_parts = parsed.path.split('/')

                if len(path_parts) >= 2:
                    blog_id = path_parts[1]
                    log_no = path_parts[2] if len(path_parts) > 2 else None

                    if not log_no:
                        query = parse_qs(parsed.query)
                        log_no = query.get('logNo', [None])[0]

                    if log_no:
                        iframe_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
                        response = requests.get(iframe_url, headers=self.headers, timeout=10)
                        response.raise_for_status()
                        response.encoding = 'utf-8'
                    else:
                        response = requests.get(url, headers=self.headers, timeout=10)
                        response.raise_for_status()
                        response.encoding = 'utf-8'
                else:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    response.encoding = 'utf-8'
            else:
                # 일반 페이지
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            # 전화번호 추출 (010-####-####)
            phone_pattern = r'010-\d{4}-\d{4}'
            phones = list(set(re.findall(phone_pattern, text)))

            if not phones:
                return None

            # 카카오톡 채널 URL 추출
            kakao_urls = re.findall(r'http://pf\.kakao\.com/[_a-zA-Z0-9]+', text)
            kakao_urls.extend(re.findall(r'https://pf\.kakao\.com/[_a-zA-Z0-9]+', text))

            # 카카오톡 채널명 추출
            channel_pattern = r'채널\s*검색\s*["\']([^"\']+)["\']'
            channel_names = re.findall(channel_pattern, text)

            # 매장명 추출 (▣ 기호나 ■ 주변)
            store_pattern = r'[▣■]\s*([^▣■\n]{2,30})\s*[▣■]'
            store_names = re.findall(store_pattern, text)

            # 주소 추출
            address_pattern = r'((?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n]{10,80}(?:호|층))'
            addresses = re.findall(address_pattern, text)

            return {
                'phones': phones,
                'kakao_urls': list(set(kakao_urls)),
                'channel_names': list(set(channel_names)),
                'store_names': list(set(store_names)),
                'addresses': list(set(addresses)),
                'text_preview': text[:500]  # 처음 500자 미리보기
            }

        except Exception as e:
            print(f"  ⚠️  카카오톡 채널 정보 추출 실패 ({url}): {e}")
            return None


def test_kakao_scraper():
    """테스트 함수"""
    scraper = KakaoChannelScraper()

    # 테스트 검색
    print("=" * 60)
    print("카카오톡 채널 검색 테스트")
    print("=" * 60)

    keywords = [
        "휴대폰파크 의정부성지",
        "휴대폰성지 전화번호",
        "수도권 휴대폰성지 위치",
    ]

    total_found = 0

    for keyword in keywords:
        print(f"\n검색어: {keyword}")
        results = scraper.search_kakao_channels(keyword, max_pages=3)
        print(f"검색 결과: {len(results)}개")

        found_count = 0
        for i, result in enumerate(results[:10], 1):
            # 상세 정보 추출
            info = scraper.extract_kakao_channel_info(result['link'])
            if info and info['phones']:
                found_count += 1
                total_found += 1
                print(f"\n✓ {found_count}. {result['title'][:50]}")
                print(f"   링크: {result['link'][:80]}")
                print(f"   전화번호: {', '.join(info['phones'][:5])}")
                if info['kakao_urls']:
                    print(f"   카카오톡 채널: {', '.join(info['kakao_urls'][:2])}")
                if info['store_names']:
                    print(f"   매장명: {', '.join(info['store_names'][:5])}")
                if info['addresses']:
                    print(f"   주소: {info['addresses'][0][:60]}...")

            time.sleep(0.5)

        print(f"\n검색어별 수집: {found_count}개 매장")

    print(f"\n{'='*60}")
    print(f"총 수집: {total_found}개 매장 정보")


if __name__ == "__main__":
    test_kakao_scraper()
