# Tavily Web Search 智能搜索技能

## 技能信息
- **技能ID**: tavily-web-search
- **版本**: 1.0.0
- **创建日期**: 2026-03-19
- **API来源**: https://tavily.com

## 功能描述
Tavily Web Search 技能提供为AI代理优化的实时网络搜索能力。该技能使智能体能够：
1. 执行高质量的实时网络搜索
2. 自动提取和总结网页内容
3. 进行深度研究和信息综合
4. 绕过反爬机制获取数据
5. 生成结构化搜索结果

## 核心功能

### 1. 实时搜索 (/search)
- 多搜索引擎聚合（Google, Bing, DuckDuckGo）
- AI优化的结果排序
- 答案摘要生成
- 相关问题和建议

### 2. 深度研究 (/research)
- 多步骤自主研究
- 信息来源追溯
- 综合报告生成
- 引用和参考管理

### 3. 内容提取 (/extract)
- 网页内容智能提取
- Markdown格式转换
- 图片和多媒体处理
- 动态页面渲染

### 4. 网络爬取 (/crawl)
- 站点地图生成
- 批量页面抓取
- 链接关系分析
- 内容变更监控

## API 端点

### 搜索端点
```
POST https://api.tavily.com/search
```
参数：
- `query`: 搜索查询
- `search_depth`: 搜索深度 (basic/advanced)
- `include_answer`: 包含AI摘要 (true/false)
- `include_images`: 包含图片 (true/false)
- `max_results`: 最大结果数 (1-20)

### 研究端点
```
POST https://api.tavily.com/research
```
参数：
- `query`: 研究主题
- `max_iterations`: 最大迭代次数
- `time_limit`: 时间限制（秒）

### 提取端点
```
POST https://api.tavily.com/extract
```
参数：
- `urls`: 要提取的URL列表
- `extract_depth`: 提取深度
- `include_images`: 包含图片

## 使用方法

### 基础搜索
```
使用 tavily-web-search 技能搜索：
- 查询："最新人工智能发展趋势"
- 深度：advanced
- 结果数：10
- 包含AI摘要：是
```

### 深度研究
```
使用 tavily-web-search 技能进行研究：
- 主题："量子计算商业应用"
- 生成综合报告
- 包含数据来源引用
```

### 批量提取
```
使用 tavily-web-search 技能提取网页：
- URL列表：[url1, url2, url3]
- 提取正文内容
- 转换为Markdown格式
```

## 配置参数

```json
{
  "api_key": "your_tavily_api_key",
  "default_search_depth": "advanced",
  "default_max_results": 10,
  "include_answer": true,
  "include_raw_content": false,
  "include_images": false,
  "timeout": 30,
  "cache_enabled": true,
  "cache_ttl": 3600
}
```

## 依赖
- Python 3.8+
- requests (HTTP客户端)
- 可选：aiohttp (异步请求)
- 可选：redis (结果缓存)

## 响应格式

### 搜索结果
```json
{
  "query": "search query",
  "answer": "AI-generated summary",
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "content": "Extracted content",
      "score": 0.95,
      "published_date": "2024-01-15"
    }
  ],
  "related_questions": ["Q1", "Q2"],
  "images": []
}
```

### 研究报告
```json
{
  "query": "research topic",
  "report": "Comprehensive report text",
  "sources": [
    {
      "url": "https://source.com",
      "title": "Source Title",
      "relevance": 0.9
    }
  ],
  "iterations": 5,
  "time_taken": 45.2
}
```

## 使用示例

### 示例1：快速信息查询
```python
# 搜索最新科技新闻
result = tavily.search(
    query="2024年科技行业十大趋势",
    search_depth="basic",
    max_results=5,
    include_answer=True
)
print(result["answer"])
```

### 示例2：深度研究
```python
# 生成研究报告
report = tavily.research(
    query="电动汽车电池技术发展",
    max_iterations=10,
    output_format="markdown"
)
save_to_file(report["report"], "ev_battery_research.md")
```

### 示例3：批量网页提取
```python
# 提取多个网页内容
contents = tavily.extract(
    urls=[
        "https://example.com/article1",
        "https://example.com/article2"
    ],
    extract_depth="deep",
    include_images=True
)
```

## 性能指标

| 指标 | 基础搜索 | 深度搜索 | 研究模式 |
|-----|---------|---------|---------|
| 平均响应时间 | 1.5s | 3-5s | 30-60s |
| 准确率 | 85% | 92% | 95% |
| 覆盖率 | 标准 | 扩展 | 全面 |
| API调用次数 | 1 | 1 | 多步骤 |

## 错误处理

| 错误代码 | 描述 | 解决方案 |
|---------|------|---------|
| TAVILY_001 | API密钥无效 | 检查API密钥配置 |
| TAVILY_002 | 请求超时 | 增加超时设置或简化查询 |
| TAVILY_003 | 速率限制 | 实现请求节流或升级套餐 |
| TAVILY_004 | 内容提取失败 | 尝试其他URL或使用备用提取器 |
| TAVILY_005 | 配额耗尽 | 监控用量或升级计划 |

## 定价

| 套餐 | 月度请求 | 功能 |
|-----|---------|------|
| Free | 1,000 | 基础搜索 |
| Starter | 5,000 | 高级搜索+提取 |
| Professional | 20,000 | 全功能+研究 |
| Enterprise | 定制 | 定制方案 |

## 安全注意事项
- 妥善保管API密钥
- 实现请求签名验证
- 敏感查询使用HTTPS
- 遵守网站robots.txt
- 尊重数据使用条款

## 更新日志

### v1.0.0 (2026-03-19)
- 初始版本发布
- 集成Tavily Search API
- 支持/research和/extract端点
- 实现结果缓存机制

## 参考资源
- [Tavily Documentation](https://docs.tavily.com)
- [API Reference](https://docs.tavily.com/api-reference)
- [Python SDK](https://github.com/tavily-ai/tavily-python)
