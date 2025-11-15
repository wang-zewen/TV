#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 可根据需要修改
"""

# ========== 爬虫配置 ==========

# 目标网站
BASE_URL = 'https://www.iyf.tv'

# 缓存时间（秒）
CACHE_TTL = 300  # 5分钟

# 重试配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 初始重试延迟（秒）
RETRY_BACKOFF = 2  # 退避倍数

# 请求配置
REQUEST_TIMEOUT = 20  # 请求超时（秒）
MIN_REQUEST_INTERVAL = 1.0  # 最小请求间隔（秒）

# 代理配置（可选）
USE_PROXY = False
PROXY_LIST = [
    # 'http://proxy1:port',
    # 'http://proxy2:port',
]

# ========== Flask 配置 ==========

# 服务器配置
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False  # 生产环境设为 False

# ========== 日志配置 ==========

# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# 日志文件
LOG_FILE = None  # 设置文件路径启用日志文件，如 'logs/spider.log'

# ========== 分类配置 ==========

CATEGORIES = {
    "1": "电影",
    "2": "电视剧",
    "3": "综艺",
    "4": "动漫",
    "5": "纪录片",
}
