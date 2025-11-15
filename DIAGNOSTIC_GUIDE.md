# 🔍 iyf.tv 网站诊断指南

在修复 403 错误之前，我需要了解网站的实际情况。请按以下步骤测试并把结果告诉我。

---

## 📋 测试步骤

### 1. 浏览器访问测试

请用以下浏览器分别访问 `https://www.iyf.tv`，告诉我结果：

#### Chrome/Edge 浏览器
1. 打开 Chrome/Edge
2. 访问 `https://www.iyf.tv`
3. 告诉我：
   - ✅ 能正常访问？
   - ⏳ 有没有等待/验证页面？
   - 🔒 是否需要点击"我是人类"之类的按钮？
   - 📄 看到的是正常的视频网站页面吗？

#### Firefox 浏览器
1. 打开 Firefox
2. 访问 `https://www.iyf.tv`
3. 同样告诉我上面的问题

#### 无痕/隐私模式
1. 打开浏览器的无痕/隐私模式
2. 访问 `https://www.iyf.tv`
3. 告诉我结果

---

### 2. 网络请求分析（重要！）

这一步很关键，帮助我了解网站的反爬机制。

#### 步骤：
1. 打开 Chrome/Edge 浏览器
2. 按 `F12` 打开开发者工具
3. 点击 **Network（网络）** 标签
4. 刷新页面 `https://www.iyf.tv`
5. 等待页面完全加载

#### 需要告诉我：

**A. 请求信息**
- 第一个请求（通常是 `www.iyf.tv` 或主页请求）的状态码是多少？
  - 200?
  - 403?
  - 其他?

**B. 请求头信息**
在 Network 标签中，找到第一个请求，点击它，然后：
1. 点击 **Headers（请求头）** 标签
2. 截图或复制 **Request Headers（请求头）** 部分，特别是：
   ```
   User-Agent: ...
   Cookie: ...
   Referer: ...
   Origin: ...
   ```

**C. 响应头信息**
同样在 Headers 标签中，找到 **Response Headers（响应头）**，告诉我：
   ```
   Server: ...
   CF-RAY: ...  (如果有，说明使用了 Cloudflare)
   Set-Cookie: ...
   ```

**D. JavaScript 文件**
在 Network 标签中：
1. 筛选器选择 **JS**
2. 看看有没有这些可疑的 JS 文件：
   - `challenge.js`
   - `cloudflare.js`
   - `recaptcha.js`
   - 或其他看起来像验证的 JS

---

### 3. 特殊情况检测

#### A. Cloudflare 检测
页面加载时，有没有看到：
- "Checking your browser..."
- "正在检查您的浏览器..."
- Cloudflare 的 logo
- 5 秒等待？

#### B. Captcha 验证
有没有遇到：
- reCAPTCHA (选择图片)
- hCaptcha
- 滑块验证
- 点击"我不是机器人"

#### C. 地区限制
有没有提示：
- "您的地区无法访问"
- "请使用中国IP"
- 或其他地区限制信息

---

### 4. curl 测试（可选，如果会用命令行）

如果你会用命令行，请运行：

```bash
# 测试 1: 简单请求
curl -I https://www.iyf.tv

# 测试 2: 模拟浏览器
curl -I https://www.iyf.tv \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 测试 3: 完整请求
curl -v https://www.iyf.tv \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  -H "Accept-Encoding: gzip, deflate, br"
```

告诉我返回的状态码和内容。

---

### 5. 页面结构分析

如果网站能正常访问，请：

#### A. 查看视频列表
1. 找到首页的视频列表
2. 右键点击一个视频项
3. 选择"检查"（Inspect）
4. 告诉我 HTML 结构，例如：
   ```html
   <div class="某个类名">
     <a href="/voddetail/123.html">
       <img src="...">
       <h3>视频标题</h3>
     </a>
   </div>
   ```

#### B. 视频详情页
1. 点击进入一个视频详情页
2. 告诉我 URL 格式，例如：
   - `https://www.iyf.tv/voddetail/123.html` ？
   - 还是其他格式？

---

## 📊 测试结果模板

请把测试结果按这个格式告诉我：

```
【浏览器访问测试】
- Chrome: ✅ 正常 / ❌ 403 / ⏳ 有验证
- Firefox: ✅ 正常 / ❌ 403 / ⏳ 有验证
- 无痕模式: ✅ 正常 / ❌ 403 / ⏳ 有验证

【Network 分析】
- 第一个请求状态码: 200 / 403 / 其他
- 是否有 CF-RAY 头: 有 / 没有
- 是否有 Set-Cookie: 有（内容：...） / 没有

【特殊情况】
- Cloudflare 检测: 有 / 没有
- Captcha 验证: 有（类型：...） / 没有
- 地区限制: 有 / 没有

【页面结构】
- 视频列表 HTML 类名: .module-item / .stui-vodlist / 其他
- 详情页 URL 格式: /voddetail/123.html / 其他

【其他发现】
（任何其他重要信息）
```

---

## 💡 为什么需要这些信息？

1. **状态码** → 确定是否真的是 403，还是其他问题
2. **请求头** → 了解网站需要哪些必须的头部
3. **Cloudflare** → 决定使用哪种绕过方案
4. **Captcha** → 如果有验证码，可能需要人工或第三方服务
5. **页面结构** → 确保爬虫的选择器正确

---

## 🔧 常见情况和解决方案

根据你的测试结果，我会采用不同的方案：

| 测试结果 | 解决方案 |
|---------|---------|
| 浏览器正常，脚本 403 | 增强请求头、使用 curl_cffi |
| Cloudflare 5秒检测 | 使用 cloudscraper 或 Playwright |
| Captcha 验证 | 使用 Playwright + 手动验证 |
| 地区限制 | 需要代理 |
| 完全无法访问 | 网站可能已失效，需要换源 |

---

**请测试后把结果发给我，我会根据实际情况优化脚本！** 🚀
