#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Playwright 是否能绕过 Cloudflare
"""

from playwright.sync_api import sync_playwright
import time
import sys

TARGET_URL = "https://www.iyf.tv"

def main():
    print("=" * 60)
    print("测试 Playwright (真实浏览器) 绕过 Cloudflare")
    print("=" * 60)

    try:
        print(f"\n正在启动浏览器...")
        print(f"目标: {TARGET_URL}")
        print("请稍候（可能需要等待 Cloudflare 验证）...\n")

        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )

            # 创建上下文
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                ignore_https_errors=True,  # 忽略 SSL 证书错误
            )

            # 创建页面
            page = context.new_page()

            # 访问页面
            print("🌐 正在访问页面...")
            response = page.goto(TARGET_URL, timeout=30000, wait_until='domcontentloaded')

            status = response.status if response else None
            print(f"   初始状态码: {status}")

            # 等待 Cloudflare 验证
            print("⏳ 等待页面加载（Cloudflare 验证）...")
            time.sleep(5)

            # 获取最终内容
            final_url = page.url
            content = page.content()

            print(f"\n✅ 最终 URL: {final_url}")
            print(f"   内容长度: {len(content)} bytes")

            # 检查是否成功
            success = False
            if len(content) > 1000:
                print("\n🎉 成功访问！")

                # 页面标题
                title = page.title()
                print(f"   📄 页面标题: {title}")

                # 检查内容
                if '视频' in content or '电影' in content or 'video' in content.lower():
                    print(f"   ✅ 页面包含视频相关内容")

                # 检测页面结构
                print("\n🔍 检测页面结构...")

                selectors = [
                    '.module-item',
                    '.stui-vodlist__box',
                    '.video-item',
                    'a[href*="voddetail"]',
                    'a[href*="detail"]',
                ]

                for selector in selectors:
                    items = page.query_selector_all(selector)
                    if items:
                        print(f"   ✅ 找到选择器 '{selector}': {len(items)} 个元素")

                        if len(items) > 0:
                            first_item = items[0]
                            href = first_item.get_attribute('href')
                            text = first_item.inner_text()[:50] if first_item.inner_text() else ''
                            print(f"      示例: {text} - {href}")

                        success = True
                        break

                if not success:
                    print(f"   ⚠️  未找到标准选择器，但页面已加载")
                    success = len(content) > 5000  # 内容足够大就算成功

            else:
                print("\n❌ 页面内容太短，可能仍被拦截")

            # 关闭浏览器
            browser.close()

            print("\n" + "=" * 60)
            print("测试完成！")
            print("=" * 60)

            if success:
                print("\n💡 结论: Playwright 可以成功访问！")
                print("   → 可以使用 Playwright 版本的爬虫脚本")
                return True
            else:
                print("\n💡 结论: 仍然被拦截")
                print("   → 需要进一步优化")
                return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
