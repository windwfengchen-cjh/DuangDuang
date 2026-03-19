# 反爬网页访问 (web-scraper)

## 概述

微信公众号/Twitter/Reddit等反爬网站，三种方法自动切换。

## 功能

- 反爬网站内容获取
- 多种爬取策略自动切换
- JavaScript渲染支持
- 验证码绕过(基础)

## 使用方法

1. 提供目标URL
2. 系统自动选择最佳策略
3. 返回清洗后的内容

## 反爬策略

1. **标准HTTP请求**: 简单网页
2. **无头浏览器**: JavaScript渲染页面
3. **代理轮换**: IP限制网站
4. **请求头伪装**: 模拟真实浏览器

## 支持的网站

- 微信公众号
- Twitter/X
- Reddit
- 知乎
- 豆瓣
- 其他反爬网站

## 输入参数

- `url`: 目标网页URL
- `method`: 爬取方法 (auto/requests/browser)
- `wait_time`: 浏览器等待时间(秒)
- `extract_content`: 是否提取正文

## 依赖

- 浏览器控制工具
- HTTP请求库
- 内容提取工具

## 版本

1.0.0

## 来源

官方技能 - sanwan.ai
