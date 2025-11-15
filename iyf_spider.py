#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iyf.tv 视频网站专用爬虫 - 高级优化版
增强反爬措施、智能重试、Cloudflare绕过
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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

# 尝试导入 cloudscraper (如果不可用则降级到 requests)
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    print("[警告] cloudscraper 未安装，将使用普通 requests (可能遇到 Cloudflare 拦截)")
    print("       安装命令: pip install cloudscraper")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


class SimpleCache:
    """简单的内存缓存"""

    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl  # 缓存时间（秒）

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


def retry_on_failure(max_retries=3, delay=2, backoff=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} 失败 (已重试 {retries} 次): {e}")
                        raise

                    logger.warning(f"{func.__name__} 失败，{current_delay}秒后重试 ({retries}/{max_retries}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


class IYFSpider:
    """iyf.tv 专用爬虫 - 高级优化版"""

    # User-Agent 池
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(self, base_url='https://www.iyf.tv', cache_ttl=300, use_proxy=False):
        self.base_url = base_url
        self.cache = SimpleCache(ttl=cache_ttl)
        self.use_proxy = use_proxy
        self.request_count = 0
        self.last_request_time = time.time()

        # 创建 session
        if HAS_CLOUDSCRAPER:
            logger.info("使用 cloudscraper 创建 session (支持 Cloudflare 绕过)")
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        else:
            logger.info("使用普通 requests session")
            self.session = requests.Session()

        # 设置请求头
        self._update_headers()

        # 初始化 session
        self._init_session()

    def _update_headers(self):
        """更新请求头"""
        self.headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        }
        self.session.headers.update(self.headers)

    def _init_session(self):
        """初始化 session，访问首页获取 cookies"""
        try:
            logger.info(f"初始化 session，访问首页: {self.base_url}")
            response = self.session.get(
                self.base_url,
                timeout=15,
                allow_redirects=True
            )

            if response.status_code == 200:
                logger.info(f"✅ Session 初始化成功 (cookies: {len(self.session.cookies)} 个)")
                # 随机延迟
                time.sleep(random.uniform(0.5, 1.5))
            else:
                logger.warning(f"⚠️  首页访问异常，状态码: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Session 初始化失败: {e}")

    def _rate_limit(self, min_interval=1.0):
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get(self, url, retry=3, cache_key=None, **kwargs):
        """
        发送 GET 请求 - 增强版

        参数:
            url: 目标 URL
            retry: 重试次数
            cache_key: 缓存键（如果提供，将使用缓存）
        """
        # 检查缓存
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"📦 使用缓存: {cache_key}")
                return cached

        # 速率限制
        self._rate_limit(random.uniform(0.5, 1.5))

        for attempt in range(retry):
            try:
                logger.info(f"🌐 请求: {url} (尝试 {attempt + 1}/{retry})")

                # 重试时增加延迟
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    logger.info(f"⏳ 等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                    # 更换 User-Agent
                    self._rotate_user_agent()

                # 发送请求
                response = self.session.get(
                    url,
                    timeout=20,
                    allow_redirects=True,
                    **kwargs
                )

                self.request_count += 1

                # 检查状态码
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    logger.info(f"✅ 成功 (状态码: {response.status_code}, 大小: {len(response.text)} bytes)")

                    # 缓存结果
                    if cache_key:
                        self.cache.set(cache_key, response)

                    return response

                elif response.status_code == 403:
                    logger.warning(f"🚫 403 禁止访问")
                    if attempt < retry - 1:
                        logger.info("🔄 尝试更换 User-Agent 和重置 session")
                        self._rotate_user_agent()
                        # 严重时重新初始化 session
                        if attempt > 1:
                            self._init_session()
                        continue

                elif response.status_code == 404:
                    logger.warning(f"❌ 404 页面不存在")
                    return None

                elif response.status_code in [500, 502, 503, 504]:
                    logger.warning(f"⚠️  服务器错误: {response.status_code}")
                    if attempt < retry - 1:
                        continue

                else:
                    logger.warning(f"⚠️  异常状态码: {response.status_code}")

            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  请求超时")
                if attempt < retry - 1:
                    continue

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 连接错误: {e}")
                if attempt < retry - 1:
                    continue

            except requests.exceptions.RequestException as e:
                logger.warning(f"❌ 请求异常: {e}")
                if attempt < retry - 1:
                    continue

            except Exception as e:
                logger.error(f"💥 未知错误: {e}")
                break

        logger.error(f"❌ 所有重试均失败: {url}")
        return None

    def _rotate_user_agent(self):
        """轮换 User-Agent"""
        new_ua = random.choice(self.USER_AGENTS)
        self.session.headers['User-Agent'] = new_ua
        logger.debug(f"🔄 切换 User-Agent: {new_ua[:60]}...")

    def _make_cache_key(self, *args):
        """生成缓存键"""
        key_string = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_list(self, page=1, type_id=None):
        """获取视频列表"""
        logger.info(f"📋 获取列表: page={page}, type_id={type_id}")

        # 生成缓存键
        cache_key = self._make_cache_key('list', page, type_id or 'all')

        # 尝试多种 URL 格式
        urls_to_try = self._generate_list_urls(page, type_id)

        response = None
        for idx, url in enumerate(urls_to_try):
            logger.info(f"尝试 URL 格式 {idx + 1}/{len(urls_to_try)}: {url}")
            response = self.get(url, cache_key=cache_key if idx == 0 else None)
            if response and response.status_code == 200:
                logger.info(f"✅ URL 格式有效")
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
                f"{self.base_url}/",  # 首页
            ])

        return urls

    def _parse_video_list(self, html):
        """解析视频列表"""
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试多种选择器
        selectors = [
            '.module-item',
            '.module-items .module-item',
            '.stui-vodlist__box',
            '.video-item',
            '.vodlist_item',
            'li.col-md-6',
            'li.col-lg-6',
            'li.col-lg-8',
            '.stui-vodlist li',
            'a.module-item-pic',
            '.myui-vodlist li',
            '.video-list .item',
        ]

        video_items = []
        for selector in selectors:
            video_items = soup.select(selector)
            if video_items:
                logger.info(f"✅ 选择器匹配: '{selector}' -> {len(video_items)} 项")
                break

        if not video_items:
            logger.warning("⚠️  未找到视频项，尝试分析页面结构...")
            self._debug_page_structure(soup)
            return []

        videos = []
        for idx, item in enumerate(video_items[:50], 1):
            try:
                video = self._parse_video_item(item)
                if video:
                    videos.append(video)
                    logger.debug(f"  [{idx}] {video['vod_name']}")
            except Exception as e:
                logger.warning(f"  [{idx}] 解析失败: {e}")
                continue

        logger.info(f"✅ 成功解析 {len(videos)} 个视频")
        return videos

    def _debug_page_structure(self, soup):
        """调试页面结构"""
        logger.debug("=" * 60)
        logger.debug("页面结构分析:")

        # 查找主要容器
        main_divs = soup.find_all('div', class_=True, limit=30)
        classes = [d.get('class') for d in main_divs]
        logger.debug(f"主要 div 类名: {classes[:10]}")

        # 查找所有链接
        links = soup.find_all('a', href=True, limit=20)
        hrefs = [a.get('href') for a in links]
        logger.debug(f"主要链接: {hrefs[:5]}")

        logger.debug("=" * 60)

    def _parse_video_item(self, item):
        """解析单个视频项"""
        # 查找链接
        link_tag = (
            item.select_one('a.module-item-pic') or
            item.select_one('a.lazyload') or
            item.select_one('a[href*="/voddetail/"]') or
            item.select_one('a[href*="/detail/"]') or
            item.select_one('a[href*="/video/"]') or
            item.select_one('a.stui-vodlist__thumb') or
            item.select_one('div.module-item-pic a') or
            item.select_one('.video-pic a') or
            item.find('a', href=True)
        )

        if not link_tag:
            return None

        href = link_tag.get('href', '')

        # 提取视频 ID
        vod_id = self._extract_vod_id(href)
        if not vod_id:
            return None

        # 提取标题
        vod_name = self._extract_title(link_tag, item)
        if not vod_name:
            vod_name = f"视频_{vod_id}"

        # 提取图片
        vod_pic = self._extract_image(item)

        # 提取备注
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
            r'/vod/detail/id/(\d+)',
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
        # 从链接的 title 属性
        title = link_tag.get('title', '').strip()
        if title:
            return title

        # 从各种标题标签
        title_selectors = [
            '.module-item-title',
            '.module-item-titlebox',
            '.stui-vodlist__title',
            '.video-title',
            'h3',
            'h4',
            'h5',
            '.title',
            '.name',
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
        img_selectors = [
            'img.lazy',
            'img.lazyload',
            '.module-item-pic img',
            '.video-pic img',
            'img',
        ]

        for selector in img_selectors:
            img_tag = item.select_one(selector)
            if img_tag:
                pic = (
                    img_tag.get('data-original') or
                    img_tag.get('data-src') or
                    img_tag.get('data-echo') or
                    img_tag.get('data-lazy-src') or
                    img_tag.get('src', '')
                )

                if pic:
                    # 处理相对路径
                    if not pic.startswith('http'):
                        if pic.startswith('//'):
                            pic = 'https:' + pic
                        elif pic.startswith('/'):
                            pic = self.base_url + pic
                    return pic

        return ''

    def _extract_remarks(self, item):
        """提取备注信息"""
        remarks_selectors = [
            '.module-item-text',
            '.module-item-note',
            '.pic-text',
            '.stui-vodlist__text',
            '.video-tag',
            '.remarks',
            '.status',
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

        # 生成缓存键
        cache_key = self._make_cache_key('detail', vod_id)

        # 尝试多种详情页 URL
        urls_to_try = [
            f"{self.base_url}/voddetail/{vod_id}.html",
            f"{self.base_url}/detail/{vod_id}.html",
            f"{self.base_url}/video/{vod_id}.html",
            f"{self.base_url}/vod/detail/id/{vod_id}.html",
            f"{self.base_url}/index.php/vod/detail/id/{vod_id}.html",
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

        # 提取详情
        detail = {
            'vod_id': vod_id,
            'vod_name': self._extract_detail_title(soup),
            'vod_pic': self._extract_detail_pic(soup),
            'vod_actor': self._extract_info(soup, ['主演', 'actor', '演员']),
            'vod_director': self._extract_info(soup, ['导演', 'director']),
            'vod_content': self._extract_content(soup),
            'vod_year': self._extract_info(soup, ['年份', 'year', '时间']),
            'vod_area': self._extract_info(soup, ['地区', 'area']),
            'vod_lang': self._extract_info(soup, ['语言', 'lang']),
            'type_name': self._extract_info(soup, ['类型', 'type', '分类']),
            'vod_remarks': self._extract_info(soup, ['状态', 'remarks', '更新']) or 'HD',
        }

        # 提取播放链接
        play_data = self._extract_play_data(soup, vod_id, response.text)
        detail.update(play_data)

        logger.info(f"✅ 详情获取成功: {detail['vod_name']}")
        return detail

    def _extract_detail_title(self, soup):
        """提取详情页标题"""
        selectors = [
            '.module-info-heading h1',
            '.page-title',
            '.video-info-header h1',
            '.stui-content__title',
            '.video-title',
            'h1.title',
            'h1',
        ]

        for selector in selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title

        # 从页面标题提取
        if soup.title:
            title_text = soup.title.string or ''
            return title_text.split('-')[0].split('_')[0].strip()

        return ''

    def _extract_detail_pic(self, soup):
        """提取详情页封面"""
        selectors = [
            '.module-item-pic img',
            '.video-cover img',
            '.stui-content__thumb img',
            '.detail-pic img',
            '.lazyload',
            'img.lazy',
        ]

        for selector in selectors:
            img_tag = soup.select_one(selector)
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

    def _extract_info(self, soup, keywords):
        """提取指定关键词的信息"""
        for keyword in keywords:
            # 方法1: 查找包含关键词的标签
            patterns = [
                soup.find('span', class_=re.compile(keyword, re.I)),
                soup.find('div', class_=re.compile(keyword, re.I)),
                soup.find('label', text=re.compile(keyword, re.I)),
                soup.find('span', text=re.compile(keyword, re.I)),
                soup.find(text=re.compile(f'{keyword}[:：]', re.I)),
            ]

            for element in patterns:
                if element:
                    # 获取父元素的文本
                    parent = element.parent if hasattr(element, 'parent') else element
                    if parent:
                        text = parent.get_text()
                        # 清理关键词
                        for kw in keywords:
                            text = re.sub(f'{kw}[:：]?', '', text, flags=re.I)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text and text != '-':
                            return text

        return ''

    def _extract_content(self, soup):
        """提取剧情介绍"""
        selectors = [
            '.module-info-introduction',
            '.module-info-introduction-content',
            '.detail-content',
            '.video-info-aux',
            '.stui-content__detail',
            '.desc',
            '.introduction',
            '.content',
            '.summary',
        ]

        for selector in selectors:
            content_tag = soup.select_one(selector)
            if content_tag:
                text = content_tag.get_text().strip()
                # 清理多余空白
                text = re.sub(r'\s+', ' ', text)
                # 截取前500字符
                return text[:500] if text else ''

        return ''

    def _extract_play_data(self, soup, vod_id, html):
        """提取播放数据"""
        logger.info(f"🎬 提取播放链接...")

        play_from_list = []
        play_url_list = []

        # 方法1: 从 JavaScript 变量提取
        js_data = self._extract_from_javascript(html)
        if js_data:
            play_from_list.append(js_data.get('play_from', '默认'))
            play_url_list.append(js_data.get('play_url', ''))

        # 方法2: 从播放列表提取
        play_lists = self._extract_from_play_list(soup)
        for play_list in play_lists:
            play_from_list.append(play_list.get('name', '线路'))
            play_url_list.append(play_list.get('urls', ''))

        # 方法3: 从 iframe 提取
        iframe_url = self._extract_from_iframe(soup)
        if iframe_url and not play_url_list:
            play_from_list.append('iframe')
            play_url_list.append(f'播放${iframe_url}')

        # 组合结果
        if play_from_list:
            logger.info(f"✅ 找到 {len(play_from_list)} 个播放源")
            return {
                'vod_play_from': '$$$'.join(play_from_list),
                'vod_play_url': '$$$'.join(play_url_list),
            }

        logger.warning("⚠️  未找到播放链接")
        return {
            'vod_play_from': '默认',
            'vod_play_url': '',
        }

    def _extract_from_javascript(self, html):
        """从 JavaScript 代码中提取播放信息"""
        # 查找 player 配置
        patterns = [
            r'player_\w+\s*=\s*(\{[^}]+\})',
            r'var\s+player\s*=\s*(\{[^}]+\})',
            r'"url"\s*:\s*"([^"]+)"',
            r"'url'\s*:\s*'([^']+)'",
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
            r'(https?://[^\s"\']+\.mp4[^\s"\']*)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                for match in matches:
                    # 尝试解析 JSON
                    if match.strip().startswith('{'):
                        try:
                            data = json.loads(match)
                            if 'url' in data:
                                return {
                                    'play_from': '默认',
                                    'play_url': f"播放${data['url']}"
                                }
                        except:
                            pass
                    # 直接是 URL
                    elif match.startswith('http'):
                        return {
                            'play_from': '默认',
                            'play_url': f'播放${match}'
                        }

        return None

    def _extract_from_play_list(self, soup):
        """从播放列表中提取"""
        play_lists = []

        # 查找播放标签页
        tab_selectors = [
            '.module-tab-item',
            '.play-source-tab',
            '.stui-vodlist__head h3',
        ]

        # 查找播放列表
        list_selectors = [
            '.module-play-list',
            '.module-blocklist',
            '.stui-content__playlist',
            '.play-list',
        ]

        # 查找所有播放列表容器
        for list_selector in list_selectors:
            containers = soup.select(list_selector)

            for idx, container in enumerate(containers):
                # 获取线路名称
                tab_name = f'线路{idx + 1}'

                # 尝试从标题获取
                title = container.find_previous(['h3', 'h4', 'span'])
                if title:
                    tab_name = title.get_text().strip() or tab_name

                # 提取集数链接
                episodes = []
                links = container.select('a')

                for ep_idx, link in enumerate(links[:100], 1):
                    ep_name = link.get_text().strip() or f'第{ep_idx}集'
                    ep_url = link.get('href', '')

                    if ep_url:
                        if not ep_url.startswith('http'):
                            ep_url = self.base_url + ep_url
                        episodes.append(f"{ep_name}${ep_url}")

                if episodes:
                    play_lists.append({
                        'name': tab_name,
                        'urls': '#'.join(episodes)
                    })

        return play_lists

    def _extract_from_iframe(self, soup):
        """从 iframe 中提取播放链接"""
        iframe_selectors = [
            'iframe#player',
            'iframe.player',
            'iframe[src*="player"]',
            'iframe',
        ]

        for selector in iframe_selectors:
            iframe = soup.select_one(selector)
            if iframe and iframe.get('src'):
                iframe_url = iframe['src']
                if not iframe_url.startswith('http'):
                    if iframe_url.startswith('//'):
                        iframe_url = 'https:' + iframe_url
                    elif iframe_url.startswith('/'):
                        iframe_url = self.base_url + iframe_url
                return iframe_url

        return None

    def search(self, keyword, page=1):
        """搜索视频"""
        logger.info(f"🔍 搜索: keyword='{keyword}', page={page}")

        # 生成缓存键
        cache_key = self._make_cache_key('search', keyword, page)

        # 尝试多种搜索 URL
        urls_to_try = [
            f"{self.base_url}/vodsearch/-------------.html?wd={keyword}&page={page}",
            f"{self.base_url}/vodsearch/{keyword}----------{page}---.html",
            f"{self.base_url}/search.html?wd={keyword}&page={page}",
            f"{self.base_url}/index.php/vod/search.html?wd={keyword}&page={page}",
            f"{self.base_url}/search/{keyword}/{page}.html",
        ]

        response = None
        for url in urls_to_try:
            response = self.get(url, cache_key=cache_key)
            if response and response.status_code == 200:
                break
            time.sleep(0.3)

        if not response:
            logger.error(f"❌ 搜索失败: keyword='{keyword}'")
            return []

        # 使用与列表相同的解析逻辑
        videos = self._parse_video_list(response.text)
        logger.info(f"✅ 搜索到 {len(videos)} 个结果")

        return videos

    def get_stats(self):
        """获取统计信息"""
        return {
            'request_count': self.request_count,
            'cache_size': len(self.cache.cache),
            'cookies': len(self.session.cookies),
            'has_cloudscraper': HAS_CLOUDSCRAPER,
        }


# 初始化爬虫
logger.info("=" * 60)
logger.info("初始化 IYF Spider...")
logger.info("=" * 60)
spider = IYFSpider()


@app.route('/')
def index():
    """首页"""
    stats = spider.get_stats()

    return jsonify({
        "code": 1,
        "msg": "iyf.tv 视频 API 服务 - 高级优化版",
        "site": spider.base_url,
        "version": "3.0.0",
        "status": "运行中",
        "stats": stats,
        "endpoints": {
            "列表": "/api.php/provide/vod/?pg=1",
            "分类": "/api.php/provide/vod/?t=1&pg=1",
            "详情": "/api.php/provide/vod/?ac=detail&ids=1",
            "搜索": "/api.php/provide/vod/?wd=关键词",
            "测试": "/test",
            "统计": "/stats"
        },
        "categories": {
            "1": "电影",
            "2": "电视剧",
            "3": "综艺",
            "4": "动漫",
            "5": "纪录片",
        },
        "features": [
            "✅ Cloudflare 绕过 (cloudscraper)" if HAS_CLOUDSCRAPER else "⚠️  基础模式 (建议安装 cloudscraper)",
            "✅ 智能缓存机制",
            "✅ 指数退避重试",
            "✅ User-Agent 池",
            "✅ Cookie 持久化",
            "✅ 速率限制",
            "✅ 多种 URL 格式支持",
            "✅ 完善的错误处理",
        ]
    })


@app.route('/stats')
def stats():
    """统计信息"""
    return jsonify({
        "code": 1,
        "stats": spider.get_stats()
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
        "pagecount": 1,
        "limit": 20,
        "total": 0,
        "list": []
    }

    try:
        # 详情查询
        if action == 'detail' and ids:
            logger.info(f"\n{'='*60}")
            logger.info(f"API 请求: 详情查询 (ids={ids})")
            logger.info(f"{'='*60}")

            for vod_id in ids.split(','):
                detail = spider.get_detail(vod_id.strip())
                if detail:
                    response['list'].append(detail)

            response['total'] = len(response['list'])

        # 搜索
        elif keyword:
            logger.info(f"\n{'='*60}")
            logger.info(f"API 请求: 搜索 (keyword='{keyword}', page={page})")
            logger.info(f"{'='*60}")

            results = spider.search(keyword, page)

            # 获取详情（限制数量以提高速度）
            for video in results[:10]:
                detail = spider.get_detail(video['vod_id'])
                if detail:
                    response['list'].append(detail)

            response['total'] = len(response['list'])

        # 列表
        else:
            logger.info(f"\n{'='*60}")
            logger.info(f"API 请求: 列表 (type={type_id}, page={page})")
            logger.info(f"{'='*60}")

            videos = spider.get_list(page, type_id)
            response['list'] = videos
            response['total'] = len(videos)

    except Exception as e:
        logger.error(f"❌ API 异常: {e}", exc_info=True)
        response['code'] = 0
        response['msg'] = f"查询出错: {str(e)}"

    return jsonify(response)


@app.route('/test', methods=['GET'])
def test():
    """测试接口"""
    logger.info("\n" + "=" * 60)
    logger.info("开始测试 iyf.tv 接口 - 高级优化版")
    logger.info("=" * 60)

    results = {
        "网站": spider.base_url,
        "版本": "3.0.0 (高级优化版)",
        "测试时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "环境": {
            "cloudscraper": "✅ 已安装" if HAS_CLOUDSCRAPER else "❌ 未安装 (建议: pip install cloudscraper)",
        },
        "测试结果": {}
    }

    videos = []

    # 测试1: 获取列表
    logger.info("\n[测试 1/3] 获取视频列表...")
    try:
        videos = spider.get_list(1)
        results["测试结果"]["列表获取"] = {
            "状态": "✅ 成功" if videos else "❌ 失败",
            "数量": len(videos),
            "示例": videos[0] if videos else None
        }
        logger.info(f"✅ 结果: 找到 {len(videos)} 个视频")
        if videos:
            logger.info(f"   示例: {videos[0]['vod_name']}")
    except Exception as e:
        results["测试结果"]["列表获取"] = {
            "状态": "❌ 失败",
            "错误": str(e)
        }
        logger.error(f"❌ 失败: {e}")

    # 测试2: 获取详情
    logger.info("\n[测试 2/3] 获取视频详情...")
    if videos:
        try:
            vod_id = videos[0]['vod_id']
            detail = spider.get_detail(vod_id)

            has_play_url = False
            if detail and detail.get('vod_play_url'):
                has_play_url = detail['vod_play_url'].strip() != ''

            results["测试结果"]["详情获取"] = {
                "状态": "✅ 成功" if detail else "❌ 失败",
                "视频ID": vod_id,
                "标题": detail.get('vod_name', '') if detail else '',
                "播放链接": "✅ 已找到" if has_play_url else "⚠️  未找到"
            }

            if detail:
                logger.info(f"✅ 结果: {detail.get('vod_name', '')}")
                logger.info(f"   播放链接: {'找到' if has_play_url else '未找到'}")
        except Exception as e:
            results["测试结果"]["详情获取"] = {
                "状态": "❌ 失败",
                "错误": str(e)
            }
            logger.error(f"❌ 失败: {e}")
    else:
        results["测试结果"]["详情获取"] = {
            "状态": "⏭️  跳过",
            "原因": "列表为空"
        }
        logger.warning("⏭️  跳过 (列表为空)")

    # 测试3: 搜索功能
    logger.info("\n[测试 3/3] 测试搜索功能...")
    try:
        search_results = spider.search("爱情")
        results["测试结果"]["搜索功能"] = {
            "状态": "✅ 成功" if search_results else "❌ 失败",
            "关键词": "爱情",
            "数量": len(search_results),
            "示例": search_results[0] if search_results else None
        }
        logger.info(f"✅ 结果: 找到 {len(search_results)} 个结果")
    except Exception as e:
        results["测试结果"]["搜索功能"] = {
            "状态": "❌ 失败",
            "错误": str(e)
        }
        logger.error(f"❌ 失败: {e}")

    # 添加统计信息
    results["统计"] = spider.get_stats()

    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60 + "\n")

    return jsonify(results)


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🎬 iyf.tv 视频 API 服务启动 - 高级优化版 v3.0")
    logger.info("=" * 60)
    logger.info(f"目标网站: {spider.base_url}")
    logger.info(f"本地地址: http://127.0.0.1:5000")
    logger.info(f"API 接口: http://127.0.0.1:5000/api.php/provide/vod/")
    logger.info(f"测试接口: http://127.0.0.1:5000/test")
    logger.info("=" * 60)
    logger.info("\n🚀 优化功能:")
    logger.info(f"  {'✅' if HAS_CLOUDSCRAPER else '⚠️ '} Cloudflare 绕过 {'(已启用)' if HAS_CLOUDSCRAPER else '(未安装 cloudscraper)'}")
    logger.info("  ✅ 智能缓存系统")
    logger.info("  ✅ 指数退避重试")
    logger.info("  ✅ User-Agent 池 (10个)")
    logger.info("  ✅ Session 持久化")
    logger.info("  ✅ 请求速率限制")
    logger.info("  ✅ 完善的日志记录")
    logger.info("  ✅ 多种 URL 格式支持")

    if not HAS_CLOUDSCRAPER:
        logger.warning("\n⚠️  建议安装 cloudscraper 以获得更好的反爬效果:")
        logger.warning("   pip install cloudscraper")

    logger.info("\n💡 提示:")
    logger.info("  1. 首次访问会自动初始化 session")
    logger.info("  2. 遇到问题会自动重试 (最多3次)")
    logger.info("  3. 查看日志了解详细运行情况\n")

    app.run(host='0.0.0.0', port=5000, debug=False)
