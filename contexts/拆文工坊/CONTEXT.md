# 拆文工坊 — Domain Context

## Overview

拆文工坊 (Deconstruct Studio) is a training system for growth-stage writers that implements a closed-loop "AI-assisted deconstruction → imitation writing → validation" workflow, enabling the capability migration from "understanding good writing" to "producing good writing".

## Core concepts

| Term | Definition |
|------|------------|
| 拆文 | A systematic methodology for deconstructing successful articles to extract their underlying creative logic, as distinct from superficial抄写 or plagiarism |
| AI任务 | A single LLM-driven analysis operation (deep_read, deconstruct, map_skeleton, check_similarity, strip_test, prompt_self_reflection, narrative_consistency_check) |
| 节点 | A step in the 7-node user workflow (选文导入→精读→拆解→灵气筛选→骨架→仿写→校验) |
| 校验 | The process of comparing an imitation draft against the original using composite similarity (0.6×skeleton Jaccard + 0.4×emotion DTW) |
| 冷却 | A forced 24-hour pause triggered by consecutive validation failures |
| 三问 | Three pre-writing self-check questions (矛盾起因, 动机诉求, 价值落点) |
| 灵气 | A cross-genre transferable expression technique identified by the user during inspiration filtering |
| 骨架 | An abstract narrative structure stripped of specific content, represented as text + Mermaid diagram |

## Module boundaries

| Module | Responsibility |
|--------|---------------|
| AI引擎 | LLM-invoked analysis tasks, stateless per call |
| 规则引擎 | User state machine: stage transitions, cooldown, frequency control, dynamic thresholds |
| 守护服务 | 8 automated probes monitoring for abuse, pollution, and anomalies |
| 前端 | 7-node workflow UI, state visualization, user interaction at nodes 4 and 6 |
