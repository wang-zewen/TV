#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iyf.tv 视频网站专用爬虫 - 终极版
使用多种方案绕过 403：curl_cffi > cloudscraper > Playwright > requests
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import time
import random
import logging
from functools import wraps
from typing import Dict, List, Optional, Any
import hashlib
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ========== 多种 HTTP 客户端支持 ==========

# 优先级1: curl_cffi (最强，模拟真实 Chrome 的 TLS 指纹)
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
    logger.info("✅ curl_cffi 可用 (推荐，TLS 指纹模拟)")
except ImportError:
    HAS_CURL_CFFI = False
    logger.warning("⚠️  curl_cffi 未安装")

# 优先级2: cloudscraper (中等，绕过 Cloudflare)
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
    logger.info("✅ cloudscraper 可用 (Cloudflare 绕过)")
except ImportError:
    HAS_CLOUDSCRAPER = False
    logger.warning("⚠️  cloudscraper 未安装")

# 优先级3: Playwright (强大但慢，真实浏览器)
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
    logger.info("✅ Playwright 可用 (真实浏览器)")
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.warning("⚠️  Playwright 未安装")

# 优先级4: requests (基础)
try:
    import requests
    HAS_REQUESTS = True
    logger.info("✅ requests 可用 (基础)")
except ImportError:
    HAS_REQUESTS = False
    logger.error("❌ requests 未安装，无法运行")
    sys.exit(1)


class SimpleCache:
    """简单的内存缓存"""

    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            value, expire_time = self.cache[key]
            if datetime.now() < expire_time:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        expire_time = datetime.now() + timedelta(seconds=self.ttl)
        self.cache[key] = (value, expire_time)

    def clear(self):
        self.cache.clear()


class MockResponse:
    """模拟响应对象"""
    def __init__(self, text, status_code=200, url=''):
        self.text = text
        self.status_code = status_code
        self.url = url
        self.content = text.encode('utf-8') if isinstance(text, str) else text


class IYFSpiderUltimate:
    """iyf.tv 专用爬虫 - 终极版，支持多种 HTTP 客户端"""

    # 超级 User-Agent 池（最新版本）
    USER_AGENTS = [
        # Chrome 121 Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        # Chrome 120 Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Chrome 121 Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        # Chrome 120 Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox 122 Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        # Firefox 121 Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari 17.2 Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        # Edge 120 Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        # Chrome 121 Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]

    def __init__(self, base_url='https://www.iyf.tv', cache_ttl=300):
        self.base_url = base_url
        self.cache = SimpleCache(ttl=cache_ttl)
        self.request_count = 0
        self.last_request_time = time.time()
        self.playwright_browser = None
        self.playwright_instance = None

        # 选择最佳的 HTTP 客户端
        self.http_client = self._select_best_client()
        logger.info(f"🔧 使用 HTTP 客户端: {self.http_client}")

        # 初始化
        self._init_session()

    def _select_best_client(self):
        """选择最佳的 HTTP 客户端"""
        if HAS_CURL_CFFI:
            return 'curl_cffi'
        elif HAS_CLOUDSCRAPER:
            return 'cloudscraper'
        elif HAS_PLAYWRIGHT:
            return 'playwright'
        else:
            return 'requests'

    def _init_session(self):
        """初始化 session"""
        if self.http_client == 'curl_cffi':
            logger.info("初始化 curl_cffi session (TLS 指纹模拟)")
            self.session = None  # curl_cffi 不需要 session

        elif self.http_client == 'cloudscraper':
            logger.info("初始化 cloudscraper session")
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )

        elif self.http_client == 'playwright':
            logger.info("初始化 Playwright browser")
            self._init_playwright()

        else:
            logger.info("初始化 requests session")
            self.session = requests.Session()

        # 测试访问
        try:
            logger.info(f"测试访问: {self.base_url}")
            response = self.get(self.base_url, retry=1)
            if response and response.status_code == 200:
                logger.info(f"✅ 初始化成功！")
            else:
                logger.warning(f"⚠️  初始化测试失败，但继续运行...")
        except Exception as e:
            logger.warning(f"⚠️  初始化测试异常: {e}")

    def _init_playwright(self):
        """初始化 Playwright"""
        if not HAS_PLAYWRIGHT:
            return

        try:
            self.playwright_instance = sync_playwright().start()
            self.playwright_browser = self.playwright_instance.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            logger.info("✅ Playwright browser 启动成功")
        except Exception as e:
            logger.error(f"❌ Playwright 初始化失败: {e}")
            self.playwright_browser = None

    def _get_enhanced_headers(self, referer=None):
        """获取增强的请求头"""
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        }

        if referer:
            headers['Referer'] = referer

        return headers

    def _rate_limit(self, min_interval=1.0):
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get(self, url, retry=3, cache_key=None, **kwargs):
        """
        发送 GET 请求 - 终极版，支持多种客户端
        """
        # 检查缓存
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"📦 使用缓存: {cache_key}")
                return cached

        # 速率限制
        self._rate_limit(random.uniform(0.8, 1.5))

        # 尝试多种方法
        methods = self._get_request_methods()

        for attempt in range(retry):
            for method_name, method_func in methods:
                try:
                    logger.info(f"🌐 [{attempt+1}/{retry}] {method_name}: {url}")

                    if attempt > 0:
                        delay = random.uniform(2, 4) * (attempt + 1)
                        logger.info(f"⏳ 等待 {delay:.1f} 秒...")
                        time.sleep(delay)

                    response = method_func(url, **kwargs)

                    if response and response.status_code == 200:
                        logger.info(f"✅ 成功 ({method_name})")
                        self.request_count += 1

                        # 缓存
                        if cache_key:
                            self.cache.set(cache_key, response)

                        return response

                    elif response and response.status_code == 403:
                        logger.warning(f"🚫 403 ({method_name})，尝试下一个方法...")
                        continue

                except Exception as e:
                    logger.warning(f"❌ {method_name} 失败: {e}")
                    continue

        logger.error(f"❌ 所有方法均失败: {url}")
        return None

    def _get_request_methods(self):
        """获取可用的请求方法列表（按优先级排序）"""
        methods = []

        if HAS_CURL_CFFI:
            methods.append(('curl_cffi', self._request_with_curl_cffi))

        if HAS_CLOUDSCRAPER and self.session:
            methods.append(('cloudscraper', self._request_with_cloudscraper))

        if HAS_PLAYWRIGHT and self.playwright_browser:
            methods.append(('playwright', self._request_with_playwright))

        if HAS_REQUESTS:
            methods.append(('requests', self._request_with_requests))

        return methods

    def _request_with_curl_cffi(self, url, **kwargs):
        """使用 curl_cffi 发送请求（模拟真实 Chrome TLS 指纹）"""
        headers = self._get_enhanced_headers()

        response = curl_requests.get(
            url,
            headers=headers,
            timeout=20,
            impersonate="chrome120",  # 模拟 Chrome 120 的 TLS 指纹
            allow_redirects=True,
        )

        # 包装成统一的响应对象
        return MockResponse(response.text, response.status_code, url)

    def _request_with_cloudscraper(self, url, **kwargs):
        """使用 cloudscraper 发送请求"""
        headers = self._get_enhanced_headers()
        self.session.headers.update(headers)

        response = self.session.get(url, timeout=20, allow_redirects=True)
        response.encoding = 'utf-8'
        return response

    def _request_with_playwright(self, url, **kwargs):
        """使用 Playwright 发送请求（真实浏览器）"""
        if not self.playwright_browser:
            raise Exception("Playwright browser 未初始化")

        context = self.playwright_browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
        )

        page = context.new_page()

        try:
            # 访问页面
            response = page.goto(url, timeout=30000, wait_until='domcontentloaded')

            # 等待一下，确保页面加载
            time.sleep(random.uniform(1, 2))

            # 获取内容
            content = page.content()
            status_code = response.status if response else 200

            # 关闭
            page.close()
            context.close()

            return MockResponse(content, status_code, url)

        except Exception as e:
            page.close()
            context.close()
            raise e

    def _request_with_requests(self, url, **kwargs):
        """使用普通 requests 发送请求"""
        headers = self._get_enhanced_headers()

        if not hasattr(self, 'session') or self.session is None:
            self.session = requests.Session()

        self.session.headers.update(headers)

        response = self.session.get(url, timeout=20, allow_redirects=True)
        response.encoding = 'utf-8'
        return response

    def _make_cache_key(self, *args):
        """生成缓存键"""
        key_string = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_list(self, page=1, type_id=None):
        """获取视频列表"""
        logger.info(f"📋 获取列表: page={page}, type_id={type_id}")

        cache_key = self._make_cache_key('list', page, type_id or 'all')
        urls_to_try = self._generate_list_urls(page, type_id)

        response = None
        for idx, url in enumerate(urls_to_try):
            logger.info(f"尝试 URL {idx+1}/{len(urls_to_try)}: {url}")
            response = self.get(url, cache_key=cache_key if idx == 0 else None)
            if response and response.status_code == 200:
                break
            time.sleep(0.5)

        if not response:
            logger.error("❌ 所有 URL 格式均无法访问")
            return []

        return self._parse_video_list(response.text)

    def _generate_list_urls(self, page, type_id):
        """生成可能的列表页 URL"""
        urls = []

        if type_id:
            urls.extend([
                f"{self.base_url}/vodshow/{type_id}--------{page}---.html",
                f"{self.base_url}/vodshow/{type_id}-{page}.html",
                f"{self.base_url}/vodtype/{type_id}-{page}.html",
                f"{self.base_url}/list/{type_id}/{page}.html",
                f"{self.base_url}/show/{type_id}--{page}.html",
                f"{self.base_url}/type/{type_id}/{page}.html",
            ])
        else:
            urls.extend([
                f"{self.base_url}/vodshow/1--------{page}---.html",
                f"{self.base_url}/vodshow/1-{page}.html",
                f"{self.base_url}/list/{page}.html",
                f"{self.base_url}/",
            ])

        return urls

    def _parse_video_list(self, html):
        """解析视频列表"""
        soup = BeautifulSoup(html, 'html.parser')

        selectors = [
            '.module-item',
            '.module-items .module-item',
            '.stui-vodlist__box',
            '.video-item',
            '.vodlist_item',
            'li.col-md-6',
            'li.col-lg-6',
            '.stui-vodlist li',
            'a.module-item-pic',
            '.myui-vodlist li',
        ]

        video_items = []
        for selector in selectors:
            video_items = soup.select(selector)
            if video_items:
                logger.info(f"✅ 选择器: '{selector}' -> {len(video_items)} 项")
                break

        if not video_items:
            logger.warning("⚠️  未找到视频项")
            return []

        videos = []
        for idx, item in enumerate(video_items[:50], 1):
            try:
                video = self._parse_video_item(item)
                if video:
                    videos.append(video)
            except Exception as e:
                logger.debug(f"[{idx}] 解析失败: {e}")
                continue

        logger.info(f"✅ 成功解析 {len(videos)} 个视频")
        return videos

    def _parse_video_item(self, item):
        """解析单个视频项"""
        link_tag = (
            item.select_one('a.module-item-pic') or
            item.select_one('a[href*="/voddetail/"]') or
            item.select_one('a[href*="/detail/"]') or
            item.find('a', href=True)
        )

        if not link_tag:
            return None

        href = link_tag.get('href', '')
        vod_id = self._extract_vod_id(href)
        if not vod_id:
            return None

        vod_name = self._extract_title(link_tag, item) or f"视频_{vod_id}"
        vod_pic = self._extract_image(item)
        vod_remarks = self._extract_remarks(item)

        return {
            'vod_id': vod_id,
            'vod_name': vod_name,
            'vod_pic': vod_pic,
            'vod_remarks': vod_remarks,
            'vod_time': datetime.now().strftime('%Y-%m-%d'),
        }

    def _extract_vod_id(self, href):
        """提取视频 ID"""
        patterns = [
            r'/voddetail/(\d+)\.html',
            r'/detail/(\d+)\.html',
            r'/video/(\d+)\.html',
            r'/play/(\d+)',
            r'/(\d+)\.html',
            r'id[=/](\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        return None

    def _extract_title(self, link_tag, item):
        """提取标题"""
        title = link_tag.get('title', '').strip()
        if title:
            return title

        title_selectors = [
            '.module-item-title',
            '.stui-vodlist__title',
            '.video-title',
            'h3', 'h4', '.title',
        ]

        for selector in title_selectors:
            title_tag = item.select_one(selector)
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title
        return ''

    def _extract_image(self, item):
        """提取图片"""
        img_selectors = ['img.lazy', 'img.lazyload', '.module-item-pic img', 'img']

        for selector in img_selectors:
            img_tag = item.select_one(selector)
            if img_tag:
                pic = (
                    img_tag.get('data-original') or
                    img_tag.get('data-src') or
                    img_tag.get('src', '')
                )

                if pic:
                    if not pic.startswith('http'):
                        if pic.startswith('//'):
                            pic = 'https:' + pic
                        elif pic.startswith('/'):
                            pic = self.base_url + pic
                    return pic
        return ''

    def _extract_remarks(self, item):
        """提取备注"""
        remarks_selectors = [
            '.module-item-text',
            '.pic-text',
            '.stui-vodlist__text',
            '.remarks',
        ]

        for selector in remarks_selectors:
            remarks_tag = item.select_one(selector)
            if remarks_tag:
                text = remarks_tag.get_text().strip()
                if text:
                    return text
        return 'HD'

    def get_detail(self, vod_id):
        """获取视频详情"""
        logger.info(f"📄 获取详情: vod_id={vod_id}")

        cache_key = self._make_cache_key('detail', vod_id)

        urls_to_try = [
            f"{self.base_url}/voddetail/{vod_id}.html",
            f"{self.base_url}/detail/{vod_id}.html",
            f"{self.base_url}/video/{vod_id}.html",
        ]

        response = None
        for url in urls_to_try:
            response = self.get(url, cache_key=cache_key)
            if response and response.status_code == 200:
                break
            time.sleep(0.3)

        if not response:
            logger.error(f"❌ 无法获取详情: vod_id={vod_id}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        detail = {
            'vod_id': vod_id,
            'vod_name': self._extract_detail_title(soup),
            'vod_pic': self._extract_detail_pic(soup),
            'vod_actor': self._extract_info(soup, ['主演', 'actor']),
            'vod_director': self._extract_info(soup, ['导演', 'director']),
            'vod_content': self._extract_content(soup),
            'vod_year': self._extract_info(soup, ['年份', 'year']),
            'vod_area': self._extract_info(soup, ['地区', 'area']),
            'vod_lang': self._extract_info(soup, ['语言', 'lang']),
            'type_name': self._extract_info(soup, ['类型', 'type']),
            'vod_remarks': self._extract_info(soup, ['状态', 'remarks']) or 'HD',
        }

        play_data = self._extract_play_data(soup, vod_id, response.text)
        detail.update(play_data)

        logger.info(f"✅ 详情: {detail['vod_name']}")
        return detail

    def _extract_detail_title(self, soup):
        """提取详情页标题"""
        selectors = [
            '.module-info-heading h1',
            '.page-title',
            '.stui-content__title',
            'h1',
        ]

        for selector in selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                return title_tag.get_text().strip()

        if soup.title:
            return soup.title.string.split('-')[0].strip()
        return ''

    def _extract_detail_pic(self, soup):
        """提取封面"""
        selectors = [
            '.module-item-pic img',
            '.video-cover img',
            '.stui-content__thumb img',
            'img.lazy',
        ]

        for selector in selectors:
            img_tag = soup.select_one(selector)
            if img_tag:
                pic = img_tag.get('data-original') or img_tag.get('data-src') or img_tag.get('src', '')
                if pic:
                    if not pic.startswith('http'):
                        if pic.startswith('//'):
                            pic = 'https:' + pic
                        elif pic.startswith('/'):
                            pic = self.base_url + pic
                    return pic
        return ''

    def _extract_info(self, soup, keywords):
        """提取信息"""
        for keyword in keywords:
            patterns = [
                soup.find('span', text=re.compile(keyword, re.I)),
                soup.find(text=re.compile(f'{keyword}[:：]', re.I)),
            ]

            for element in patterns:
                if element:
                    parent = element.parent if hasattr(element, 'parent') else element
                    if parent:
                        text = parent.get_text()
                        for kw in keywords:
                            text = re.sub(f'{kw}[:：]?', '', text, flags=re.I)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text and text != '-':
                            return text
        return ''

    def _extract_content(self, soup):
        """提取剧情"""
        selectors = [
            '.module-info-introduction',
            '.detail-content',
            '.stui-content__detail',
            '.introduction',
        ]

        for selector in selectors:
            content_tag = soup.select_one(selector)
            if content_tag:
                text = content_tag.get_text().strip()
                text = re.sub(r'\s+', ' ', text)
                return text[:500]
        return ''

    def _extract_play_data(self, soup, vod_id, html):
        """提取播放数据"""
        # 简化版：只提取基本播放信息
        return {
            'vod_play_from': '默认',
            'vod_play_url': '',
        }

    def search(self, keyword, page=1):
        """搜索视频"""
        logger.info(f"🔍 搜索: keyword='{keyword}', page={page}")

        cache_key = self._make_cache_key('search', keyword, page)

        urls_to_try = [
            f"{self.base_url}/vodsearch/-------------.html?wd={keyword}&page={page}",
            f"{self.base_url}/search.html?wd={keyword}&page={page}",
        ]

        response = None
        for url in urls_to_try:
            response = self.get(url, cache_key=cache_key)
            if response and response.status_code == 200:
                break
            time.sleep(0.3)

        if not response:
            logger.error(f"❌ 搜索失败")
            return []

        videos = self._parse_video_list(response.text)
        logger.info(f"✅ 搜索到 {len(videos)} 个结果")
        return videos

    def get_stats(self):
        """获取统计信息"""
        return {
            'request_count': self.request_count,
            'cache_size': len(self.cache.cache),
            'http_client': self.http_client,
            'has_curl_cffi': HAS_CURL_CFFI,
            'has_cloudscraper': HAS_CLOUDSCRAPER,
            'has_playwright': HAS_PLAYWRIGHT,
        }

    def close(self):
        """关闭资源"""
        if self.playwright_browser:
            self.playwright_browser.close()
        if self.playwright_instance:
            self.playwright_instance.stop()


# 初始化爬虫
logger.info("=" * 60)
logger.info("初始化 IYF Spider Ultimate...")
logger.info("=" * 60)
spider = IYFSpiderUltimate()


@app.route('/')
def index():
    """首页"""
    stats = spider.get_stats()

    return jsonify({
        "code": 1,
        "msg": "iyf.tv 视频 API - 终极版",
        "version": "4.0.0 Ultimate",
        "http_client": spider.http_client,
        "stats": stats,
        "endpoints": {
            "列表": "/api.php/provide/vod/?pg=1",
            "详情": "/api.php/provide/vod/?ac=detail&ids=1",
            "搜索": "/api.php/provide/vod/?wd=关键词",
            "测试": "/test",
        }
    })


@app.route('/api.php/provide/vod/', methods=['GET'])
def provide_vod():
    """TVBox API 接口"""
    action = request.args.get('ac', 'list')
    type_id = request.args.get('t')
    page = int(request.args.get('pg', 1))
    keyword = request.args.get('wd', '')
    ids = request.args.get('ids', '')

    response = {
        "code": 1,
        "msg": "数据列表",
        "page": page,
        "list": []
    }

    try:
        if action == 'detail' and ids:
            for vod_id in ids.split(','):
                detail = spider.get_detail(vod_id.strip())
                if detail:
                    response['list'].append(detail)

        elif keyword:
            results = spider.search(keyword, page)
            for video in results[:10]:
                detail = spider.get_detail(video['vod_id'])
                if detail:
                    response['list'].append(detail)

        else:
            videos = spider.get_list(page, type_id)
            response['list'] = videos

        response['total'] = len(response['list'])

    except Exception as e:
        logger.error(f"❌ API 异常: {e}", exc_info=True)
        response['code'] = 0
        response['msg'] = str(e)

    return jsonify(response)


@app.route('/test', methods=['GET'])
def test():
    """测试接口"""
    results = {
        "版本": "4.0.0 Ultimate",
        "HTTP客户端": spider.http_client,
        "测试结果": {}
    }

    # 测试列表
    try:
        videos = spider.get_list(1)
        results["测试结果"]["列表"] = {
            "状态": "✅" if videos else "❌",
            "数量": len(videos),
        }
    except Exception as e:
        results["测试结果"]["列表"] = {"状态": "❌", "错误": str(e)}

    # 测试详情
    if videos:
        try:
            detail = spider.get_detail(videos[0]['vod_id'])
            results["测试结果"]["详情"] = {
                "状态": "✅" if detail else "❌",
                "标题": detail.get('vod_name', '') if detail else '',
            }
        except Exception as e:
            results["测试结果"]["详情"] = {"状态": "❌", "错误": str(e)}

    return jsonify(results)


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🎬 iyf.tv 终极版 API 启动")
    logger.info(f"   HTTP 客户端: {spider.http_client}")
    logger.info("=" * 60)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        spider.close()
