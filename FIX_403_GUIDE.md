# 🔧 修复 403 错误指南

你遇到了 403 错误，这里是完整的诊断和修复流程。

---

## 🚀 快速诊断

### 方法 1: 运行诊断工具（推荐）

```bash
python3 diagnose.py
```

这个工具会自动测试多种请求方式，并给出建议。

### 方法 2: 手动浏览器测试

查看 `DIAGNOSTIC_GUIDE.md`，按步骤测试并把结果告诉我。

---

## 📋 常见 403 原因和解决方案

### 1. Cloudflare 拦截（最常见）

**症状**:
- 浏览器能访问，但脚本返回 403
- 页面有 5 秒"检查浏览器"等待
- 响应头有 `CF-RAY` 或 `Server: cloudflare`

**解决方案**:

#### A. 安装 cloudscraper（推荐）
```bash
pip install cloudscraper
```

然后使用 `iyf_spider.py` 或 `iyf_spider_ultimate.py`

#### B. 使用 curl_cffi（更强）
```bash
pip install curl_cffi
```

然后使用 `iyf_spider_ultimate.py`

#### C. 使用 Playwright（终极方案）
```bash
pip install playwright
playwright install chromium
```

然后使用 `iyf_spider_ultimate.py`

---

### 2. 缺少必要的请求头

**症状**:
- 简单请求返回 403
- 加上浏览器 User-Agent 后可以访问

**解决方案**:

脚本已经包含完整的请求头模拟，确保使用最新版本。

---

### 3. 需要 Cookie

**症状**:
- 第一次访问返回 403
- 需要先访问首页获取 Cookie

**解决方案**:

脚本会自动访问首页获取 Cookie（`_init_session` 方法）

---

### 4. IP 被封禁

**症状**:
- 所有方法都返回 403
- 浏览器也无法访问或很慢

**解决方案**:

需要使用代理：

```python
# 在 config.py 中配置
USE_PROXY = True
PROXY_LIST = [
    'http://proxy_ip:port',
]
```

---

### 5. 网站完全失效

**症状**:
- 浏览器也无法访问
- DNS 解析失败
- 长时间超时

**解决方案**:

可能网站已经关闭，需要更换其他视频源。

---

## 🎯 推荐的解决流程

### 步骤 1: 运行诊断
```bash
python3 diagnose.py
```

### 步骤 2: 根据结果选择方案

#### 如果 `urllib + headers` 成功:
→ 使用基础版 `iyf_spider.py`

#### 如果 `requests` 成功:
→ 使用 `iyf_spider.py`

#### 如果 `cloudscraper` 成功:
→ 安装 cloudscraper:
```bash
pip install cloudscraper
```
→ 使用 `iyf_spider.py` 或 `iyf_spider_ultimate.py`

#### 如果全部失败:
→ 安装 Playwright:
```bash
pip install playwright
playwright install chromium
```
→ 使用 `iyf_spider_ultimate.py`

---

## 📦 安装方案对比

| 方案 | 成功率 | 速度 | 安装难度 | 推荐度 |
|------|--------|------|----------|--------|
| requests | 60% | ⚡⚡⚡ | ⭐ | ⭐⭐ |
| cloudscraper | 85% | ⚡⚡ | ⭐⭐ | ⭐⭐⭐⭐ |
| curl_cffi | 90% | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Playwright | 95% | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🔧 详细安装步骤

### 方案 A: cloudscraper（推荐）

```bash
# 1. 安装依赖
pip install cloudscraper

# 2. 运行测试
python3 test_spider.py

# 3. 如果成功，启动服务
python3 iyf_spider.py
```

### 方案 B: curl_cffi（最强，但可能安装困难）

```bash
# 1. 安装依赖
pip install curl_cffi

# 2. 运行终极版
python3 iyf_spider_ultimate.py
```

注意: curl_cffi 在某些系统上可能安装失败，如果失败请使用方案 A 或 C。

### 方案 C: Playwright（终极方案）

```bash
# 1. 安装依赖
pip install playwright

# 2. 安装浏览器
playwright install chromium

# 3. 运行终极版
python3 iyf_spider_ultimate.py
```

注意: Playwright 会下载真实的 Chrome 浏览器（约 200MB），需要一些时间。

---

## 🧪 测试各个方案

### 测试 cloudscraper:
```python
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get('https://www.iyf.tv')
print(f"状态码: {response.status_code}")
print(f"内容长度: {len(response.text)}")
```

### 测试 curl_cffi:
```python
from curl_cffi import requests

response = requests.get('https://www.iyf.tv', impersonate="chrome120")
print(f"状态码: {response.status_code}")
print(f"内容长度: {len(response.text)}")
```

### 测试 Playwright:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    response = page.goto('https://www.iyf.tv')
    print(f"状态码: {response.status}")
    print(f"内容长度: {len(page.content())}")
    browser.close()
```

---

## 💡 如果还是不行

### 1. 使用浏览器测试

按照 `DIAGNOSTIC_GUIDE.md` 的步骤，用浏览器详细测试，并把以下信息告诉我：

- ✅ 浏览器能否正常访问？
- 🔍 有没有 Cloudflare 验证页面？
- 📋 Network 标签中第一个请求的状态码？
- 🍪 有没有设置 Cookie？
- 🔒 有没有 Captcha 验证？

### 2. 提供更多信息

告诉我：
- 你的操作系统（Windows/Mac/Linux）
- Python 版本（`python3 --version`）
- 你所在的地区（网站可能有地区限制）
- 使用的网络环境（家庭/公司/服务器）

### 3. 尝试其他视频源

如果 iyf.tv 实在无法访问，可以考虑其他视频网站。

---

## 📞 需要帮助？

把诊断工具的输出和浏览器测试结果发给我，我会根据实际情况调整脚本！

```bash
# 运行诊断并保存结果
python3 diagnose.py > diagnostic_result.txt 2>&1

# 把 diagnostic_result.txt 的内容发给我
```

---

**记住**: 403 错误有多种原因，需要针对性解决。诊断是关键！🔍
