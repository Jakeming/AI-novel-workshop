# PRD: Deconstruct Studio MVP — AI Engine + 7-Node Workflow

**Status**: `ready-for-agent`
**Date**: 2026-05-28
**Labels**: `enhancement`, `ready-for-agent`

---

## Problem Statement

成长型创作者面临一个核心困境：看了一百篇好文，笔记做了一大本，自己一动笔还是不会写。"拆文"（文章解构）是被验证有效的方法论，但纯人工拆解耗时极长（单篇 3-5 小时），且新手缺乏识别"通用逻辑 vs 专属桥段"的判断力。需要一个 AI 辅助的系统，将资深创作者的拆文内隐认知外化为可执行的分析节点，通过强制的人机交互关卡确保用户完成核心能力练习，而非让 AI 代写。

## Solution

Deconstruct Studio — 一个"AI 辅助拆解 → 仿写 → 校验"闭环训练系统的 Web MVP。系统通过 7 节点工作流引导用户完成从选文到仿写校验的完整闭环，AI 负责机械化分析工作，人类保留审美判断和创作决策权。

## User Stories

### 核心工作流

1. As a 新手创作者, I want to 粘贴一篇小说全文作为拆解对象, so that 系统可以开始分析
2. As a 新手创作者, I want AI 自动生成深度精读报告（摘要、情绪曲线、钩子位置）, so that 快速建立对文章结构的全局认知
3. As a 新手创作者, I want AI 自动将文章分层拆解（立意/结构/情节/语言）, so that 理解好文的内在逻辑
4. As a 新手创作者, I want AI 自动分类"可复用通用逻辑" vs "专属桥段", so that 避开抄袭陷阱
5. As a 新手创作者, I want 对每个疑似"灵气"的段落运行跨题材测试, so that 验证一个表达手法是否真正可迁移
6. As a 新手创作者, I want 逐条确认AI标记的通用逻辑, so that 在确认过程中内化判断标准
7. As a 新手创作者, I want 系统生成纯叙事骨架（文字版 + 流程图）, so that 剥离内容后看到底层结构
8. As a 新手创作者, I want 填写三问自检（矛盾起因/动机/价值落点）后才能进入写作, so that 强制区分自己的创作与原作
9. As a 新手创作者, I want 提交仿写稿后系统自动校验相似度, so that 获得客观的原创性反馈
10. As a 新手创作者, I want 校验失败时看到具体相似片段对比, so that 知道哪里需要修改
11. As a 新手创作者, I want 连续失败后系统强制执行冷却期, so that 跳出思维定势
12. As a 新手创作者, I want 冷却期收到创意急救包, so that 获得新的灵感方向
13. As a 新手创作者, I want 校验通过后系统自动归档五份标准文件, so that 积累个人创作库

### AI 引擎

14. As a 系统开发者, I want deep_read 任务接收原文输出精读报告, so that 前端可展示情绪曲线和钩子位置
15. As a 系统开发者, I want deconstruct 任务继续深度分析输出分层拆解, so that 用户获得结构化洞察
16. As a 系统开发者, I want map_skeleton 任务输出文字骨架 + Mermaid 代码, so that 前端可渲染流程图
17. As a 系统开发者, I want check_similarity 任务计算复合相似度（骨架+情绪）并给出 verdict, so that 自动判定仿写原创性
18. As a 系统开发者, I want strip_test 任务为专属桥段生成 3 个反差领域改写, so that 辅助用户判断可迁移性
19. As a 系统开发者, I want prompt_self_reflection 在失败时生成苏格拉底式提问, so that 引导用户自我突破而非直接给答案
20. As a 系统开发者, I want narrative_consistency_check 检查仿写稿内部一致性, so that 捕获人名错误/逻辑矛盾

### 规则引擎

21. As a 系统开发者, I want user_status API 返回用户当前冷却/频次/阶段状态, so that 前端正确锁定/解锁功能
22. As a 系统开发者, I want 冷却规则由规则引擎独立管理, so that AI 引擎不耦合业务规则
23. As a 系统开发者, I want 阶段切换条件可量化配置, so that 新手→成长→成熟规则可调

### 守护服务

24. As a 系统管理员, I want Guardian-AI 监控驳回死循环、灵气污染、骨架单一性等 8 项探针, so that 系统在无人值守下安全运行
25. As a 系统管理员, I want Guardian-AI 在检测到异常时自动发出告警, so that 人工可及时介入

## Implementation Decisions

### 架构总览

四层架构：前端（React + Tailwind） → AI 引擎（Python） → 规则引擎（Python） → 守护服务（Python）

### 模块划分

| 模块 | 语言 | 职责 |
|------|------|------|
| AI 引擎 | Python 3.12+ | 7 个 LLM 驱动的分析任务，无状态，每次调用独立 |
| 规则引擎 | Python 3.12+ | 冷却计时、频次控制、三阶段状态机、动态阈值 |
| 前端 | TypeScript + React | 7 节点工作流 SPA，状态机管理，Playwright E2E 测试 |
| 守护服务 | Python 3.12+ | 8 个监控探针，批处理数据上下文模块 |

### AI 引擎架构决策

- **LLM 客户端使用深度模块模式**：一个 `llm.call(task_name, ctx) -> dict` 接口，内部封装 prompt 模板注册、重试/回退、结构化输出解析、token 跟踪（ADR 隐含：一体化 LLM 层而非每个任务各自实现 API 调用）
- **check_similarity 拆为 3 个子比较器**：骨架比较器（三元组 + Jaccard）、情绪比较器（序列 + DTW）、嵌入比较器（余弦相似度），由 ValidationAggregator 组合阈值判定
- **AI 引擎不输出冷却字段**：规则引擎独立管理冷却逻辑（ADR-0001）
- **Prompts 模板注册制**：每个任务一个 `@register_prompt` 装饰器函数，与 LLM 客户端解耦

### 规则引擎架构决策

- `Coolant.check_submit_allowed()` 作为核心 seam，所有前端操作的前置依赖
- 冷却判定基于 `consecutive_failures` 计数器，由 `record_validation()` 方法更新
- 阶段阈值集中管理在 `ThresholdTable` 中，与 AI 引擎的 `ValidationAggregator` 共享阈值定义但职责分离

### 前端架构决策

- **WorkflowController** 状态机模式：UI 组件只读不写，7 节点状态集中管理
- `canEnter(node)` 方法封装跨节点依赖和冷却期锁定逻辑
- TypeScript 实现，无外部状态管理库依赖

### 守护服务架构决策

- **ProbeContext 批处理模式**：每轮探针周期批量加载数据，新增探针无需改数据库访问
- 每个探针继承 `BaseProbe`，返回 `Alert | None`

### 数据模型（MVP 阶段）

| 实体 | 关键字段 |
|------|---------|
| users | stage, cooldown_until, consecutive_failures, daily_submit_count, last_submit_date, reputation_score |
| deconstruct_sessions | 节点时间戳、AI 输出路径、三问答案、校验历史、是否触发冷却 |
| imitation_drafts | 版本控制、每次提交全文、相似度结果 |
| skeleton_library | topology_cluster_id, contributor_reputation |
| inspiration_entries | 笔记向量（Milvus）、手法抽象描述 |

### API 契约

AI 引擎 7 个任务通过函数调用（MVP 阶段），后续拆分为独立 gRPC 服务。规则引擎暴露 `GET /api/user/status` 作为所有创作操作的前置依赖。

## Testing Decisions

### 测试原则
- 测试验证行为，不验证实现。好的测试在内部重构后仍然通过
- AI 引擎测试：mock LLM 层，验证输出 schema 和业务逻辑正确性
- 规则引擎测试：纯逻辑，不需要 mock，直接测试状态转换
- 前端测试：Playwright E2E 覆盖完整用户旅程（冷却期锁死、灵气筛选灰显等）
- 守护服务测试：用已知异常的 ProbeContext 验证探针触发逻辑

### 测试覆盖目标

| 模块 | 测试类型 | 优先级 |
|------|---------|--------|
| LLM 客户端 + prompts | 单元测试（mock OpenAI） | P0 |
| ValidationAggregator | 单元测试（纯逻辑, 用已知输入验证输出） | P0 |
| 3 个 Comparator | 单元测试 | P0 |
| Coolant | 单元测试（状态转换 + 边界条件） | P0 |
| WorkflowController | 单元测试（状态机流程） | P1 |
| Probe 探针 | 单元测试 | P1 |
| 前端 E2E | Playwright | P1 |

### 前例参考
- AI 引擎的 `comparators.py` 设计保证了每个比较器可独立实例化并测试
- 规则引擎 `Coolant` 无外部依赖，纯函数式设计可直接断言返回值

## Out of Scope

- **桌面端（Electron）**：MVP 仅提供 Web 版本
- **离线模式/本地 LLM**：MVP 阶段所有 AI 调用走云端
- **商业化/付费墙**：MVP 免费，无 Pro/教育版定价
- **社区功能/公共骨架库**：MVP 只有个人骨架库，贡献机制后续开发
- **AB 实验平台**：动态阈值优化不纳入 MVP
- **导出/迁移功能**：数据导出功能后续开发
- **骨架库多样性审计**：Guardian-AI 的骨架拓扑探针在 v2 阶段实现
- **多语言支持**：MVP 仅支持中文
- **非小说文体适配**：论点文、诗歌、产品文案等不在 MVP 范围

## Further Notes

- 项目使用 GitHub Issues 跟踪，5 个 triage labels（needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix）
- 开发采用 TDD 循环，优先构建 AI 引擎的 LLM 客户端层
- 建议开发顺序：LLM 客户端 → deep_read → deconstruct → map_skeleton → check_similarity（含 comparators）→ strip_test → prompt_self_reflection → narrative_consistency_check → 规则引擎 → 前端 7 节点 → 守护服务
