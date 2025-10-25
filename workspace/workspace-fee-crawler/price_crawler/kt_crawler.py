#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KT 휴대폰 지원금 크롤러
통일된 UI, 데이터 형식, 로깅 시스템

작성일: 2025-07-22
버전: 1.0
파일명: kt_crawler.py
"""

import os
import sys
import time
from pathlib import Path
import json
import shutil
import logging
import argparse
import traceback
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import pickle

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Rich UI 지원 (선택사항)
# Rich 라이브러리 사용 안함 (UnicodeEncodeError 방지)
RICH_AVAILABLE = False
console = None

# Path imports
from shared_config.config.paths import PathManager, get_raw_data_path, get_checkpoint_path, get_log_path

# 경로 매니저 초기화
path_manager = PathManager()

# 로깅 설정
log_file = get_log_path('kt_crawler', 'crawlers')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 데이터 클래스 정의
@dataclass
class DeviceData:
    """기기 데이터 - 통합 형식"""
    date: str = ""
    crawled_at: str = field(default_factory=lambda: datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'))
    carrier: str = "KT"
    manufacturer: str = "전체"
    scrb_type_name: str = ""
    network_type: str = ""
    device_nm: str = ""
    plan_name: str = ""
    monthly_fee: int = 0
    release_price: int = 0
    public_support_fee: int = 0
    additional_support_fee: int = 0
    total_support_fee: int = 0
    total_price: int = 0


class KTCrawler:
    """KT 크롤러"""
    
    BASE_URL = "https://shop.kt.com/smart/supportAmtList.do"
    
    def __init__(self, config: Dict[str, Any] = None):
        """초기화"""
        # 기본 설정
        self.config = {
            'headless': True,
            'max_workers': 1,  # KT는 단일 스레드로 시작
            'page_timeout': 10,  # 20 -> 10 속도 개선
            'element_timeout': 5,  # 10 -> 5 속도 개선
            'retry_count': 1,  # 2 -> 1 속도 개선
            'fast_mode': True,
            'output_dir': 'data',
            'checkpoint_interval': 20,
            'use_rich': False,
            'debug': False,
            'delay_between_requests': 0.5,  # 2 -> 0.5 속도 개선
            'first_page_only': False  # 첫 페이지만 수집 (최신 공시 기기)
        }
        
        if config:
            self.config.update(config)
        
        # 디렉토리 생성
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        # 데이터 저장소
        self.all_data: List[DeviceData] = []
        self.data_lock = threading.Lock()
        self.active_drivers = []
        self.active_services = []
        self.drivers_lock = threading.Lock()
        
        # 진행 상태
        self.completed_count = 0
        self.failed_count = 0
        self.total_devices = 0
        self.status_lock = threading.Lock()
        self.start_time = None
        
        # 체크포인트
        self.checkpoint_file = get_checkpoint_path('kt')
        
        # 진행상황 추적
        self.progress_details = {
            'subscription_types': {},
            'rate_plans': {},
            'current_status': ''
        }
    
    def create_driver(self) -> webdriver.Chrome:
        """Chrome 드라이버 생성"""
        options = Options()
        
        # 기본 옵션
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 로깅 비활성화
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        
        # 크래시 방지
        options.add_argument('--disable-crash-reporter')
        
        # 안정성 향상 옵션 추가
        options.add_argument('--disable-features=NetworkService')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-breakpad')
        options.add_argument('--disable-background-networking')
        
        # macOS 특정 안정성 옵션
        import platform
        if platform.system() == 'Darwin':
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--force-device-scale-factor=1')
        
        # 성능 최적화
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # 메모리 최적화
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # User-Agent 설정
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
        # 차단 회피
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        
        # 헤드리스 모드
        if self.config['headless']:
            options.add_argument('--headless=new')
        
        # 성능 최적화 (fast_mode)
        if self.config['fast_mode']:
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'plugins': 2,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2,
                }
            }
            options.add_experimental_option('prefs', prefs)
        
        # ChromeDriver 설정
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # ChromeDriver 다운로드 및 설치
                chromedriver_path = ChromeDriverManager().install()
                
                # macOS에서 quarantine 속성 제거
                if platform.system() == 'Darwin':
                    try:
                        import subprocess
                        subprocess.run(['xattr', '-cr', os.path.dirname(chromedriver_path)], 
                                     capture_output=True, check=False)
                        subprocess.run(['chmod', '+x', chromedriver_path], 
                                     capture_output=True, check=False)
                    except:
                        pass
                
                # Service 객체 생성
                service = Service(
                    executable_path=chromedriver_path,
                    log_output=os.devnull
                )
                
                # Driver 생성
                driver = webdriver.Chrome(service=service, options=options)
                
                # 활성 드라이버 목록에 추가
                with self.drivers_lock:
                    self.active_drivers.append(driver)
                    self.active_services.append(service)
                
                logger.info(f"ChromeDriver 생성 성공 (시도 {attempt + 1}/{max_retries})")
                break
                
            except Exception as e:
                logger.error(f"ChromeDriver 생성 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise Exception(f"ChromeDriver를 시작할 수 없습니다: {str(e)}")
        
        driver.set_page_load_timeout(self.config['page_timeout'])
        driver.implicitly_wait(5)
        
        # JavaScript로 자동화 탐지 방지
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Chrome 속성 위장
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko', 'en-US', 'en']
                });
                
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel'
                });
                
                Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.'
                });
                
                // Permissions API 오버라이드
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            '''
        })
        
        return driver
    
    def check_driver_health(self, driver: webdriver.Chrome) -> bool:
        """WebDriver 상태 확인 - 개선된 버전"""
        try:
            # 1. 드라이버 자체가 살아있는지 확인
            if not driver or not hasattr(driver, 'execute_script'):
                return False

            # 2. 세션이 살아있는지 확인
            driver.current_url  # 세션이 죽었으면 여기서 예외 발생

            # 3. JavaScript 실행으로 페이지 상태 확인
            result = driver.execute_script("return document.readyState")

            # 4. window handle이 유효한지 확인
            current_handle = driver.current_window_handle

            return result is not None and current_handle is not None
        except Exception as e:
            logger.warning(f"WebDriver 상태 확인 실패: {e}")
            return False
    
    def wait_for_page_ready(self, driver: webdriver.Chrome, timeout: int = None):
        """페이지 로딩 대기 - 속도 최적화"""
        if timeout is None:
            timeout = self.config['element_timeout']

        wait_time = min(timeout, 3) if self.config['fast_mode'] else timeout

        try:
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # fast_mode에서는 jQuery 체크 생략
            if not self.config['fast_mode']:
                WebDriverWait(driver, wait_time).until(
                    lambda d: d.execute_script(
                        "return typeof jQuery === 'undefined' || jQuery.active == 0"
                    )
                )
            time.sleep(0.3 if self.config['fast_mode'] else 1)
        except TimeoutException:
            logger.debug("페이지 로딩 타임아웃")
        except:
            pass
    
    def parse_html_data(self, html_content: str) -> List[DeviceData]:
        """HTML 데이터 파싱"""
        data_list = []
        
        # BeautifulSoup 대신 정규식과 문자열 파싱 사용
        # 각 제품을 prodItemCase 단위로 추출 (li 태그가 아닌 cd 속성을 기준으로)
        # HTML에서 각 제품은 li cd="..." 로 시작하고 다음 li cd="..." 전까지가 하나의 제품
        product_items = []
        
        # li cd="..." 패턴 찾기
        li_starts = []
        for match in re.finditer(r'<li cd="([^"]+)">', html_content):
            li_starts.append((match.start(), match.group(1)))
        
        # 각 제품별로 HTML 추출
        for i in range(len(li_starts)):
            start_pos = li_starts[i][0]
            cd = li_starts[i][1]
            
            # 다음 li까지 또는 끝까지
            if i < len(li_starts) - 1:
                end_pos = li_starts[i + 1][0]
            else:
                # 마지막 요소는 </ul>까지
                end_match = html_content.find('</ul>', start_pos)
                end_pos = end_match if end_match > -1 else len(html_content)
            
            li_content = html_content[start_pos:end_pos]
            product_items.append((cd, li_content))
        
        for cd, li_content in product_items:
            try:
                # 기기명 추출
                device_name_match = re.search(r'<strong class="prodName">([^<]+)</strong>', li_content)
                device_name = device_name_match.group(1).strip() if device_name_match else ""
                
                # 공시일 추출
                date_match = re.search(r'<span>(\d{4}\.\d{2}\.\d{2})</span>', li_content)
                date_str = date_match.group(1).replace('.', '-') if date_match else ""
                
                # 출고가 추출
                release_price_match = re.search(r'<div class="tit">출고가</div>[\s\S]*?<div class="conts">([^<]+)</div>', li_content)
                release_price = 0
                if release_price_match:
                    price_text = release_price_match.group(1).replace('원', '').replace(',', '').strip()
                    release_price = int(price_text) if price_text.isdigit() else 0
                
                # 공통지원금 (공시지원금) 추출
                common_support_match = re.search(r'<div class="tit">공통지원금</div>[\s\S]*?<div class="conts">([^<]+)</div>', li_content)
                public_support = 0
                if common_support_match:
                    support_text = common_support_match.group(1).replace('원', '').replace(',', '').strip()
                    public_support = int(support_text) if support_text.isdigit() else 0
                
                # 단말가격 (구매가) 추출
                final_price_match = re.search(r'<div class="tit">단말가격</div>[\s\S]*?<div class="conts">([^<]+)</div>', li_content)
                final_price = 0
                if final_price_match:
                    price_text = final_price_match.group(1).replace('원', '').replace(',', '').strip()
                    final_price = int(price_text) if price_text.isdigit() else 0
                
                # 요금할인 추출 (24개월)
                rate_discount_match = re.search(r'<strong class="tit"[^>]*>요금할인\(24개월\)</strong>[\s\S]*?<div class="conts">\s*([^<]+)', li_content)
                rate_discount_total = 0
                monthly_discount = 0
                if rate_discount_match:
                    discount_text = rate_discount_match.group(1).replace('원', '').replace(',', '').strip()
                    rate_discount_total = int(discount_text) if discount_text.isdigit() else 0
                    # 24개월 총 할인액을 월 할인액으로 변환
                    monthly_discount = rate_discount_total // 24 if rate_discount_total > 0 else 0
                else:
                    # 요금할인이 없는 경우 디버그 로그
                    if self.config.get('debug', False):
                        logger.debug(f"요금할인을 찾을 수 없음: {device_name}")
                        # 다른 패턴으로 재시도
                        alt_match = re.search(r'요금할인[\s\S]*?([0-9,]+)원', li_content)
                        if alt_match:
                            logger.debug(f"대체 패턴으로 발견: {alt_match.group(1)}")
                
                # 전환지원금 (추가지원금) 추출 - KT는 별도로 표시하지 않는 경우가 많음
                conversion_support_match = re.search(r'<div class="tit">전환지원금</div>[\s\S]*?<div class="conts">([^<]+)</div>', li_content)
                additional_support = 0
                if conversion_support_match:
                    support_text = conversion_support_match.group(1).replace('원', '').replace(',', '').strip()
                    additional_support = int(support_text) if support_text.isdigit() else 0
                
                # 제조사 판별
                manufacturer = '기타'
                if '갤럭시' in device_name or 'Galaxy' in device_name.lower():
                    manufacturer = '삼성'
                elif '아이폰' in device_name or 'iPhone' in device_name:
                    manufacturer = '애플'
                elif 'LG' in device_name:
                    manufacturer = 'LG'
                elif '샤오미' in device_name or 'Xiaomi' in device_name or '레드미' in device_name:
                    manufacturer = '샤오미'
                
                # 네트워크 타입 판별
                network_type = '5G'  # 기본값
                if 'LTE' in device_name or '4G' in device_name:
                    network_type = 'LTE'
                elif any(keyword in device_name for keyword in ['워치', 'Watch', '태블릿', 'Tab', 'iPad']):
                    network_type = '기타'
                
                # DeviceData 생성
                device_data = DeviceData(
                    date=date_str,
                    crawled_at=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'),
                    carrier='KT',
                    manufacturer=manufacturer,
                    scrb_type_name='전체',  # 나중에 crawl_data에서 업데이트
                    network_type=network_type,
                    device_nm=device_name,
                    plan_name='요금할인',  # 요금제별 수집 시 업데이트
                    monthly_fee=monthly_discount,  # 월 요금할인액 또는 요금제 월요금
                    release_price=release_price,
                    public_support_fee=public_support,  # 공통지원금 = 공시지원금
                    additional_support_fee=additional_support,  # 전환지원금 = 추가지원금
                    total_support_fee=public_support + additional_support,  # 총 지원금 = 공시지원금 + 추가지원금
                    total_price=final_price
                )
                
                data_list.append(device_data)
                
            except Exception as e:
                logger.error(f"데이터 파싱 오류: {e}")
                if self.config['debug']:
                    traceback.print_exc()
                continue
        
        return data_list
    
    def collect_rate_plans(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """요금제 목록 수집"""
        rate_plans = []
        
        try:
            # 요금제 변경 버튼 클릭
            change_btn_clicked = driver.execute_script("""
                var btn = document.getElementById('btnPayChange');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            """)
            
            if not change_btn_clicked:
                logger.error("요금제 변경 버튼을 찾을 수 없습니다.")
                return rate_plans
            
            time.sleep(2)  # 모달 로딩 대기
            
            # 5G와 LTE 탭별로 요금제 수집
            for network_type in ['5G', 'LTE']:
                # 네트워크 탭 선택
                tab_clicked = driver.execute_script(f"""
                    var tabs = document.querySelectorAll('button');
                    for (var tab of tabs) {{
                        if (tab.textContent.trim() === '{network_type}' && 
                            tab.getAttribute('onclick') && 
                            tab.getAttribute('onclick').includes('fnChangePplTabPopup')) {{
                            tab.click();
                            return true;
                        }}
                    }}
                    return false;
                """)
                
                if not tab_clicked:
                    logger.warning(f"{network_type} 탭을 찾을 수 없습니다.")
                    continue
                
                time.sleep(1)
                
                # 전체 요금제 선택
                all_plans_clicked = driver.execute_script("""
                    var btn = document.getElementById('pplGroupObj_ALL');
                    if (btn && !btn.classList.contains('active')) {
                        btn.click();
                    }
                    return true;
                """)
                
                time.sleep(1)
                
                # 요금제 목록 추출
                plans = driver.execute_script(f"""
                    var plans = [];
                    var items = document.querySelectorAll('.chargeItemCase');
                    
                    items.forEach(function(item) {{
                        var nameElem = item.querySelector('.prodName');
                        var priceElem = item.querySelector('.price');
                        
                        if (nameElem && priceElem) {{
                            var planId = item.getAttribute('id');
                            // prodCopy 제거하고 요금제명만 추출
                            var planNameFull = nameElem.textContent.trim();
                            var copyElem = nameElem.querySelector('.prodCopy');
                            var planName = copyElem ? planNameFull.replace(copyElem.textContent, '').trim() : planNameFull;
                            var priceText = priceElem.textContent.trim();
                            
                            // 월 요금 추출 (예: "월 130,000원" -> 130000)
                            var price = priceText.replace(/[^0-9]/g, '');
                            
                            plans.push({{
                                id: planId,
                                name: planName,
                                monthly_fee: parseInt(price) || 0,
                                network_type: '{network_type}'
                            }});
                        }}
                    }});
                    
                    return plans;
                """)
                
                rate_plans.extend(plans)
                logger.info(f"{network_type} 요금제 {len(plans)}개 수집")
            
            # 모달 닫기
            driver.execute_script("""
                var closeBtn = document.querySelector('.modal-close, .btn-close, [class*="close"]');
                if (closeBtn) closeBtn.click();
            """)
            
        except Exception as e:
            logger.error(f"요금제 수집 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
        
        return rate_plans
    
    def crawl_data_for_plan(self, driver: webdriver.Chrome, plan: Dict[str, Any], sub_type: Dict[str, str] = None, is_first: bool = True) -> List[DeviceData]:
        """특정 요금제에 대한 기기 데이터 수집"""
        devices = []
        
        try:
            # 모달이 닫혀있을 때만 요금제 변경 버튼 클릭
            modal_check = driver.execute_script("""
                // 다양한 모달 셀렉터 확인
                var selectors = [
                    '.layerBody',
                    '.layerContent', 
                    '.chargeListWrap',
                    '.layer_wrap',
                    '.modal-content',
                    '#popupYn'
                ];
                
                var result = {
                    visible: false,
                    modalType: null,
                    buttonExists: false
                };
                
                // 요금제 변경 버튼 확인
                var btn = document.getElementById('btnPayChange');
                result.buttonExists = btn !== null && btn.offsetParent !== null;
                
                // 모달 표시 여부 확인
                for (var i = 0; i < selectors.length; i++) {
                    var elem = document.querySelector(selectors[i]);
                    if (elem && elem.offsetParent !== null) {
                        var style = window.getComputedStyle(elem);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            result.visible = true;
                            result.modalType = selectors[i];
                            break;
                        }
                    }
                }
                
                return result;
            """)
            
            modal_visible = modal_check['visible']
            
            if not modal_check['buttonExists']:
                logger.error("요금제 변경 버튼을 찾을 수 없습니다.")
                return devices
            
            if not modal_visible:
                pay_change_clicked = driver.execute_script("""
                    var btn = document.getElementById('btnPayChange');
                    if (btn) {
                        // console.log('요금제 변경 버튼 발견:', btn);
                        btn.click();
                        return true;
                    }
                    // console.log('요금제 변경 버튼을 찾을 수 없음');
                    return false;
                """)
                
                if not pay_change_clicked:
                    logger.error("요금제 변경 버튼을 찾을 수 없습니다.")
                    return devices
                
                time.sleep(2)  # 모달 로딩 대기
            
            # 모달이 열렸는지 확인
            modal_opened = driver.execute_script("""
                // KT 요금제 선택 모달 확인
                var chargeList = document.querySelector('.chargeListWrap');
                var chargeItems = document.querySelectorAll('.chargeItemCase');
                var layerBody = document.querySelector('.layerBody');
                
                // 다양한 조건으로 모달 확인
                return (chargeList !== null && chargeItems.length > 0) || 
                       (layerBody !== null && layerBody.offsetParent !== null);
            """)
            
            if not modal_opened:
                logger.warning("요금제 선택 모달이 열리지 않았습니다. 계속 진행합니다.")
                # 에러 대신 경고로 변경하고 계속 진행
            
            # 네트워크 타입 선택 (5G/LTE)
            network_tab_clicked = driver.execute_script(f"""
                var networkType = '{plan['network_type']}';
                var tabId = 'TAB_' + networkType;
                var tab = document.getElementById(tabId);
                
                if (tab) {{
                    var button = tab.querySelector('button');
                    if (button && button.getAttribute('aria-selected') !== 'true') {{
                        button.click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if network_tab_clicked:
                time.sleep(1)  # 네트워크 탭 변경 대기
            
            # 전체요금제 버튼 클릭
            all_plans_clicked = driver.execute_script("""
                var allBtn = document.getElementById('pplGroupObj_ALL');
                if (allBtn && allBtn.getAttribute('aria-selected') !== 'true') {
                    allBtn.click();
                    return true;
                }
                return false;
            """)
            
            if all_plans_clicked:
                time.sleep(1)  # 전체요금제 로딩 대기
            
            time.sleep(1)
            
            # 요금제 선택 - 재시도 로직 포함
            plan_selected = False
            for retry in range(3):
                plan_selected = driver.execute_script(f"""
                    try {{
                        // fnPplClick 함수가 있는지 확인
                        if (typeof fnPplClick === 'function') {{
                            fnPplClick('{plan['id']}');
                            return true;
                        }} else {{
                            // 대체 방법: 요금제 요소 직접 클릭
                            var planElem = document.getElementById('{plan['id']}');
                            if (planElem) {{
                                // onclick 속성 확인
                                var onclickAttr = planElem.getAttribute('onclick');
                                if (onclickAttr) {{
                                    eval(onclickAttr);
                                    return true;
                                }} else {{
                                    planElem.click();
                                    return true;
                                }}
                            }}
                        }}
                    }} catch (e) {{
                        // console.error('요금제 선택 오류:', e);
                    }}
                    return false;
                """)
                
                if plan_selected:
                    logger.info(f"요금제 '{plan['name']}' 선택 성공 (시도 {retry + 1}/3)")
                    break
                else:
                    logger.warning(f"요금제 선택 실패, 재시도 {retry + 1}/3")
                    time.sleep(1)
            
            if not plan_selected:
                logger.warning(f"요금제 {plan['name']}를 선택할 수 없습니다.")
                return devices
            
            time.sleep(2)  # 선택 후 대기 시간 증가
            
            # 요금제가 실제로 선택되었는지 확인
            is_selected = driver.execute_script(f"""
                var planElem = document.getElementById('{plan['id']}');
                if (planElem) {{
                    // aria-selected 또는 active 클래스 확인
                    var isActive = planElem.classList.contains('active') || 
                                  planElem.classList.contains('selected');
                    var ariaSelected = planElem.querySelector('[aria-selected="true"]');
                    return isActive || ariaSelected !== null;
                }}
                return false;
            """)
            
            if not is_selected:
                logger.warning(f"요금제 '{plan['name']}'가 선택되지 않았습니다.")
                # 재시도는 하지 않고 계속 진행
            
            # 선택완료 버튼 클릭
            complete_clicked = driver.execute_script("""
                var btn = document.getElementById('btnLayerItem');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            """)
            
            if not complete_clicked:
                logger.warning(f"선택완료 버튼을 찾을 수 없음 - 요금제: {plan['name']}")
                return devices
            
            # 페이지 리로드 감지를 위한 마커 설정
            driver.execute_script("window.ktCrawlerMarker = Date.now();")
            
            time.sleep(3)  # 모달 닫힘 대기
            
            # 페이지가 업데이트되었는지 확인
            self.wait_for_page_ready(driver)
            
            # 페이지 업데이트 대기 (AJAX 또는 페이지 새로고침)
            logger.info("요금제 선택 완료, 페이지 업데이트 대기 중...")
            
            # 페이지가 새로고침되거나 AJAX로 업데이트될 때까지 대기
            update_detected = False
            for i in range(20):  # 최대 20초 대기
                time.sleep(1)
                
                # 페이지 상태 확인
                page_status = driver.execute_script("""
                    return {
                        url: window.location.href,
                        readyState: document.readyState,
                        ajaxActive: typeof jQuery !== 'undefined' ? jQuery.active : 0,
                        prodListExists: document.getElementById('prodList') !== null,
                        itemCount: document.querySelectorAll('#prodList li[cd]').length,
                        markerExists: typeof window.ktCrawlerMarker !== 'undefined',
                        modalClosed: document.querySelector('.layerBody') === null || 
                                    document.querySelector('.layerBody').offsetParent === null
                    };
                """)
                
                logger.debug(f"대기 {i+1}초: items={page_status['itemCount']}, ajax={page_status['ajaxActive']}, modal={not page_status['modalClosed']}")
                
                # 페이지 리로드 감지 (마커가 사라짐)
                if not page_status['markerExists']:
                    logger.info("페이지 리로드 감지")
                    self.wait_for_page_ready(driver)
                    update_detected = True
                    break
                
                # AJAX 완료 및 모달 닫힘 확인
                if page_status['modalClosed'] and page_status['ajaxActive'] == 0 and page_status['readyState'] == 'complete':
                    if page_status['itemCount'] > 0:
                        update_detected = True
                        logger.info(f"페이지 업데이트 완료: {page_status['itemCount']}개 기기 발견")
                        break
            
            if not update_detected:
                logger.warning("페이지 업데이트를 감지하지 못했습니다. 계속 진행합니다.")
            
            # 추가 안정화 대기
            time.sleep(2)
            
            # 기기 목록 가져오기
            prod_list_info = driver.execute_script("""
                var prodList = document.getElementById('prodList');
                var result = {
                    found: prodList !== null,
                    html: prodList ? prodList.outerHTML : null,
                    itemCount: prodList ? prodList.querySelectorAll('li[cd]').length : 0,
                    currentUrl: window.location.href,
                    pageTitle: document.title
                };
                
                // 디버그: 페이지 상태 확인
                if (!prodList) {
                    // prodList가 없으면 다른 가능한 요소들 확인
                    var alternatives = {
                        prodListDiv: document.querySelector('.prodList'),
                        productList: document.querySelector('.productList'),
                        itemList: document.querySelector('.itemList'),
                        anyLiWithCd: document.querySelectorAll('li[cd]').length
                    };
                    result.alternatives = alternatives;
                }
                
                return result;
            """)
            
            logger.info(f"prodList 정보: found={prod_list_info.get('found')}, items={prod_list_info.get('itemCount')}")
            
            prod_list_html = prod_list_info.get('html')
            
            if prod_list_html:
                # 첫 페이지 파싱
                devices = self.parse_html_data_with_plan(prod_list_html, plan)
                logger.info(f"요금제 '{plan['name']}' 페이지 1에서 {len(devices)}개 기기 수집")
                
                # 테스트 모드에서는 기기 수 제한
                if self.config.get('max_devices') and len(devices) > self.config['max_devices']:
                    devices = devices[:self.config['max_devices']]
                    logger.info(f"테스트 모드: {self.config['max_devices']}개 기기로 제한")
                    # 테스트 모드에서는 페이지네이션 건너뛰기
                    page_count = 1
                # first_page_only 모드면 추가 페이지 수집 안함
                elif self.config.get('first_page_only'):
                    logger.info(f"첫 페이지만 수집 모드: {len(devices)}개 기기 수집 완료")
                    return devices
                else:
                    # 페이지네이션 확인 및 처리
                    page_count = driver.execute_script("""
                        var pageLinks = document.querySelectorAll('.pageWrap a[pageno]');
                        var maxPage = 1;
                        pageLinks.forEach(function(link) {
                            var pageNo = parseInt(link.getAttribute('pageno'));
                            if (pageNo > maxPage) maxPage = pageNo;
                        });
                        return maxPage;
                    """)
                    
                    logger.info(f"총 {page_count}개 페이지 발견")
                
                # 2페이지부터 순회
                for page_num in range(2, page_count + 1):
                    # 페이지 이동
                    page_clicked = driver.execute_script(f"""
                        var pageLink = document.querySelector('.pageWrap a[pageno="{page_num}"]');
                        if (pageLink) {{
                            pageLink.click();
                            return true;
                        }}
                        return false;
                    """)
                    
                    if page_clicked:
                        time.sleep(3)  # 페이지 로딩 대기
                        
                        # 해당 페이지의 기기 목록 가져오기
                        page_html = driver.execute_script("""
                            var prodList = document.getElementById('prodList');
                            return prodList ? prodList.outerHTML : null;
                        """)
                        
                        if page_html:
                            page_devices = self.parse_html_data_with_plan(page_html, plan)
                            devices.extend(page_devices)
                            logger.info(f"페이지 {page_num}에서 {len(page_devices)}개 기기 추가 수집")
                
                logger.info(f"요금제 '{plan['name']}'에서 총 {len(devices)}개 기기 수집 완료")
            
        except TimeoutException as e:
            logger.error(f"요금제 '{plan.get('name', 'Unknown')}' 처리 중 타임아웃: {e}")
            return devices
        except WebDriverException as e:
            logger.error(f"WebDriver 오류 - 요금제 '{plan.get('name', 'Unknown')}': {e}")
            # WebDriver 오류 시 복구 시도
            try:
                driver.refresh()
                self.wait_for_page_ready(driver)
            except:
                pass
            return devices
        except Exception as e:
            logger.error(f"요금제별 데이터 수집 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
        
        return devices
    
    def parse_html_data_with_plan(self, html_content: str, plan: Dict[str, Any]) -> List[DeviceData]:
        """요금제 정보를 포함한 HTML 데이터 파싱"""
        devices = self.parse_html_data(html_content)
        
        # 각 기기에 요금제 정보 추가
        for device in devices:
            device.plan_name = plan['name']
            device.monthly_fee = plan['monthly_fee']
            device.network_type = plan['network_type']
        
        return devices
    
    def crawl_data(self, driver: webdriver.Chrome) -> int:
        """데이터 크롤링"""
        extracted_count = 0
        self.current_driver = driver  # 현재 드라이버 참조 저장
        
        # 가입유형 정보
        subscription_types = [
            # {'value': '01', 'name': '신규가입'},  # 이미 수집 완료
            {'value': '02', 'name': '번호이동'},
            {'value': '04', 'name': '기기변경'}
        ]
        
        try:
            # 먼저 메인 페이지로 이동
            try:
                driver.get("https://shop.kt.com/")
            except Exception as e:
                logger.warning(f"메인 페이지 로드 실패: {e}")
                # 바로 지원금 페이지로 이동 시도
            
            time.sleep(2)
            
            # 그 다음 지원금 페이지로 이동
            driver.get(self.BASE_URL)
            self.wait_for_page_ready(driver)
            
            # 페이지가 로드될 때까지 대기
            time.sleep(5)
            
            # 초기 정렬 설정 - 최근 공시 순
            initial_sort = driver.execute_script("""
                var sortBtn = document.getElementById('sortProd1');
                if (sortBtn && !sortBtn.classList.contains('active')) {
                    sortBtn.click();
                    return true;
                }
                return false;
            """)
            
            if initial_sort:
                logger.info("초기 정렬: 최근 공시 순")
                time.sleep(2)
            
            # 각 가입유형별로 처리
            logger.info(f"처리할 가입유형 목록: {[s['name'] for s in subscription_types]}")
            
            # 완료된 가입유형 초기화
            if not hasattr(self, 'completed_scrb_types'):
                self.completed_scrb_types = []
            if not hasattr(self, 'current_scrb_type'):
                self.current_scrb_type = None
            if not hasattr(self, 'current_plan_index'):
                self.current_plan_index = None
            
            for sub_idx, sub_type in enumerate(subscription_types):
                # 이미 완료된 가입유형 건너뛰기
                if sub_type['name'] in self.completed_scrb_types:
                    logger.info(f"가입유형 '{sub_type['name']}' 건너뛰기 (이미 완료)")
                    continue
                
                logger.info(f"가입유형 처리 시작 ({sub_idx + 1}/{len(subscription_types)}): {sub_type['name']}")
                self.current_scrb_type = sub_type['name']
                try:
                    # 가입유형 간 WebDriver 갱신 (첫 번째 제외)
                    if sub_idx > 0:
                        logger.info(f"가입유형 간 WebDriver 세션 갱신 중...")
                        
                        # 기존 드라이버 종료
                        try:
                            driver.quit()
                        except:
                            pass
                        
                        # 새 드라이버 생성
                        time.sleep(3)
                        self.current_driver = self.create_driver()
                        driver = self.current_driver
                        
                        # 페이지 재로드
                        driver.get(self.BASE_URL)
                        self.wait_for_page_ready(driver)
                        time.sleep(5)
                        
                        logger.info("WebDriver 세션 갱신 완료")
                    
                    print(f"\n가입유형: {sub_type['name']} 처리 시작")
                    
                    # 가입유형 선택
                    type_selected = driver.execute_script(f"""
                        var select = document.getElementById('sbscTypeCd');
                        if (select) {{
                            select.value = '{sub_type['value']}';
                            // change 이벤트 발생
                            var event = new Event('change', {{ bubbles: true }});
                            select.dispatchEvent(event);
                            return true;
                        }}
                        return false;
                    """)
                    
                    if not type_selected:
                        logger.error(f"가입유형 선택 실패: {sub_type['name']}")
                        continue
                    
                    time.sleep(3)  # 페이지 업데이트 대기
                    
                    # 정렬 옵션 설정 - 최근 공시 순
                    sort_applied = driver.execute_script("""
                    // 최근 공시 순 정렬 버튼 클릭
                    var sortBtn = document.getElementById('sortProd1');
                    if (sortBtn && !sortBtn.classList.contains('active')) {
                        sortBtn.click();
                        return true;
                    }
                    
                    // 이미 선택되어 있거나 버튼이 없는 경우에도 진행
                    return false;
                    """)
                    
                    if sort_applied:
                        logger.info("최근 공시 순으로 정렬 적용")
                        time.sleep(2)  # 정렬 후 페이지 갱신 대기
                    
                    # 1. 요금제 목록 수집
                    print("요금제 목록 수집 중...")
                    
                    rate_plans = self.collect_rate_plans(driver)
                    
                    if not rate_plans:
                        logger.warning(f"{sub_type['name']}에서 요금제를 찾을 수 없습니다. 기본 모드로 수집합니다.")
                        # 기본 크롤링 모드 (요금제 구분 없이)
                        prod_list_html = driver.execute_script("""
                            var prodList = document.getElementById('prodList');
                            return prodList ? prodList.outerHTML : null;
                        """)
                        
                        if prod_list_html:
                            devices = self.parse_html_data(prod_list_html)
                            # 가입유형 정보 추가
                            for device in devices:
                                device.scrb_type_name = sub_type['name']
                            
                            with self.data_lock:
                                self.all_data.extend(devices)
                            extracted_count += len(devices)
                    else:
                        # 2. 각 요금제별로 데이터 수집
                        print(f"{len(rate_plans)}개 요금제 발견")
                        
                        # 가입유형별 진행상황 추적
                        sub_type_progress = []
                        
                        # 재개 지점 결정
                        start_index = 0
                        if self.current_scrb_type == sub_type['name'] and self.current_plan_index is not None:
                            start_index = self.current_plan_index + 1
                            logger.info(f"요금제 인덱스 {start_index}부터 재개")
                        
                        # 테스트 모드에서는 요금제 수 제한
                        if self.config.get('max_plans'):
                            rate_plans = rate_plans[:self.config['max_plans']]
                            print(f"테스트 모드: {len(rate_plans)}개 요금제만 수집")
                        
                        for i, plan in enumerate(rate_plans):
                            # 재개 지점 이전의 요금제는 건너뛰기
                            if i < start_index:
                                continue
                            
                            self.current_plan_index = i
                            # WebDriver 상태 확인 및 재생성 (개선된 로직)
                            should_refresh = False

                            # 20개 요금제마다 정기 갱신 (30개 -> 20개로 줄임)
                            if i > 0 and i % 20 == 0:
                                should_refresh = True
                                logger.info(f"정기 WebDriver 세션 갱신 (요금제 {i}/{len(rate_plans)})")
                            # 매 요금제마다 상태 체크
                            elif i > 0 and not self.check_driver_health(driver):
                                should_refresh = True
                                logger.warning(f"WebDriver 상태 불량 감지, 재생성 필요 (요금제 {i}/{len(rate_plans)})")

                            if should_refresh:
                                logger.info("WebDriver 세션을 갱신합니다...")

                                # 현재 URL 저장
                                current_url = None
                                try:
                                    current_url = driver.current_url
                                except:
                                    current_url = self.BASE_URL

                                # 기존 드라이버 종료 (강제 종료)
                                try:
                                    driver.quit()
                                except:
                                    pass

                                # 잠시 대기 (프로세스 정리 시간)
                                time.sleep(3)

                                # 새 드라이버 생성 (최대 3회 시도)
                                for retry in range(3):
                                    try:
                                        self.current_driver = self.create_driver()
                                        driver = self.current_driver
                                        break
                                    except Exception as e:
                                        logger.error(f"드라이버 재생성 실패 ({retry+1}/3): {e}")
                                        if retry < 2:
                                            time.sleep(5)
                                        else:
                                            raise Exception("드라이버 재생성 실패")

                                # 페이지 재로드
                                driver.get(current_url)
                                self.wait_for_page_ready(driver)
                                time.sleep(3)

                                # 가입유형 재선택
                                try:
                                    driver.execute_script(f"""
                                        var select = document.getElementById('sbscTypeCd');
                                        if (select) {{
                                            select.value = '{sub_type['value']}';
                                            var event = new Event('change', {{ bubbles: true }});
                                            select.dispatchEvent(event);
                                        }}
                                    """)
                                    time.sleep(2)
                                except Exception as e:
                                    logger.error(f"가입유형 재선택 실패: {e}")

                                logger.info("WebDriver 세션 갱신 완료")
                            
                            plan_start_time = time.time()
                            
                            print(f"\n[{i+1}/{len(rate_plans)}] 요금제: {plan['name']}")
                            print(f"- 네트워크: {plan['network_type']}")
                            print(f"- 월 요금: {plan['monthly_fee']:,}원")
                            
                            try:
                                devices = self.crawl_data_for_plan(driver, plan, sub_type, is_first=True)
                            except Exception as e:
                                logger.error(f"요금제 {plan['name']} 크롤링 중 오류: {e}")
                                logger.error(f"오류 상세: 가입유형={sub_type['name']}, 인덱스={i}, 네트워크={plan['network_type']}")
                                if self.config.get('debug'):
                                    traceback.print_exc()
                                
                                # WebDriver 세션 오류인 경우 재생성 시도 (개선된 로직)
                                error_msg = str(e).lower()
                                if any(err in error_msg for err in ['invalid session id', 'chrome not reachable',
                                                                     'connection refused', 'target window already closed',
                                                                     'no such window', 'session not created']):
                                    logger.warning("WebDriver 세션 오류 감지, 재생성 시도...")

                                    # 기존 드라이버 강제 종료
                                    try:
                                        driver.quit()
                                    except:
                                        pass

                                    time.sleep(5)  # 프로세스 정리 시간 충분히 부여

                                    # 새 드라이버 생성 (최대 3회 시도)
                                    for retry in range(3):
                                        try:
                                            self.current_driver = self.create_driver()
                                            driver = self.current_driver
                                            driver.get(self.BASE_URL)
                                            self.wait_for_page_ready(driver)
                                            time.sleep(3)

                                            # 가입유형 재선택
                                            driver.execute_script(f"""
                                                var select = document.getElementById('sbscTypeCd');
                                                if (select) {{
                                                    select.value = '{sub_type['value']}';
                                                    var event = new Event('change', {{ bubbles: true }});
                                                    select.dispatchEvent(event);
                                                }}
                                            """)
                                            time.sleep(2)

                                            # 재시도
                                            devices = self.crawl_data_for_plan(driver, plan, sub_type, is_first=True)
                                            break
                                        except Exception as retry_error:
                                            logger.error(f"재시도 실패 ({retry+1}/3): {retry_error}")
                                            if retry == 2:  # 마지막 시도 실패
                                                devices = []
                                            else:
                                                time.sleep(5)
                                else:
                                    devices = []
                            
                            # 가입유형 정보 추가
                            for device in devices:
                                device.scrb_type_name = sub_type['name']
                            
                            with self.data_lock:
                                self.all_data.extend(devices)
                            
                            extracted_count += len(devices)
                            
                            # 요금제별 결과 표시
                            plan_elapsed = time.time() - plan_start_time
                            sub_type_progress.append({
                                'plan_name': plan['name'],
                                'network_type': plan['network_type'],
                                'monthly_fee': plan['monthly_fee'],
                                'device_count': len(devices),
                                'elapsed_time': plan_elapsed
                            })
                            
                            # 체크포인트 저장 (10개 요금제마다 또는 100개 기기마다)
                            if i % 10 == 0 or len(self.all_data) % 100 == 0:
                                self.save_checkpoint()
                                logger.info(f"체크포인트 저장: {len(self.all_data)}개 기기 (가입유형: {sub_type['name']}, 요금제 {i+1}/{len(rate_plans)})")
                            
                            print(f"[OK] 수집 완료: {len(devices)}개 기기 ({plan_elapsed:.1f}초)")
                            
                            # 다음 요금제 처리 전 잠시 대기
                            if i < len(rate_plans) - 1:
                                time.sleep(self.config.get('delay_between_requests', 0.5))
                    
                    
                    # 모든 요금제 처리 완료 후 모달 닫기
                    try:
                        driver.execute_script("""
                            var closeBtn = document.querySelector('.modal_closeBtn, .btnCloseLayer, .btn-close');
                            if (closeBtn) {
                                closeBtn.click();
                            }
                        """)
                        time.sleep(1)
                    except:
                        pass

# 가입유형별 요약 표시
                    self._print_subscription_type_summary(sub_type['name'], sub_type_progress)
                    
                    total_devices_for_type = sum(p['device_count'] for p in sub_type_progress) if 'sub_type_progress' in locals() else 0
                    logger.info(f"{sub_type['name']} 완료: {total_devices_for_type}개 수집")
                    
                    # 전체 진행상황 업데이트
                    self.progress_details['subscription_types'][sub_type['name']] = {
                        'total_devices': total_devices_for_type,
                        'rate_plans': sub_type_progress if 'sub_type_progress' in locals() else []
                    }
                    
                    # 가입유형 완료 표시
                    self.completed_scrb_types.append(sub_type['name'])
                    self.current_scrb_type = None
                    self.current_plan_index = None
                    logger.info(f"가입유형 '{sub_type['name']}' 완료")
                
                except Exception as sub_e:
                    logger.error(f"{sub_type['name']} 처리 중 오류: {sub_e}")
                    if self.config['debug']:
                        traceback.print_exc()
                    # 오류가 발생해도 다음 가입유형 처리를 계속함
                    continue
            
            logger.info(f"총 추출된 기기 수: {extracted_count}")
            
            # 최종 진행상황 요약 표시
            self._print_final_progress_summary()
            
        except Exception as e:
            logger.error(f"크롤링 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
        
        return extracted_count
    
    def _print_subscription_type_summary(self, sub_type_name: str, progress: List[Dict[str, Any]]):
        """가입유형별 요약 표시"""
        if not progress:
            return
        
        total_devices = sum(p['device_count'] for p in progress)
        total_time = sum(p['elapsed_time'] for p in progress)
        
        if False:
            # 요약 테이블 생성
            table = Table(title=f"[{sub_type_name}] 수집 결과", show_header=True, header_style="bold cyan")
            table.add_column("요금제", style="yellow")
            table.add_column("네트워크", justify="center")
            table.add_column("월 요금", justify="right", style="green")
            table.add_column("수집 기기", justify="right", style="cyan")
            table.add_column("소요 시간", justify="right")
            
            for p in progress:
                table.add_row(
                    p['plan_name'],
                    p['network_type'],
                    f"{p['monthly_fee']:,}원",
                    f"{p['device_count']}개",
                    f"{p['elapsed_time']:.1f}초"
                )
            
            table.add_row(
                "[bold]총계[/bold]", "", "",
                f"[bold]{total_devices}개[/bold]",
                f"[bold]{total_time:.1f}초[/bold]",
                style="bold magenta"
            )
            
            logger.info("\n")
            logger.info(table)
        else:
            print(f"\n=== [{sub_type_name}] 수집 결과 ===")
            print(f"총 수집 기기: {total_devices}개")
            print(f"총 소요 시간: {total_time:.1f}초")
            print("-" * 50)
    
    def _print_final_progress_summary(self):
        """최종 진행상황 요약"""
        if not self.progress_details['subscription_types']:
            return
        
        # 가입유형별 통계
        print("\n=== 전체 수집 현황 요약 ===")
        for sub_type, data in self.progress_details['subscription_types'].items():
            print(f"\n{sub_type}:")
            for plan in data['rate_plans']:
                print(f"  • {plan['plan_name']}: {plan['device_count']}개")
            print(f"  합계: {data['total_devices']}개")
    
    def save_checkpoint(self):
        """체크포인트 저장 - 개선된 버전"""
        checkpoint_data = {
            'completed': self.completed_count,
            'failed': self.failed_count,
            'data': [vars(d) for d in self.all_data],
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'current_scrb_type': getattr(self, 'current_scrb_type', None),
            'current_plan_index': getattr(self, 'current_plan_index', None),
            'completed_scrb_types': getattr(self, 'completed_scrb_types', []),
            'progress': self.progress_details
        }
        
        # 원자적 쓰기를 위해 임시 파일 사용
        temp_file = self.checkpoint_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            # 원자적 파일 교체
            temp_file.replace(self.checkpoint_file)
            logger.debug(f"체크포인트 저장 완료 (데이터: {len(checkpoint_data.get('data', []))}개)")
        except Exception as e:
            logger.error(f"체크포인트 저장 실패: {e}")
            # 임시 파일 정리
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def load_checkpoint(self) -> bool:
        """체크포인트 로드 - 개선된 버전"""
        if not os.path.exists(self.checkpoint_file):
            return False
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                data = pickle.load(f)
            
            self.completed_count = data.get('completed', 0)
            self.failed_count = data.get('failed', 0)
            self.all_data = [DeviceData(**d) for d in data.get('data', [])]
            
            # 재개 정보 복원
            self.current_scrb_type = data.get('current_scrb_type')
            self.current_plan_index = data.get('current_plan_index')
            self.completed_scrb_types = data.get('completed_scrb_types', [])
            self.progress_details = data.get('progress', self.progress_details)
            
            logger.info(f"체크포인트 로드: {data['timestamp']}")
            if self.current_scrb_type:
                logger.info(f"재개 지점: {self.current_scrb_type} - 요금제 인덱스 {self.current_plan_index}")
            return True
        except Exception as e:
            logger.error(f"체크포인트 로드 실패: {e}")
            return False
    
    def save_results(self):
        """결과 저장"""
        if not self.all_data:
            logger.warning("저장할 데이터가 없습니다.")
            return []
        
        # DataFrame 생성
        df = pd.DataFrame([vars(d) for d in self.all_data])
        
        # 파일 저장
        timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
        saved_files = []
        
        # CSV
        csv_file = get_raw_data_path('kt', 'csv')
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        saved_files.append(str(csv_file))
        
        # 파일 경로 출력
        logger.info(f"[OK] CSV 저장: {csv_file}")
        
        # 통계 출력
        self._print_statistics(df)
        
        return saved_files
    
    def _print_statistics(self, df: pd.DataFrame):
        """통계 출력"""
        print("\n" + "="*50)
        print("크롤링 결과 요약")
        print("="*50)
        print(f"총 데이터: {len(df):,}개")
        print(f"가입유형: {df['scrb_type_name'].nunique()}개")
        print(f"제조사: {df['manufacturer'].nunique()}개")
        print(f"네트워크: {df['network_type'].nunique()}개")
        print(f"디바이스: {df['device_nm'].nunique()}개")
        print(f"요금제: {df['plan_name'].nunique()}개")
        print(f"평균 출고가: {df['release_price'].mean():,.0f}원")
        print(f"평균 공시지원금: {df['public_support_fee'].mean():,.0f}원")
        print(f"최대 공시지원금: {df['public_support_fee'].max():,.0f}원")
        
        # 가입유형별 통계
        if df['scrb_type_name'].nunique() > 1:
            print("\n가입유형별 통계:")
            for scrb_type in df['scrb_type_name'].unique():
                type_df = df[df['scrb_type_name'] == scrb_type]
                print(f"- {scrb_type}: {len(type_df):,}개 (평균 공시지원금: {type_df['public_support_fee'].mean():,.0f}원)")
    
    def run(self):
        """메인 실행"""
        self.start_time = time.time()
        driver = None
        
        try:
            # 헤더 출력
            print("\n" + "="*60)
            print("KT 공시지원금 크롤러")
            print("버전 v1.0")
            print("="*60)
            
            # 체크포인트 확인
            if self.config.get('resume') and self.load_checkpoint():
                logger.info("체크포인트에서 재개합니다.")
            
            # 드라이버 생성
            driver = None
            try:
                driver = self.create_driver()
                
                # 크롤링 시작
                print("\n공시지원금 데이터 수집 시작")
                
                # 데이터 크롤링
                extracted_count = self.crawl_data(driver)
            finally:
                # 드라이버 정리
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            
            with self.status_lock:
                self.completed_count = 1 if extracted_count > 0 else 0
                self.failed_count = 0 if extracted_count > 0 else 1
                self.total_devices = extracted_count
            
            # 결과 저장
            saved_files = self.save_results()
            
            # 완료 메시지
            elapsed = time.time() - self.start_time
            
            print(f"\n크롤링 완료!")
            print(f"소요 시간: {elapsed:.1f}초")
            print(f"총 수집 데이터: {self.total_devices}개")
            
            # 체크포인트 삭제
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            
            return saved_files
            
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            self.save_checkpoint()
            if self.all_data:
                saved_files = self.save_results()
                return saved_files
            return []
        except Exception as e:
            logger.error(f"크롤링 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
            self.save_checkpoint()
            if self.all_data:
                saved_files = self.save_results()
                return saved_files
            return []
        finally:
            # 모든 리소스 정리
            self.cleanup_resources()
    
    def cleanup_resources(self):
        """리소스 정리 - 개선된 버전"""
        logger.info("리소스 정리 시작")
        
        # 활성 드라이버 정리
        if hasattr(self, 'active_drivers') and hasattr(self, 'drivers_lock'):
            with self.drivers_lock:
                drivers_to_clean = self.active_drivers.copy()
                self.active_drivers.clear()
                
                for driver in drivers_to_clean:
                    try:
                        driver.quit()
                        logger.debug("드라이버 종료됨")
                    except Exception as e:
                        logger.debug(f"드라이버 종료 실패: {e}")
        
        # 활성 서비스 정리
        if hasattr(self, 'active_services') and hasattr(self, 'drivers_lock'):
            with self.drivers_lock:
                services_to_clean = self.active_services.copy()
                self.active_services.clear()
                
                for service in services_to_clean:
                    try:
                        service.stop()
                        logger.debug("서비스 종료됨")
                    except Exception as e:
                        logger.debug(f"서비스 종료 실패: {e}")
        
        logger.info("리소스 정리 완료")
    
    def __del__(self):
        """객체 소멸자 - 모든 드라이버 정리"""
        try:
            self.cleanup_resources()
        except Exception as e:
            logger.debug(f"소멸자 오류: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='KT 공시지원금 크롤러',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 기본 옵션
    parser.add_argument('--headless', action='store_true', 
                        help='헤드리스 모드 실행 (기본값)')
    parser.add_argument('--show-browser', action='store_true',
                        help='브라우저 표시')
    
    # 기타 옵션
    parser.add_argument('--output', type=str, default='data',
                        help='출력 디렉토리 (기본값: data)')
    parser.add_argument('--resume', action='store_true',
                        help='체크포인트에서 재개')
    parser.add_argument('--debug', action='store_true',
                        help='디버그 모드')
    parser.add_argument('--no-rich', action='store_true',
                        help='Rich UI 비활성화')
    parser.add_argument('--test', action='store_true',
                        help='테스트 모드 (제한된 데이터만 수집)')
    parser.add_argument('--max-plans', type=int, default=None,
                        help='수집할 최대 요금제 수')
    parser.add_argument('--max-devices', type=int, default=None,
                        help='요금제당 수집할 최대 기기 수')
    parser.add_argument('--first-page-only', action='store_true',
                        help='각 요금제의 첫 페이지만 수집 (최신 공시 기기)')

    args = parser.parse_args()
    
    # 설정
    config = {
        'headless': True if not args.show_browser else False,
        'output_dir': args.output,
        'resume': args.resume,
        'debug': args.debug,
        'use_rich': RICH_AVAILABLE and not args.no_rich,
        'test': args.test,
        'max_plans': args.max_plans if args.max_plans else (3 if args.test else None),
        'max_devices': args.max_devices if args.max_devices else (5 if args.test else None),
        'first_page_only': args.first_page_only
    }
    
    # 크롤러 실행
    crawler = KTCrawler(config)
    saved_files = crawler.run()
    
    sys.exit(0 if saved_files else 1)


if __name__ == '__main__':
    # 인자 없이 실행시 기본 실행
    if len(sys.argv) == 1:
        config = {}
        crawler = KTCrawler(config)
        crawler.run()
    else:
        main()