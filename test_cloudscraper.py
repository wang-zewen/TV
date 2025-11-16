#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 cloudscraper 是否能绕过 Cloudflare
"""

import cloudscraper

TARGET_URL = "https://www.iyf.tv"

print("=" * 60)
print("测试 cloudscraper 绕过 Cloudflare")
print("=" * 60)

try:
    print(f"\n正在访问: {TARGET_URL}")
    print("请稍候...\n")

    # 创建 scraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=10,  # 延迟，让 Cloudflare 有时间处理
    )

    # 发送请求
    response = scraper.get(TARGET_URL, timeout=30)

    print(f"✅ 状态码: {response.status_code}")
    print(f"   URL: {response.url}")
    print(f"   内容长度: {len(response.text)} bytes")

    # 检查响应内容
    if response.status_code == 200:
        print("\n🎉 成功绕过 Cloudflare！")

        # 检查是否是正常的 HTML
        content_lower = response.text.lower()

        if '<html' in content_lower or '<!doctype' in content_lower:
            print("   ✅ 返回的是正常 HTML 页面")

            # 检查是否包含视频相关内容
            if 'video' in content_lower or '视频' in response.text or '电影' in response.text:
                print("   ✅ 页面包含视频相关内容")

            # 显示部分内容
            print("\n📄 页面标题:")
            import re
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
            if title_match:
                print(f"   {title_match.group(1)}")

        else:
            print("   ⚠️  返回的不是 HTML 页面")

    elif response.status_code == 403:
        print("\n❌ 仍然返回 403")
        print("   cloudscraper 也无法绕过，需要使用 Playwright（真实浏览器）")

    else:
        print(f"\n⚠️  返回状态码: {response.status_code}")

    # 显示响应头
    print("\n📋 响应头（部分）:")
    important_headers = ['Server', 'CF-RAY', 'cf-mitigated', 'Set-Cookie']
    for header in important_headers:
        if header in response.headers:
            value = response.headers[header]
            if len(value) > 100:
                value = value[:100] + '...'
            print(f"   {header}: {value}")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
