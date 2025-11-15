# iyf.tv 视频爬虫 API - 高级优化版

一个专为 iyf.tv 视频网站设计的爬虫 API 服务，支持 TVBox 等播放器调用。

## ✨ 主要特性

### 🚀 核心功能
- **Cloudflare 绕过**: 使用 cloudscraper 绕过反爬虫保护
- **智能缓存**: 内存缓存减少重复请求
- **指数退避重试**: 失败自动重试，使用指数退避策略
- **User-Agent 池**: 10+ 真实浏览器 UA 随机切换
- **Session 持久化**: 自动管理 Cookie 和会话
- **速率限制**: 防止请求过快被封禁
- **完善日志**: 详细的运行日志，方便调试

### 📺 API 功能
- ✅ 视频列表获取
- ✅ 视频详情查询
- ✅ 视频搜索
- ✅ 播放链接提取
- ✅ 多分类支持

## 📋 系统要求

- Python 3.7+
- Linux/macOS/Windows

## 🔧 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd TV
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**重要**: 确保安装 `cloudscraper` 以获得最佳性能：

```bash
pip install cloudscraper
```

## 🚀 使用方法

### 方式1: 使用启动脚本（Linux/macOS）

```bash
chmod +x run.sh
./run.sh
```

### 方式2: 直接运行

```bash
python3 iyf_spider.py
```

服务启动后会监听 `http://127.0.0.1:5000`

## 📖 API 接口文档

### 1. 首页信息

```
GET /
```

返回服务信息、功能列表和统计数据。

### 2. 获取视频列表

```
GET /api.php/provide/vod/?pg=1
```

参数:
- `pg`: 页码（默认: 1）
- `t`: 分类ID（可选）

示例:
```bash
curl "http://127.0.0.1:5000/api.php/provide/vod/?pg=1"
curl "http://127.0.0.1:5000/api.php/provide/vod/?t=1&pg=2"
```

### 3. 获取视频详情

```
GET /api.php/provide/vod/?ac=detail&ids=视频ID
```

参数:
- `ac=detail`: 操作类型
- `ids`: 视频ID（多个用逗号分隔）

示例:
```bash
curl "http://127.0.0.1:5000/api.php/provide/vod/?ac=detail&ids=123"
curl "http://127.0.0.1:5000/api.php/provide/vod/?ac=detail&ids=123,456,789"
```

### 4. 搜索视频

```
GET /api.php/provide/vod/?wd=关键词
```

参数:
- `wd`: 搜索关键词
- `pg`: 页码（可选，默认: 1）

示例:
```bash
curl "http://127.0.0.1:5000/api.php/provide/vod/?wd=爱情"
curl "http://127.0.0.1:5000/api.php/provide/vod/?wd=动作&pg=2"
```

### 5. 测试接口

```
GET /test
```

运行完整的功能测试，返回测试报告。

示例:
```bash
curl "http://127.0.0.1:5000/test"
```

### 6. 统计信息

```
GET /stats
```

返回服务运行统计信息。

## 🎯 TVBox 配置

在 TVBox 中添加数据源:

```json
{
  "sites": [
    {
      "key": "iyf",
      "name": "IYF影视",
      "type": 1,
      "api": "http://127.0.0.1:5000/api.php/provide/vod/",
      "searchable": 1,
      "quickSearch": 1,
      "filterable": 1
    }
  ]
}
```

## 🔍 分类 ID

| ID | 分类 |
|----|------|
| 1  | 电影 |
| 2  | 电视剧 |
| 3  | 综艺 |
| 4  | 动漫 |
| 5  | 纪录片 |

## 🛠️ 故障排除

### 问题1: 403 错误

**症状**: 所有请求返回 403

**解决方案**:
1. 确保安装了 `cloudscraper`:
   ```bash
   pip install cloudscraper
   ```
2. 检查网络连接
3. 尝试更换网络环境（可能IP被封）

### 问题2: 找不到视频

**症状**: 列表为空或搜索无结果

**解决方案**:
1. 检查目标网站是否可访问
2. 查看日志了解详细错误
3. 网站结构可能已变化，需要更新选择器

### 问题3: 播放链接提取失败

**症状**: 详情中没有播放链接

**解决方案**:
1. 某些视频可能需要进一步解析
2. 检查日志中的提取过程
3. 可能需要更新播放链接提取逻辑

### 问题4: 请求很慢

**症状**: 响应时间过长

**解决方案**:
1. 启用缓存（已默认启用）
2. 减少详情查询数量
3. 检查网络延迟

## 📊 性能优化建议

1. **启用缓存**: 默认缓存5分钟，可调整 `cache_ttl` 参数
2. **控制并发**: 避免同时发送大量请求
3. **使用代理**: 如果需要，可以配置代理池
4. **监控日志**: 及时发现和解决问题

## 🔒 安全建议

1. **不要公开暴露**: 仅在本地或内网使用
2. **遵守法律**: 仅用于个人学习和研究
3. **尊重网站**: 不要发送过多请求

## 📝 版本历史

### v3.0.0 (高级优化版)
- ✅ 添加 cloudscraper 支持
- ✅ 智能缓存系统
- ✅ 指数退避重试
- ✅ User-Agent 池
- ✅ 完善的日志系统
- ✅ 多种 URL 格式支持
- ✅ 改进的错误处理
- ✅ 速率限制

### v2.0.0 (增强版)
- 基本反爬措施
- 简单重试机制

### v1.0.0 (初始版)
- 基础爬虫功能

## 📄 许可证

本项目仅用于学习和研究目的，请勿用于商业用途。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本工具仅供学习交流使用，使用者需遵守相关法律法规，不得用于非法用途。
使用本工具产生的任何后果由使用者自行承担，开发者不承担任何责任。

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**Happy Coding! 🎉**
