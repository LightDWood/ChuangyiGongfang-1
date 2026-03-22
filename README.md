# 需求收敛智能体对话系统

一个基于多智能体系统的需求收敛辅助工具，帮助团队高效地收集、整理和收敛需求。

## 项目结构

```
创意工坊/
├── frontend/           # React 前端项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/        # 布局组件（三栏布局）
│   │   │   ├── conversation/  # 对话组件
│   │   │   └── artifacts/     # 产物管理组件
│   │   ├── pages/
│   │   ├── stores/           # Zustand 状态管理
│   │   ├── services/         # API 服务
│   │   ├── types/            # TypeScript 类型定义
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/           # Python/FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── models/          # 数据库模型
│   │   ├── services/        # 业务逻辑
│   │   ├── agents/          # 多智能体系统
│   │   ├── memory/          # 记忆层
│   │   └── main.py
│   ├── requirements.txt
│   └── alembic.ini
└── README.md
```

## 技术栈

### 前端
- React 18
- TypeScript
- Vite
- Zustand (状态管理)
- TailwindCSS
- Axios
- React Router

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy (异步)
- Python-Jose (JWT)
- Passlib + Bcrypt
- Aiosqlite
- Alembic

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://localhost:3000 启动。

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端服务将在 http://localhost:8000 启动。

## 功能特性

- **用户认证**: JWT 令牌认证，支持注册/登录
- **会话管理**: 创建、编辑、删除需求讨论会话
- **流式响应**: SSE 支持实时流式输出
- **产物管理**: 自动生成和管理需求文档
- **三栏布局**:
  - 左侧: 会话列表
  - 中间: 对话窗口
  - 右侧: 产物展示

## API 端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 会话
- `GET /api/sessions` - 获取会话列表
- `POST /api/sessions` - 创建会话
- `GET /api/sessions/{id}` - 获取会话详情
- `DELETE /api/sessions/{id}` - 删除会话
- `GET /api/sessions/{id}/messages` - 获取消息列表
- `POST /api/sessions/{id}/messages` - 发送消息
- `GET /api/sessions/{id}/messages/stream` - 流式消息响应

### 产物
- `GET /api/artifacts/{id}` - 获取产物详情
- `PUT /api/artifacts/{id}` - 更新产物
- `DELETE /api/artifacts/{id}` - 删除产物

## 数据库模型

- **User**: 用户信息
- **Session**: 对话会话
- **Message**: 消息记录
- **Artifact**: 产物（需求文档、规格说明等）

## 开发说明

### 前端开发

```bash
# 类型检查
npm run typecheck

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 后端开发

```bash
# 运行服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 数据库迁移
alembic upgrade head
```

## License

MIT
