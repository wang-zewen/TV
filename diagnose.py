#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的诊断工具 - 测试网站访问情况
不需要安装太多依赖
"""

import urllib.request
import urllib.error
import json
import time

TARGET_URL = "https://www.iyf.tv"

def test_basic_request():
    """测试 1: 最简单的请求"""
    print("\n" + "="*60)
    print("测试 1: 基础请求（urllib）")
    print("="*60)

    try:
        req = urllib.request.Request(TARGET_URL)
        response = urllib.request.urlopen(req, timeout=10)

        print(f"✅ 状态码: {response.status}")
        print(f"   URL: {response.url}")
        print(f"   内容长度: {len(response.read())} bytes")

        # 打印响应头
        print("\n📋 响应头:")
        for header, value in response.headers.items():
            print(f"   {header}: {value}")

        return True

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误: {e.code} - {e.reason}")
        print(f"   响应头:")
        for header, value in e.headers.items():
            print(f"   {header}: {value}")
        return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_with_headers():
    """测试 2: 模拟浏览器请求"""
    print("\n" + "="*60)
    print("测试 2: 模拟浏览器（urllib + headers）")
    print("="*60)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        req = urllib.request.Request(TARGET_URL, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)

        print(f"✅ 状态码: {response.status}")
        print(f"   URL: {response.url}")

        content = response.read()
        print(f"   内容长度: {len(content)} bytes")

        # 检查是否是 HTML
        if b'<html' in content[:1000].lower() or b'<!doctype' in content[:1000].lower():
            print(f"   ✅ 返回的是 HTML 内容")
        else:
            print(f"   ⚠️  返回的不是 HTML 内容")

        # 检查 Cloudflare
        if b'cloudflare' in content.lower():
            print(f"   ⚠️  检测到 Cloudflare")
        if b'checking your browser' in content.lower():
            print(f"   ⚠️  检测到浏览器验证页面")

        print("\n📋 响应头:")
        for header, value in response.headers.items():
            print(f"   {header}: {value}")

            # 检查关键头部
            if header.lower() == 'cf-ray':
                print(f"   🔍 检测到 Cloudflare (CF-RAY)")
            if header.lower() == 'server' and 'cloudflare' in value.lower():
                print(f"   🔍 服务器使用 Cloudflare")

        return True

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误: {e.code} - {e.reason}")

        if e.code == 403:
            print("\n💡 403 错误分析:")
            print("   可能原因:")
            print("   1. Cloudflare 拦截")
            print("   2. WAF (防火墙) 拦截")
            print("   3. 缺少必要的 Cookie")
            print("   4. IP 被封禁")
            print("   5. 需要 JavaScript 挑战")

        print(f"\n📋 响应头:")
        for header, value in e.headers.items():
            print(f"   {header}: {value}")

        return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_with_requests():
    """测试 3: 使用 requests 库（如果可用）"""
    print("\n" + "="*60)
    print("测试 3: requests 库测试")
    print("="*60)

    try:
        import requests

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        session = requests.Session()
        response = session.get(TARGET_URL, headers=headers, timeout=10, allow_redirects=True)

        print(f"状态码: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"内容长度: {len(response.text)} bytes")

        if response.status_code == 200:
            print("✅ requests 成功访问")
        elif response.status_code == 403:
            print("❌ requests 返回 403")
        else:
            print(f"⚠️  状态码: {response.status_code}")

        print(f"\n📋 响应头:")
        for header, value in response.headers.items():
            print(f"   {header}: {value}")

        # Cookies
        if session.cookies:
            print(f"\n🍪 Cookies:")
            for cookie in session.cookies:
                print(f"   {cookie.name}: {cookie.value[:50]}...")

        return response.status_code == 200

    except ImportError:
        print("⚠️  requests 未安装，跳过")
        return None

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_with_cloudscraper():
    """测试 4: 使用 cloudscraper（如果可用）"""
    print("\n" + "="*60)
    print("测试 4: cloudscraper 测试 (Cloudflare 绕过)")
    print("="*60)

    try:
        import cloudscraper

        scraper = cloudscraper.create_scraper()
        response = scraper.get(TARGET_URL, timeout=15)

        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)} bytes")

        if response.status_code == 200:
            print("✅ cloudscraper 成功访问")
        elif response.status_code == 403:
            print("❌ cloudscraper 也返回 403 (可能需要更强的方案)")
        else:
            print(f"⚠️  状态码: {response.status_code}")

        return response.status_code == 200

    except ImportError:
        print("⚠️  cloudscraper 未安装")
        print("   安装命令: pip install cloudscraper")
        return None

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主函数"""
    print("🔍 iyf.tv 网站诊断工具")
    print(f"目标: {TARGET_URL}")
    print("\n开始测试...\n")

    results = {}

    # 测试 1
    results['basic'] = test_basic_request()
    time.sleep(1)

    # 测试 2
    results['with_headers'] = test_with_headers()
    time.sleep(1)

    # 测试 3
    results['requests'] = test_with_requests()
    if results['requests'] is not None:
        time.sleep(1)

    # 测试 4
    results['cloudscraper'] = test_with_cloudscraper()

    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    for test_name, result in results.items():
        if result is True:
            status = "✅ 成功"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⏭️  跳过"

        print(f"{test_name:20s}: {status}")

    # 建议
    print("\n💡 建议:")

    if results['with_headers']:
        print("   ✅ urllib + headers 可以访问")
        print("   → 使用普通 requests 就可以")

    elif results['requests']:
        print("   ✅ requests 可以访问")
        print("   → 使用 requests 库")

    elif results['cloudscraper']:
        print("   ✅ cloudscraper 可以访问")
        print("   → 网站使用了 Cloudflare，需要 cloudscraper")

    else:
        print("   ❌ 所有方法都失败")
        print("   可能原因:")
        print("   1. 网站需要真实浏览器 (考虑 Playwright/Selenium)")
        print("   2. IP 被封禁 (需要代理)")
        print("   3. 需要特殊的 Cookie 或 Token")
        print("   4. 网站已失效")
        print("\n   建议:")
        print("   1. 用浏览器访问看看能否打开")
        print("   2. 查看 DIAGNOSTIC_GUIDE.md 进行详细诊断")
        print("   3. 考虑使用 Playwright 方案")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
