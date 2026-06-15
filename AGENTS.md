# 网文写作工具集 — Kilo 版

## Skill 路由表

| Skill | 说明 |
|-------|------|
| `skill("story-long-write")` | 长篇网文写作（逐章推进） |
| `skill("story-short-write")` | 短篇网文写作（情绪驱动） |
| `skill("story-long-analyze")` | 长篇小说深度拆解 |
| `skill("story-short-analyze")` | 短篇小说拆文分析 |
| `skill("story-long-scan")` | 长篇市场扫榜 |
| `skill("story-short-scan")` | 短篇市场扫榜 |
| `skill("story-deslop")` | 去除 AI 写作痕迹 |
| `skill("story-cover")` | 生成封面图 |
| `skill("story-review")` | 多视角对抗式审查 |
| `skill("story-import")` | 逆向导入已有小说到项目结构 |
| `skill("story")` | 工具箱路由 · 模糊意图自动分发 |
| `skill("story-setup")` | 环境部署 · hooks/rules/agents 一键部署 |
| `skill("browser-cdp")` | 浏览器 CDP 工具 |

## 触发词速查

| 用户说 | 路由到 |
|--------|--------|
| 开书、写大纲、长篇、连载、日更、续写 | story-long-write |
| 短篇、盐言、一万字 | story-short-write |
| 拆文、分析这本书、黄金三章 | story-long-analyze |
| 拆短篇、分析这个故事 | story-short-analyze |
| 长篇排行、什么火、起点/番茄/晋江 | story-long-scan |
| 短篇排行、知乎盐言排行 | story-short-scan |
| 去 AI 味、太 AI、去味 | story-deslop |
| 封面、封面图 | story-cover |
| 准备写书、搭环境、初始化 | story-setup |
| 浏览器、抓取、登录态 | browser-cdp |
| 导入、反向解析、把我的书导进来 | story-import |
| 审查一下、帮我审一下 | story-review |

## 文件结构

- `拆文库/` — 拆文分析结果存放目录
- `{书名}/正文/` — 长篇小说正文章节
- `{书名}/设定/` — 角色设定、世界设定
- `{书名}/大纲/` — 卷纲、细纲
- `{书名}/追踪/` — 上下文.md（写作上下文）、伏笔.md
- `{书名}/对标/` — 对标作品分析

## Compact 后恢复上下文

写作中的关键上下文：
1. 当前写作项目名称和进度
2. 最近讨论的角色设定变更
3. 未完成的伏笔列表
4. 当前章节的情绪/节奏目标

如果存在 `{书名}/追踪/上下文.md`，compact 后首先读取恢复上下文。

## 语言

- 跟随用户的语言回复，用户用什么语言就用什么语言回复
- 中文回复遵循《中文文案排版指北》
