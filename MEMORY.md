# MEMORY — 新 AI 速读入口

> readers = CLI AI Agent (Claude Code Opus 4.5)
> 这不是知识库——是压缩索引。完整知识在 `knowledge/`。

## 进入项目后，按此顺序
| 优先级 | 读什么 | 为什么 |
|--------|--------|--------|
| 1 | `AGENT.md` | 规则 + 命令 + 约束 |
| 2 | `knowledge/INDEX.md` | 由此进入完整知识：ADR / gotchas / 数据源 |
| 3 | `web/js/utils.js` | 公共 deep module：jsonpFetch / openModal / classifyBuyStatus |
| 4 | `web/js/main.js` | 前端主逻辑：STATE / renderCategory |

> 架构决策 → `knowledge/adr/`（6 篇，完整背景/决策/后果）
> 已知坑点 → `knowledge/gotchas.md`（含生命周期 + 源码行号）
> 数据源   → `knowledge/data-sources.md`
> 代码结构 → `codegraph_explore`（CodeGraph MCP 工具，替代原 modules/ + CLI 图谱）

## 关键约定（约束速查，不存知识）
- `STATE.data[cat]` 是前端唯一数据源。轮询直接原地写 STATE
- Python 间 → `scripts/core/utils.py`；Python→前端 → JSON
- `web/js/config.js` = 纯常量；`utils.js` = 纯函数
- 具体技术细节 → `knowledge/gotchas.md` 和 `knowledge/adr/`；调用链 → `codegraph_explore`

## 最近关键变更（append-only）
<!-- Agent 自动追加，仅存最近 5 条 -->

- hooks 已移除 → 验证由 data_judge subagent 替代 (有降级路径)
- .codegraph/ 本地生成，不进 git
- knowledge/modules/ 已删除 → 结构信息由 codegraph_explore 提供
- plans/ 软链接到 brain 方案文档 (非本机自动降级)

## Session 待确认（append-only）
<!-- 不确定该不该加规则的，记这里下次人审 -->
