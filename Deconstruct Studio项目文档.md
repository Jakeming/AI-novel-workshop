# Deconstruct Studio 终极项目交付方案
**版本**：v3.0（防弹版）  
**项目经理**：AI-PM Agent  
**执行主体**：AI 编程代理 + 全自动 CI/CD 流水线  
**设计原则**：  

+ **Apple 式**：极限体验、阶段门禁、隐私优先、Radar 缺陷雷达  
+ **Google 式**：OKR 透明、数据驱动、Design Doc 评审、20% 容错  
+ **腾讯式**：小步快跑、灰度放量、AB 实验验证、内部赛马  
+ **阿里式**：战役攻坚、借事修人、全局复盘、中台复用

**核心理念**：将文学创作辅助训练，转译为 **零人工干预、全自动纠偏、抗对抗攻击** 的确定性系统。

---

## 一、项目章程与核心目标
**使命**：60 天内交付 Deconstruct Studio Web 端 MVP，实现“AI 辅助拆解-仿写-校验”闭环，并通过自动化验证确保系统在无人值守下可安全、公平地运行。

**关键成果（OKR）**：

+ **O1**：交付核心闭环，真实用户 7 步完成率 > 70%
    - KR1：20 名种子用户中，至少 14 人成功获得一次“绿灯”归档
+ **O2**：建立无人干预的自动品控体系
    - KR2：相似度误判申诉率 < 5%，恶意攻击拦截率 100%
+ **O3**：构建可演进的创作数据飞轮
    - KR3：公共骨架库冷启动 50 篇，多样性指数达标，周均有效检索 > 500 次

---

## 二、总架构与 AI 执行铁律
本项目所有任务均分解为 **可被脚本 / AI Agent 执行的原子单元**，每个单元包含：输入、输出、验收脚本、回滚条件。人类仅保留两类权利：**例外决策** 与 **战略方向调整**。

**执行铁律**：

1. 所有判定必须量化，禁止“文学价值”“感觉不对”等模糊描述。
2. 任何自动化规则都必须附带 **自纠偏机制**（如动态阈值、降级策略）。
3. 任何用户行为都假设可能为恶意，默认集成 **防滥用探针**。
4. 代码合并、测试、部署、灰度放量全部自动化，由 CI/CD 驱动。

---

## 三、战役式开发计划（阿里风格）
### 战役一：核心闭环验证（第 1–6 周）
**目标**：跑通 Web 端新手期 7 节点，AI 引擎可调度，规则引擎上线，安全基线建立。

**核心交付物**：

1. **AI 微服务集群**  
    - 实现 6 个核心任务（deep_read, deconstruct, map_skeleton, check_similarity, strip_test, prompt_self_reflection）+ 1 个新增一致性检查（narrative_consistency_check）  
    - 严格遵循 v2.0 修补后的输入输出与内部校验规则  
    - 自动部署至 Cloud Run，通过 gRPC 供后端调用  
    - 验收：10 篇内置范文批量调用，输出结构与规格 100% 一致，相似度误差 ≤5%
2. **前端核心页面**  
    - React + Tailwind 单页应用，仅实现新手期状态机  
    - 所有页面交互用 Playwright 自动化测试覆盖（包括冷却期锁死、灵气筛选修辞灰显等）  
    - 验收：端到端测试套件通过率 100%
3. **规则引擎与 user_status API**  
    - 集中管理冷却、频次、动态阈值放宽、阶段切换  
    - 提供 `GET /api/user/status` 作为所有创作操作的前置依赖  
    - 验收：契约测试（Pact）覆盖全部状态组合
4. **guardian-ai 守护服务 v1**  
    - 驳回死循环监控、灵气库污染告警、骨架库多样性审计  
    - 防刷机制：文本相似度对比（识别反复提交）、速率限制、成本熔断  
    - 验收：模拟恶意脚本攻击，所有探针正确触发

**Apple 阶段门禁**：

+ Alpha (W2)：AI 引擎本地可调，前端可展示节点 2 情绪曲线
+ Beta (W4)：自动化测试用户 100% 走完闭环，后端 0 5xx 错误
+ PVT (W6)：种子用户灰度，绿灯通过率 >70%，节点 4 完成率 >60%，若不达标自动回滚

---

### 战役二：体验打磨与数据飞轮（第 7–12 周）
**目标**：成长期上线，动态阈值精准化，公共库冷启动，离线模式安全降级可用。

**核心交付物**：

+ AB 实验平台集成（Firebase Remote Config），分流动态阈值组，自动收集误判率与冷却触发率
+ 公共骨架库冷启动：AI 批量拆解 50 篇跨领域、跨文化、多拓扑结构范文，经自动化多样性审计后入库
+ 离线模式降级策略：当本地模型连续失败 3 次，切换至静态规则替换引擎
+ `narrative_consistency_check` 分层报告：critical（硬伤，黄色警告）与 advisory（风格选择，折叠）

**阶段门禁**：AB 实验核心指标劣化 >5% 自动关闭；连续 7 天无用户晋升成长，自动触发诊断流水线。

---

### 战役三：生态与商业化（第 13 周起）
**目标**：桌面端 Electron 打包、社区功能、付费墙，全灰度发布。

**交付与安全**：

+ 所有功能按 1% → 5% → 20% → 全量灰度，监控崩溃率、API 延迟、付费转化
+ 公共库贡献者信誉系统上线（PageRank 式加权，新用户骨架隔离区）
+ 法律文本落地：骨架库版权声明、用户协议防洗稿条款

---

## 四、AI 引擎最终规格（合并全部修补与防御）
### 4.1 任务清单与输入/输出摘要
| 任务名 | 输入关键字段 | 输出核心字段 |
| --- | --- | --- |
| deep_read | original_text | summary, emotion_curve, hooks, paragraph_functions |
| deconstruct | original_text | intent, structure, plot, language, portable_logic, specific_elements |
| map_skeleton | original_text, user_answers | text_skeleton, mermaid_code |
| check_similarity | original_text, imitation_text, user_answers, previous_motivation_failures, allow_threshold_relaxation | conflict_similarity, motivation_similarity, value_similarity, verdict, similar_segments, cooldown_required |
| strip_test | specific_element | original, test_cases (含 rhetoric_lost 标记) |
| prompt_self_reflection | （通常由 check_similarity 红/黄灯触发） | questions (3 个苏格拉底式提问) |
| narrative_consistency_check | imitation_text | inconsistencies (分 critical / advisory) |


### 4.2 关键修补逻辑硬编码
**相似度判定（防死循环）**：

+ 复合相似度 = 0.6 × 骨架三元组 Jaccard + 0.4 × 情绪序列 DTW 距离
+ **硬规则**：若 `骨架匹配率 < 0.3`，忽略三问答案的黄灯警告，verdict 仅由骨架+情绪决定
+ **动态阈值放宽触发**：`previous_motivation_failures ≥ 3` 且 `allow_threshold_relaxation = true`，则将对应维度阈值临时上调 10%（如 60%→70%），24 小时后自动恢复
+ **防刷检测前置**：若该用户过去 1 小时内提交的仿写稿间文本相似度 > 80%，`previous_motivation_failures` 不累加，不触发放宽

**灵气筛选防污染**：

+ strip_test 生成改写后，内部执行修辞结构对比（比喻、排比等），若丢失则标记 `rhetoric_lost: true`，前端灰显且不可收录
+ 用户收录灵气时，必填“打动我的本质”，系统将其与 AI 预生成的“手法抽象描述”做 embedding 相似度，< 0.5 则拒绝保存

**离线模式容错**：

+ 本地模型输出必须通过 Mermaid 语法解析和长度偏离检查（改写长度在原文 ±30% 以内）
+ 连续 3 次丢弃后，自动切换为静态关键词替换引擎（如人名→Bot，皇宫→数据中心），并明示“离线简化版”

**冷却与状态锁死**：

+ `user_status` API 返回全局锁：`can_submit_new_imitation` 在冷却期内为 false，前端所有新建仿写入口置灰
+ 修改旧稿时，若新旧内容文本相似度 < 30%，视为新建，同样受冷却限制

**全文一致性提示**：

+ 仅 `critical` 级别不一致（如人名错误）显示为黄色警告条，`advisory` 折叠至“详细报告”

---

## 五、数据模型（核心表，修补字段）
**users**

```sql
stage VARCHAR(20) DEFAULT 'novice',
cooldown_until TIMESTAMP,
motivation_fail_count_2h INT,
last_motivation_fail_time TIMESTAMP,
daily_submit_count INT,
last_submit_date DATE,
reputation_score FLOAT DEFAULT 0.0
```

**deconstruct_sessions**：关联原文、节点时间戳、AI 输出路径、三问答案、校验历史、是否触发冷却

**imitation_drafts**：版本控制，记录每次提交的全文及相似度结果，用于防刷对比

**skeleton_library**：公共库骨架，增加字段 `topology_cluster_id`（拓扑聚类标签）、`contributor_reputation`（贡献时信誉分）

**inspiration_entries**：灵气库，存储用户笔记、AI 手法抽象描述、收录时相似度验证分值

---

## 六、Guardian-AI 全自动监控矩阵
| 监控探针 | 检测逻辑 | 触发动作 |
| --- | --- | --- |
| 驳回死循环探针 | 同一用户 2h 内提交-驳回≥3 次且无通过 | 自动临时放宽阈值 10%，记录告警 |
| 灵气库污染探针 | 灵气库中笔记-手法描述相似度 <0.5 的比例 >30% | 推送“灵气库健康检查”通知，建议回顾 |
| 骨架拓扑单一探针 | 公共库内骨架图编辑距离聚类 <4 种拓扑 | 自动生成“需补充拓扑类型”任务 |
| 恶意刷失败探针 | 1h 内连续失败且稿间相似度 >80% | 冻结该用户放宽资格，不计入失败累积 |
| 速率/成本熔断探针 | 单用户 10min 内相似度请求 >10 次且全红/黄 | 冻结 API 调用 1h，弹出 CAPTCHA |
| 洗稿检测探针 | 仿写稿与已知网络内容子串匹配 >70% | 标记为高风险，不通过校验，人工抽检 |
| 离线模式降级探针 | strip_test 或 map_skeleton 连续丢弃 ≥3 次 | 自动切换至静态引擎，前端提示 |
| 公共库污染探针 | 新入库骨架含品牌/产品名 | 拒绝入库，信誉分扣除 |


所有探针 24×7 运行，异常自动记录到 BigQuery，由 Looker Studio 生成实时仪表盘。

---

## 七、隐私、合规与对抗防御
**隐私**：  

+ 所有用户文本默认本地存储（IndexedDB），云端同步须显式开启且端到端加密  
+ AI 分析在内存中进行，处理完毕即丢弃原文，训练豁免写入服务条款

**版权与防抄袭**：  

+ 公共骨架库匿名贡献，系统自动脱敏、去广告  
+ 使用条款严禁将骨架库和急救包内容用于商业出版，技术层面通过访问频次限制、数字水印（离线输出）和爬虫检测强制执行  
+ 洗稿检测探针在线运作，高置信度命中时自动驳回并留存证据

**对抗性防御总结**：  

+ 慢毒注入 → 信誉隔离 + 多样性审计  
+ 三元组淹没 / 情绪仿制 → 困惑度前置 + 对抗训练  
+ 资源耗尽 → 速率限制 + 成本熔断  
+ 模型逆向 / 舆论攻击 → 本地仅部署通用量化模型 + 输出水印  
+ 急救包/公共库爬取 → API 深度限流 + 法律条款

## 八、部署与发布策略
**CI/CD 管道**：  

+ 代码提交 → 单元/集成/契约测试 → 安全扫描（含对抗样本测试） → 自动部署到开发环境  
+ 合并到 main → 自动部署到预发布 → 灰度 1% → 监控探针全部正常 → 逐步扩大灰度  
+ 任何门禁指标未达标，自动停止发布并回滚

**MVP 发布**：  

+ Web 端，支持新手期完整闭环，冷却/频次/动态阈值全功能  
+ 内置 50 篇种子骨架，多样性审计通过  
+ guardian-ai v1 上线 5 项核心探针

**后续版本**：  

+ 桌面端采用 Electron，集成离线简化模型，数字水印  
+ 成长/成熟期逐步解锁，社区功能凭信誉分灰度开放

## 九、项目交付物清单（AI 代理执行用）
1. `ai-engine/`：FastAPI 服务代码，包含全部任务端点与内部校验逻辑
2. `rule-engine/`：NestJS 服务，user_status API，冷却/频次/阈值放宽状态机
3. `guardian-ai/`：监控探针脚本，自动化告警与修复触发
4. `frontend/`：React Web 应用，含完整 Playwright 端到端测试
5. `data-pipeline/`：种子骨架生成脚本，多样性审计脚本，BigQuery 表建表语句
6. `contracts/`：API 契约文件（OpenAPI/Pact），用于自动化契约测试
7. `security/`：对抗样本测试集，速率限制配置，CAPTCHA 集成文档
8. `legal/`：服务条款、隐私协议、版权声明模板

