import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import re

# 기존 주소 목록 로드
import os
from pathlib import Path

project_root = Path(__file__).parent
addresses_dir = project_root / 'addresses'
results_dir = project_root / 'results'
existing_addresses_file = addresses_dir / 'existing_addresses.txt'

# results 디렉토리 생성
results_dir.mkdir(exist_ok=True)

print("기존 주소 목록 로드 중...")
existing_addresses = set()
try:
    with open(existing_addresses_file, 'r', encoding='utf-8') as f:
        existing_addresses = set(line.strip() for line in f if line.strip())
    print(f"기존 주소 {len(existing_addresses)}개 로드됨")
except FileNotFoundError:
    print("existing_addresses.txt 파일이 없습니다. 모든 데이터를 수집합니다.")

def setup_driver():
    """크롬 드라이버 설정"""
    options = webdriver.ChromeOptions()
    # 기본 설정
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 추가 안티탐지 설정
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(10)
    
    return driver

def search_naver_map(driver, search_query):
    """네이버 지도에서 검색"""
    print(f"\n🔍 '{search_query}' 검색 중...")
    
    # 네이버 지도 열기
    driver.get("https://map.naver.com/")
    time.sleep(3)
    
    # 검색창 찾기 및 검색
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))
        )
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)
    except Exception as e:
        print(f"검색 중 오류: {e}")
        return []
    
    # iframe으로 전환
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
        )
        driver.switch_to.frame("searchIframe")
    except:
        print("검색 결과가 없습니다.")
        return []
    
    return scroll_and_collect_all_places(driver)

def scroll_and_collect_all_places(driver):
    """모든 결과를 스크롤하면서 수집"""
    all_places = []
    page_num = 1
    duplicates_count = 0
    new_count = 0
    
    while True:
        print(f"\n📄 페이지 {page_num} 처리 중...")
        
        # 현재 페이지의 모든 결과 로드를 위해 스크롤
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 10
        
        while scroll_attempts < max_scroll_attempts:
            # 현재 로드된 항목 수 확인
            items = driver.find_elements(By.CSS_SELECTOR, "li._1EKsQ._12tNp")
            current_count = len(items)
            
            if current_count == last_count:
                scroll_attempts += 1
                if scroll_attempts >= 3:  # 3번 연속 같은 수면 스크롤 종료
                    break
            else:
                scroll_attempts = 0
            
            last_count = current_count
            
            # 스크롤 다운
            try:
                scroll_container = driver.find_element(By.CSS_SELECTOR, "div#_pcmap_list_scroll_container")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
                time.sleep(1)
            except:
                break
        
        print(f"현재 페이지에 {current_count}개 항목 발견")
        
        # 각 매장 정보 수집
        places = driver.find_elements(By.CSS_SELECTOR, "li._1EKsQ._12tNp")
        
        for idx, place in enumerate(places):
            try:
                # 매장명
                name_elem = place.find_element(By.CSS_SELECTOR, "span._3Apyb")
                name = name_elem.text.strip()
                
                # 클릭하여 상세 정보 보기
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", place)
                    time.sleep(0.5)
                    place.click()
                    time.sleep(1.5)
                except ElementClickInterceptedException:
                    continue
                
                # 메인 프레임으로 전환
                driver.switch_to.default_content()
                time.sleep(0.5)
                
                # 상세 정보 프레임으로 전환
                try:
                    driver.switch_to.frame("entryIframe")
                    time.sleep(1)
                    
                    # 상세 정보 수집
                    info = extract_place_details(driver, name)
                    
                    # 주소 중복 체크
                    if info['주소'] in existing_addresses:
                        print(f"  {idx + 1}. {name} - 기존 데이터와 중복 (스킵)")
                        duplicates_count += 1
                    # 필터링: 휴대폰액세서리 업종 제외 & 전화번호 또는 웹사이트가 있는 경우만
                    elif info['업종'] and '액세서리' in info['업종']:
                        print(f"  {idx + 1}. {name} - 휴대폰액세서리 업종 (스킵)")
                    elif info['전화번호'] or info['웹사이트']:
                        all_places.append(info)
                        new_count += 1
                        print(f"  {idx + 1}. {name} - ✅ 수집 완료 (신규)")
                    else:
                        print(f"  {idx + 1}. {name} - 연락처 정보 없음 (스킵)")
                    
                except Exception as e:
                    print(f"  {idx + 1}. {name} - 상세 정보 수집 실패: {e}")
                finally:
                    # 다시 검색 결과 프레임으로 전환
                    driver.switch_to.default_content()
                    time.sleep(0.5)
                    driver.switch_to.frame("searchIframe")
                
            except Exception as e:
                print(f"  항목 처리 중 오류: {e}")
                continue
        
        print(f"\n현재까지: 신규 {new_count}개, 중복 {duplicates_count}개")
        
        # 다음 페이지 확인
        try:
            # 페이지네이션 찾기
            pagination = driver.find_element(By.CSS_SELECTOR, "div._1Z4DX")
            next_button = pagination.find_element(By.CSS_SELECTOR, "a._3pA6R.btn_next")
            
            # 다음 버튼이 비활성화되었는지 확인
            if "disabled" in next_button.get_attribute("class"):
                print("마지막 페이지입니다.")
                break
            
            # 다음 페이지로 이동
            next_button.click()
            time.sleep(2)
            page_num += 1
            
        except NoSuchElementException:
            print("더 이상 페이지가 없습니다.")
            break
    
    return all_places

def extract_place_details(driver, name):
    """매장 상세 정보 추출"""
    info = {
        '크롤링날짜': datetime.now().strftime('%Y-%m-%d'),
        '매장명': name,
        '주소': '',
        '전화번호': '',
        '업종': '',
        '영업시간': '',
        '방문자리뷰': '',
        '블로그리뷰': '',
        '웹사이트': ''
    }
    
    try:
        # 주소
        try:
            addr_elem = driver.find_element(By.CSS_SELECTOR, "span._2yqUQ")
            info['주소'] = addr_elem.text.strip()
        except:
            pass
        
        # 전화번호
        try:
            phone_elem = driver.find_element(By.CSS_SELECTOR, "span._3ZA0S")
            info['전화번호'] = phone_elem.text.strip()
        except:
            pass
        
        # 업종
        try:
            category_elem = driver.find_element(By.CSS_SELECTOR, "span._1M85P")
            info['업종'] = category_elem.text.strip()
        except:
            pass
        
        # 영업시간
        try:
            hours_elem = driver.find_element(By.CSS_SELECTOR, "time._1Uj7-")
            info['영업시간'] = hours_elem.text.strip()
        except:
            pass
        
        # 리뷰 수
        try:
            review_container = driver.find_element(By.CSS_SELECTOR, "div._1kUrA")
            spans = review_container.find_elements(By.CSS_SELECTOR, "span")
            for span in spans:
                text = span.text.strip()
                if "방문자리뷰" in text:
                    match = re.search(r'(\d+)', text)
                    if match:
                        info['방문자리뷰'] = match.group(1)
                elif "블로그리뷰" in text:
                    match = re.search(r'(\d+)', text)
                    if match:
                        info['블로그리뷰'] = match.group(1)
        except:
            pass
        
        # 웹사이트
        try:
            link_elem = driver.find_element(By.CSS_SELECTOR, "a._11PUw")
            info['웹사이트'] = link_elem.get_attribute('href')
        except:
            pass
    
    except Exception as e:
        print(f"    상세 정보 추출 중 오류: {e}")
    
    return info

def save_results(places):
    """결과를 CSV 파일로 저장"""
    if not places:
        print("저장할 데이터가 없습니다.")
        return

    df = pd.DataFrame(places)

    # 출력 파일 경로
    csv_file = results_dir / 'naver_map_results.csv'
    tsv_file = results_dir / 'google_sheets_upload.tsv'

    # 기존 파일이 있으면 추가, 없으면 새로 생성
    try:
        existing_df = pd.read_csv(csv_file)
        df = pd.concat([existing_df, df], ignore_index=True)
        print(f"기존 파일에 추가: {len(places)}개")
    except FileNotFoundError:
        print(f"새 파일 생성: {len(places)}개")

    # CSV 저장
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"총 {len(df)}개의 데이터가 {csv_file}에 저장되었습니다.")

    # TSV로도 저장 (Google Sheets 업로드용)
    df.to_csv(tsv_file, sep='\t', index=False, encoding='utf-8-sig')
    print(f"Google Sheets 업로드용 TSV 파일도 생성되었습니다: {tsv_file}")

def main():
    print("=" * 60)
    print("네이버 지도 크롤러 (중복 제외 버전)")
    print("=" * 60)
    
    # 지역별 검색어 생성 - 부산 타겟
    regions = [
        "부산 해운대",
        "부산 부산진구",
        "부산 동래구",
        "부산 남구",
        "부산 서면"
    ]

    search_terms = ["휴대폰 대리점", "휴대폰 판매점"]

    # 지역 + 검색어 조합
    search_queries = []
    for region in regions:
        for term in search_terms:
            search_queries.append(f"{region} {term}")
    
    all_results = []
    
    # 드라이버 시작
    driver = setup_driver()
    
    try:
        for query in search_queries:
            results = search_naver_map(driver, query)
            all_results.extend(results)
            print(f"\n'{query}' 검색 완료: {len(results)}개 신규 데이터")
            
            # 중간 저장
            if results:
                save_results(results)
            
            # 다음 검색 전 대기
            time.sleep(3)
    
    except Exception as e:
        print(f"\n크롤링 중 오류 발생: {e}")
    
    finally:
        driver.quit()
        print(f"\n🎯 크롤링 완료! 총 {len(all_results)}개의 신규 데이터 수집")

if __name__ == "__main__":
    main()