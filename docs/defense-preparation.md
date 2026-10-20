# 🎓 VirtualClassroom（AI虚拟课堂）— 答辩准备文档

> 大三学生答辩参考 | 项目采用混合架构：Python AI后端 + Java业务后端 + Vue 3前端

---

## 一、项目简介（30秒介绍模板）

> "VirtualClassroom 是一个**AI驱动的在线虚拟课堂系统**。用户选择学习主题后，AI自动生成结构化教学大纲和PPT风格的板书图片；进入课堂后，AI教师以**SSE流式**逐字"讲解"课程内容，期间可进行问答互动和抢答。系统还配备了3种性格的AI学伴智能体，可与用户进行课堂讨论。技术上采用 **Python + Java 双后端微服务架构**，核心AI流程基于 **LangGraph多智能体编排**，结合向量数据库实现对话上下文检索。"

---

## 二、技术栈一览

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端** | Vue 3 (Composition API) | 3.x | 单页面应用 |
| 状态管理 | Pinia | 2.x | Vue 3 官方推荐 |
| 3D渲染 | Three.js | - | 虚拟形象渲染 |
| 图表 | ECharts | 5.x | 知识点掌握雷达图 |
| 构建工具 | Vue CLI + Webpack | 5.x | 开发服务器+代理 |
| **AI后端** | Python FastAPI | 0.104 | 异步Web框架 |
| LLM框架 | LangChain + LangGraph | 0.0.340 | 多智能体编排 |
| 向量数据库 | ChromaDB | 0.4.22 | 对话历史语义检索 |
| 大语言模型 | DeepSeek Chat API | - | AI对话生成 |
| 文生图 | 豆包 Seedream 5.0（火山方舟） | - | PPT板书图片 |
| Embedding | 阿里百炼 text-embedding-v4 | - | 文本向量化 |
| Stream | SSE (Server-Sent Events) | - | 实时流式输出 |
| **业务后端** | Java Spring Boot 3 | 3.x | RESTful API |
| ORM | MyBatis | 3.x | SQL映射 |
| 数据库 | MySQL | 8.0 | 关系型数据 |
| 认证 | JWT (jjwt) | - | Token认证 |
| **部署** | 本地开发 | - | 三个端口并行 |

---

## 三、系统架构图

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                       │
│                   localhost:8080                      │
│  ┌──────┐ ┌──────┐ ┌──────────┐ ┌───────────────┐   │
│  │ Home │ │Class │ │ Profile  │ │Leaderboard    │   │
│  │ 首页 │ │ 课堂 │ │ 我的     │ │   排行榜      │   │
│  └──────┘ └──────┘ └──────────┘ └───────────────┘   │
│         SSE流式消费  │   REST API调用                 │
└─────────┬───────────┴───────────┬───────────────────┘
          │                       │
    ┌─────▼─────────┐     ┌──────▼──────────┐
    │ Python后端    │     │  Java后端        │
    │ (FastAPI)     │     │  (Spring Boot)  │
    │ :8000         │     │  :8081          │
    │               │     │                 │
    │ AI教学 SSE流  │     │ 用户认证 JWT    │
    │ 大纲生成      │     │ 大纲CRUD        │
    │ 板书图片      │     │ 排行榜          │
    │ 学伴互动      │     │ 学习记录        │
    │ 评分/推荐     │     │ 成就系统        │
    └───┬───┬───┬───┘     └──────┬──────────┘
        │   │   │               │
   ┌────▼┐ ┌▼─┐┌▼─────────┐    │
   │Deep-│ │豆││阿里百炼   │    │
   │Seek │ │包││Embedding │    │
   │Chat │ │  ││          │    │
   └─────┘ └──┘└────┬─────┘    │
                    │          │
              ┌─────▼────┐ ┌──▼──┐
              │ ChromaDB │ │MySQL│
              │ (向量库) │ │(关系)│
              └──────────┘ └─────┘
```

---

## 四、核心技术亮点

### 4.1 LangGraph 多智能体编排

系统使用 LangGraph 实现了一个**多智能体协作框架**，包含4个专职Agent：

| Agent | 职责 | 技术实现 |
|-------|------|----------|
| **Tutor** (教师) | 模块化教学、进度跟踪 | 三节点图：input→teach→output |
| **Outline** (大纲) | 对话式生成教学大纲 | 四步流程：收集需求→生成大纲→确认→调整 |
| **Grader** (评分) | 多维度评分 | 正确性40%+完整性30%+表达20%+深度10% |
| **Recommender** (推荐) | 学习资源推荐 | 基于当前进度的个性化推荐 |
| **Board** (板书) | 知识板书生成 | 1封面+2知识点+1总结，4张PPT结构 |

**Orchestrator 协调器**：单例模式管理所有Agent，支持：
- 智能体注册与路由
- 上下文交接（前一个Agent的结果传递给下一个）
- 流水线模式（Pipeline：多Agent顺序执行）

### 4.2 SSE 流式教学

系统的核心用户体验是"AI教师实时讲课"：

```
用户点击"开始上课" → POST /ai/tutor/teach
     ↓
创建SSE连接 (stream/{session_id})
     ↓
LangChain astream() 逐Token生成
     ↓
event: token → {"token": "同学们好..." }    ← 前端逐字显示
event: board_switch → { board数据 }          ← 切换板书
event: boards_ready → { 含图片URL的板书 }   ← 板书图片生成完毕
event: done → 教学完成
```

**关键技术点**：
- SSE比WebSocket更适合此场景：单向推流、浏览器原生支持(`EventSource`)
- 打字机效果：前端缓冲区 + setInterval逐字渲染
- TTS同步：板书内容通过浏览器 `speechSynthesis` 同步朗读
- 板书切换：基于时间间隔的自动切换算法

### 4.3 向量数据库 (ChromaDB) 上下文增强

```
用户提问 → 文本向量化(阿里百炼 embedding-v4)
         → ChromaDB 语义检索历史对话
         → Top-K 相关历史注入 System Prompt
         → DeepSeek 生成更有上下文的回答
```

### 4.4 AI学伴多智能体系统

三种性格的AI学伴，各有不同的 System Prompt 和行为概率：

| 学伴 | 性格 | 评论概率 | 打招呼 | 行为特征 |
|------|------|----------|--------|----------|
| 🎓 小明 | 学霸型 | 50% | ✅ | 高正确率，偶尔炫耀 |
| 😎 小乐 | 显眼包 | 80% | ✅ | 活泼互动，气氛担当 |
| 🤫 小静 | 内向型 | 20% | ❌ | 安静含蓄，发言有深度 |

- 学伴在课堂开始时会主动和AI教师打招呼
- 讲课时每30-60秒随机触发一次评论
- 支持"发起讨论"功能：用户提话题，学伴们依次发言，限时3分钟

### 4.5 板书图片生成

```
课程文本 → Board Agent 分析 → 生成4张板书结构
    ↓ (每张板书包含：title, content, key_points, image_prompt)
豆包 Seedream 5.0 生成 → 1920×1920 PNG
    ↓
保存到 static/boards/ → 前端实时展示
```

---

## 五、前端架构

### 5.1 页面结构（Vue Router）

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | Home | 首页：创建/选择大纲入口 |
| `/classroom` | Classroom | 核心课堂：AI教学、板书、学伴 |
| `/profile` | Profile | 个人中心：设置、大纲管理 |
| `/leaderboard` | Leaderboard | 排行榜 |
| `/login` | Login | 登录注册 |

### 5.2 状态管理（Pinia）

- **useUserStore**：用户信息、XP经验值、设置（教师风格/学伴选择）
- **useClassStore**：当前大纲、模块进度、聊天消息、知识掌握度

### 5.3 API代理策略

Vue devServer 通过路径前缀路由到不同后端：

```
/api/v1/auth         → Java :8081   (认证)
/api/v1/users        → Java :8081   (用户)
/api/v1/leaderboard  → Java :8081   (排行榜)
/api/v1/outline/生成  → Python :8000  (AI生成)
/api/v1/outline/CRUD  → Java :8081   (业务CRUD)
/api/v1/ai           → Python :8000  (AI交互)
/static              → Python :8000  (静态文件)
```

**SSE代理特殊处理**：检测 `text/event-stream` 响应头，禁用缓冲确保实时推送。

---

## 六、数据库设计

### MySQL 核心表

| 表名 | 主要字段 | 说明 |
|------|----------|------|
| `users` | id, username, xp, level, streak, total_learning_hours | 用户信息+游戏化数据 |
| `outlines` | id, user_id, topic, title, level, modules_data(JSON) | 教学大纲 |
| `module_contents` | outline_id, module_index, content, board_data(JSON) | 模块教学内容+板书 |
| `teaching_sessions` | session_id, outline_id, current_module, status | 教学会话进度 |

### ChromaDB 向量集合

| 集合名 | 存储内容 | 向量维度 |
|--------|----------|----------|
| `classroom_qa` | 对话历史(问题+回答) | 1024 (embedding-v4) |

---

## 七、答辩常见问题及回答

### Q1：为什么选择双后端（Python + Java）架构？

**回答**：这是**关注点分离**的体现。
- **Python后端**负责AI核心能力——LangGraph多智能体、LLM调用、SSE流式输出，这些是Python生态的强项
- **Java后端**负责传统CRUD业务——用户认证、数据管理、排行榜，利用Spring Boot的成熟生态和MyBatis对MySQL的良好支持
- 两者通过前端Vue的devServer代理实现路由分发，对用户完全透明

### Q2：LangGraph 是什么？和 LangChain 有什么关系？

**回答**：
- **LangChain** 是LLM应用开发框架，提供了Prompt管理、模型调用、链式调用的基础能力
- **LangGraph** 是LangChain生态中的状态图编排框架，用于构建**有状态的、多步骤的**智能体工作流

本项目用LangGraph实现了：
1. 多智能体的**状态共享**（`MultiAgentState`）
2. **条件路由**——根据用户意图自动选择Agent
3. **图结构编排**——Tutor Agent内部是 input→teach→output 三节点图
4. **流水线模式**——多个Agent按序协作完成复杂任务

### Q3：SSE 和 WebSocket 的区别？为什么选择 SSE？

**回答**：
- **SSE (Server-Sent Events)**：单向推送，服务器→客户端，基于HTTP协议，浏览器原生 `EventSource` API
- **WebSocket**：双向通信，需要升级HTTP协议，适合实时互动

本项目选SSE原因：
1. AI教学是**单向内容推送**——教师讲课、板书切换都是服务端→客户端
2. 用户输入走普通POST请求，不需要双向通道
3. SSE部署更简单，无需额外WS服务器，兼容性好
4. 自动重连机制——`EventSource` 断线后自动重连

### Q4：ChromaDB 向量数据库在你的项目中起什么作用？

**回答**：主要用于**教学上下文的语义检索**。

当用户向AI教师提问时：
1. 将问题通过阿里百炼 `text-embedding-v4` 转为1024维向量
2. 在 ChromaDB 中搜索语义相近的历史对话
3. 将Top-K相关对话注入到LLM的System Prompt中

这样AI教师能"记住"之前的教学内容，回答更有连贯性，而无需在每次请求时传全部历史（节省Token）。

### Q5：如何处理 LLM 生成速度慢的问题？

**回答**：采用了**流式输出 + 前端缓冲**策略：
1. **服务端**：`LangChain astream()` 异步流式生成，产生 token 即通过 SSE 推送
2. **前端缓冲区**：收到 token 先存入 `tokenBuffer`，由 `setInterval` 定时消费
3. **打字机效果**：逐字渲染到屏幕，用户能立即看到内容开始出现
4. **TTS预读**：缓冲到一定量后启动语音朗读

这种设计让用户感受到"即时响应"——第一个token通常在1-2秒内出现。

### Q6：AI板书图片是怎么生成的？

**回答**：
1. **Board Agent**：分析课程文本，生成4张板书的文字结构（标题、要点、配图描述）
2. **图片描述精炼**：每张板书自动生成一个中文 `image_prompt`
3. **文生图**：调用豆包 Seedream 5.0 API，将提示词转为 1920×1920 PPT风格板书图
4. **本地缓存**：图片保存到 `static/boards/`，避免重复生成
5. **SSE同步**：每张图片生成完毕后通过SSE推送给前端，前端实时切换展示

### Q7：JWT 认证流程是怎样的？

**回答**：
1. 用户登录 → Java后端验证用户名密码 → 生成JWT Token返回
2. 前端将Token存入 `localStorage`，后续请求自动带在 `Authorization: Bearer xxx` 头
3. Java后端的 `AuthInterceptor` 拦截器验证Token有效性
4. Token过期 → 前端 `ApiClient` 检测401 → 跳转到登录页

### Q8：游戏化系统（XP/等级）是怎么实现的？

**回答**：
- **前端**：Pinia Store 管理 XP 状态，答题 +10~20XP，正确回答触发升级检查
- **后端Java**：`POST /users/add-xp` 持久化经验值变化，处理升级逻辑（升级阈值 = 上一级 × 1.2）
- **上课时长收益**：前端每60秒自动调用一次 `addXP(10)`，暂停不计时
- **升级公式**：100 → 120 → 144 → 172 → 206...（合理递增，新手友好）

### Q9：多AI学伴是怎么协调的？不会冲突吗？

**回答**：
- **串行调用**：多个学伴的发言是串行调用的（`for...of` 循环），每人依次生成回复
- **概率触发**：评论区是随机触发的（30-60秒一次），不是所有学伴同时发言
- **独立上下文**：每个学伴有独立的 System Prompt（定义性格），根据类型有不同回复风格
- **讨论模式**：用户发起讨论后，学伴按序发言，每人能看到历史发言内容

### Q10：前端如何处理SSE断线重连？

**回答**：
- 浏览器 `EventSource` 原生支持自动重连
- 服务端 `sse-starlette` 库管理连接生命周期
- 前端 `onUnmounted` 时主动 `close()` 清理连接
- SSE心跳：服务端每30秒发送心跳事件保活
- `vue.config.js` 中SSE代理禁用缓冲（`X-Accel-Buffering: no`），防止Nginx等中间层缓冲导致超时

### Q11：项目中有哪些设计模式？

**回答**：

| 模式 | 应用场景 | 说明 |
|------|----------|------|
| **单例模式** | Orchestrator 协调器 | 全局唯一的智能体管理中心 |
| **观察者模式** | SSE事件推送 | 服务端推送事件，前端监听消费 |
| **策略模式** | 多Agent路由 | 根据意图选择不同Agent处理 |
| **模板方法** | Agent基类 `setup()` | 定义Agent统一初始化流程 |
| **代理模式** | Vue devServer 路由代理 | 前端统一入口，后端多服务透明 |
| **工厂模式** | Agent注册 `register_agent()` | 统一创建和管理Agent实例 |

### Q12：项目最大的技术挑战是什么？

**回答**：**SSE流式教学的全链路协调**——需要同步管理：
1. LLM逐token生成（异步生成器）
2. 打字机效果逐字渲染（前端setInterval）
3. TTS语音同步朗读（浏览器SpeechSynthesis）
4. 板书定时自动切换（时间间隔算法）
5. 板书图片异步生成（豆包API调用+缓存）

这五者需要精确的时间协调和状态管理，任何一个环节的延迟或异常都需要优雅降级而非崩溃。通过分层解耦（SSE层→缓冲区层→渲染层→TTS层）和充分的异常捕获实现了稳定运行。

---

## 八、答辩演示建议

### 演示流程（5-8分钟）

1. **登录/注册** → 展示用户系统
2. **创建大纲** → 展示AI对话式大纲生成
3. **进入课堂** → 展示AI教师流式讲课 + 板书自动切换 + TTS朗读
4. **学伴互动** → 展示学伴打招呼、评论区发言
5. **发起讨论** → 展示多学伴讨论功能
6. **答题互动** → 展示选择题/填空题，XP增加
7. **切换"我的"** → 展示大纲管理、设置（教师风格、学伴选择）

### 技术亮点展示

- 打开浏览器DevTools → Network标签 → 查看SSE的 `text/event-stream` 类型请求，展示 `token`、`board_switch` 事件
- 打开Pinia DevTools → 展示状态变化
- 展示 `static/boards/` 目录中的AI生成板书图片

---

## 九、环境配置速查

| 配置项 | 文件 | 说明 |
|--------|------|------|
| DEEPSEEK_API_KEY | backend/.env | DeepSeek对话模型 |
| ARK_API_KEY | backend/.env | 豆包Seedream文生图 |
| DASHSCOPE_API_KEY | backend/.env | 阿里百炼Embedding |
| MySQL连接 | backend/.env + java application.properties | 数据库 |

### 启动命令

```bash
# 终端1：Python AI后端
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：Java业务后端
cd java-backend/java-backend && mvn spring-boot:run

# 终端3：Vue前端
cd frontend && npm run serve
```
