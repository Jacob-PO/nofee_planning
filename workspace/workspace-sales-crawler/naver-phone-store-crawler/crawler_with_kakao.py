"""
통합 크롤러: 네이버(당근마켓) + 카카오톡 채널
"""
from crawler import NaverStoreCrawler
from kakao_channel_scraper import KakaoChannelScraper
from regions import REGIONS
import time
from datetime import datetime
import pandas as pd


class UnifiedCrawler:
    def __init__(self):
        self.naver_crawler = NaverStoreCrawler(enable_detail_scraping=True)
        self.kakao_scraper = KakaoChannelScraper()
        self.results = []
        self.seen_phones = set()

    def crawl_region_all_sources(self, region, max_pages=2):
        """특정 지역을 모든 소스(당근마켓 + 카카오톡 채널)에서 크롤링"""
        print(f"\n{'='*60}")
        print(f"지역: {region}")
        print('='*60)

        total_collected = 0

        # 1. 당근마켓 크롤링
        print("\n[1] 당근마켓 검색...")
        daangn_keywords = [
            f"{region} 휴대폰성지 당근",
            f"{region} 휴대폰 매장 당근"
        ]

        for keyword in daangn_keywords:
            count = self.naver_crawler.crawl_by_region(region, keyword.replace(f"{region} ", ""), max_pages)
            total_collected += count
            time.sleep(1)

        # 당근마켓 결과를 통합 결과에 추가
        for item in self.naver_crawler.results:
            phone = item.get('전화번호', '')
            if phone and phone not in self.seen_phones:
                self.seen_phones.add(phone)
                self.results.append({
                    **item,
                    '출처': '당근마켓'
                })

        # 2. 카카오톡 채널 크롤링
        print("\n[2] 카카오톡 채널 검색...")
        kakao_keywords = [
            f"{region} 휴대폰성지 전화번호",
            f"{region} 휴대폰 매장 위치",
        ]

        kakao_count = 0
        for keyword in kakao_keywords:
            results = self.kakao_scraper.search_kakao_channels(keyword, max_pages=2)

            for result in results[:5]:  # 상위 5개만 확인
                info = self.kakao_scraper.extract_kakao_channel_info(result['link'])

                if info and info['phones']:
                    # 카카오톡 채널 URL이 없으면 스킵
                    if not info['kakao_urls']:
                        continue

                    for phone in info['phones']:
                        if phone not in self.seen_phones:
                            self.seen_phones.add(phone)

                            # 카카오톡 채널 URL 사용
                            kakao_url = info['kakao_urls'][0]

                            # 카카오톡 채널 페이지에서 매장명 추출
                            channel_name = self.kakao_scraper.get_kakao_channel_name(kakao_url)
                            store_name = channel_name if channel_name else (info['store_names'][0] if info['store_names'] else "매장명 미상")

                            self.results.append({
                                '지역명': region,
                                '매장명': store_name,
                                '지역명_매장명': f"{region}_{store_name}",
                                '전화번호': phone,
                                '링크': kakao_url,
                                '출처': '카카오톡채널'
                            })

                            kakao_count += 1
                            print(f"  ✓ 수집 완료: {store_name} ({phone}) - {kakao_url[:50]}")

                time.sleep(0.5)

            time.sleep(1)

        print(f"\n지역별 수집: 당근마켓 {total_collected}개, 카카오톡채널 {kakao_count}개")
        return total_collected + kakao_count

    def crawl_all_regions(self, max_regions=None):
        """전체 지역 크롤링"""
        print("=" * 60)
        print("통합 크롤러 시작 (당근마켓 + 카카오톡 채널)")
        print("=" * 60)

        regions_to_crawl = REGIONS[:max_regions] if max_regions else REGIONS

        for i, region in enumerate(regions_to_crawl, 1):
            print(f"\n[{i}/{len(regions_to_crawl)}] {region}")
            self.crawl_region_all_sources(region, max_pages=2)
            time.sleep(2)

        print("\n" + "=" * 60)
        print(f"크롤링 완료! 총 {len(self.results)}개 매장 수집")
        print(f"유니크 전화번호: {len(self.seen_phones)}개")
        print("=" * 60)

    def save_to_csv(self, filename=None):
        """결과를 CSV로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified_stores_{timestamp}.csv"

        df = pd.DataFrame(self.results)

        # 컬럼 순서 정리
        columns = ['지역명', '매장명', '지역명_매장명', '전화번호', '링크', '출처']
        df = df[columns]

        df.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"\n✓ CSV 저장 완료: {filename}")
        print(f"✓ 총 {len(df)}개 항목")

        # 출처별 통계
        print("\n출처별 통계:")
        for source, count in df['출처'].value_counts().items():
            print(f"  - {source}: {count}개")

        return filename

    def upload_to_google_sheets(self, credentials_file, spreadsheet_url, worksheet_name='naver'):
        """Google Sheets에 업로드"""
        from sheets_uploader import GoogleSheetsUploader

        if not self.results:
            print("업로드할 데이터가 없습니다.")
            return False

        print("\n" + "=" * 60)
        print("Google Sheets 업로드 시작")
        print("=" * 60)

        uploader = GoogleSheetsUploader(credentials_file)

        if not uploader.connect():
            return False

        if not uploader.open_sheet(spreadsheet_url, worksheet_name):
            return False

        # 출처 컬럼 제외하고 업로드 (시트에는 출처 컬럼 없음)
        df = pd.DataFrame(self.results)
        df = df[['지역명', '매장명', '지역명_매장명', '전화번호', '링크']]

        # 기존 링크 가져오기
        existing_links = uploader.get_existing_links('링크')

        if existing_links:
            df_new = df[~df['링크'].isin(existing_links)]
            print(f"✓ 중복 제거: {len(df) - len(df_new)}개")
        else:
            df_new = df

        if len(df_new) == 0:
            print("⚠️  업로드할 신규 데이터가 없습니다.")
            return False

        success = uploader.upload_dataframe(df_new, append_mode=True)

        if success:
            print("=" * 60)
            print(f"✓ Google Sheets 업로드 완료!")
            print(f"✓ {len(df_new)}개 항목 추가됨")
            print("=" * 60)

        return success


def main():
    """메인 실행"""
    crawler = UnifiedCrawler()

    # 부산 지역만 테스트 (처음 5개 구)
    print("부산 지역 테스트 크롤링 (5개 구)")
    crawler.crawl_all_regions(max_regions=5)

    # 결과 저장
    crawler.save_to_csv()

    # Google Sheets 업로드
    credentials_path = "../../config/google_api_key.json"
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1IDbMaZucrE78gYPK_dhFGFWN_oixcRhlM1sU9tZMJRo/edit"

    import os
    if os.path.exists(credentials_path):
        crawler.upload_to_google_sheets(
            credentials_file=credentials_path,
            spreadsheet_url=spreadsheet_url,
            worksheet_name='naver'
        )
    else:
        print(f"\n⚠️  인증 파일을 찾을 수 없습니다: {credentials_path}")


if __name__ == "__main__":
    main()
