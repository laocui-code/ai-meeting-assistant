# AI 会议助手

一个基于 AI 的会议管理系统，帮助自动生成会议纪要、提取待办事项，并与外部任务系统集成。

## 项目概述

### 核心功能

- **智能记录**：AI 自动生成结构化会议纪要（摘要、决策、讨论要点）
- **待办追踪**：自动提取和管理待办事项（负责人、截止日期、优先级）
- **智能搜索**：支持关键词搜索和语义搜索
- **无缝集成**：与 Notion、Jira、Google Calendar 等系统集成
- **对话界面**：使用自然语言查询会议信息

### 版本演进

| 版本 | 核心能力 | 对应集数 |
|------|----------|----------|
| V1 | 会议纪要生成 + 待办事项提取 | E01-E08 |
| V2 | 参与者管理 + 语义搜索 | E09-E12 |
| V3 | 外部系统集成 + 自动化 | E13-E15 |
| V4 | 对话查询 + Agent 能力 | E16-E18 |

## 技术栈

### 后端

- **语言**：Python 3.10+
- **框架**：FastAPI
- **ORM**：SQLAlchemy 2.0+
- **数据库**：
  - 开发环境：SQLite
  - 生产环境：PostgreSQL + pgvector

### AI 能力

- **大语言模型**：Claude / GPT-4 / 通义千问（可选）
- **向量数据库**：Chroma（开发）/ pgvector（生产）
- **Embedding 模型**：Sentence Transformers / OpenAI Embeddings

### 前端

- **框架**：React 18 + TypeScript
- **UI 组件**：Ant Design / shadcn/ui
- **状态管理**：Zustand
- **数据请求**：TanStack Query

### 外部集成

- Notion API
- Jira REST API
- Google Calendar API
- SendGrid / Slack Webhook

## 项目结构

```
ai-meeting-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # 应用入口
│   │   ├── api/              # API 路由
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 业务逻辑
│   │   ├── core/             # 核心配置
│   │   └── db/               # 数据库配置
│   └── requirements.txt
├── frontend/                  # 前端项目（待开发）
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
# 确认 Python 版本 >= 3.10
python --version

# 创建项目目录
mkdir ai-meeting-assistant
cd ai-meeting-assistant

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

### 4. 验证

- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs

## 开发进度

### 已完成

- [x] E01：项目概述与技术选型
- [x] E02：FastAPI 服务搭建与数据库模型设计
  - 分层设计的项目架构
  - Pydantic Settings 配置管理
  - 使用 SQLAlchemy 2.0 的 Meeting 和 ActionItem 模型
  - 异步数据库操作
  - API 路由结构及占位端点

### 进行中

- [ ] E03：会议输入与摘要生成（LLM 集成）

### 待开发

- [ ] E04：待办事项自动提取
- [ ] E05：待办事项状态管理
- [ ] E06-E08：前端开发
- [ ] E09-E12：V2 功能
- [ ] E13-E15：V3 功能
- [ ] E16-E18：V4 功能

## 许可证

MIT License
