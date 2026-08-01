# QDII Tracker

> Agent 规则入口。架构+功能见 [README](./README.md)。解释记忆见 `knowledge/`。结构记忆见 `.codegraph/`。

## 任务路由（防幻觉：每个任务必须按此流程）

收到用户任务后，按类型选择对应流程，**不跳步、不自行发挥**。

### 基金操作类（加/删/改/查基金）

```
用户说"加基金/新增基金/纳入追踪" 
  → ❶ 加载 fund-add Skill（MUST，禁止直接改 config/funds.json）
  → ❷ Skill 内步骤：fundctl.py add → scan → enrich → fill → holdings
  → ❸ fundctl.py check（全绿才算完）
```

```
用户说"检查数据/诊断/异常" 
  → ❶ 加载 fund-diagnose Skill
  → ❷ fundctl.py diagnose → 解读输出 → auto-fix → check
```

### 代码修改类（改 scripts/ 核心逻辑）

```
用户说"改代码/重构/优化/修复" 
  → ❶ 加载 code-change Skill
  → ❷ 改前预检：blast radius（codegraph_explore）→ pipeline-contracts → 确认影响
  → ❸ 改后验证：fundctl.py check → codegraph status
  → ❹ 加载 doc-maintain Skill（如果新增/删除/改名文件）
```

### 截图/UI 类

```
用户说"截图/分享" 或 修改 screenshot.js/app.css/index.html
  → ❶ 加载 screenshot-check Skill
  → ❷ 按 Skill checklist 逐项检查
```

### 信息查询类（无代码改动）

```
用户问"XX 在哪里/XX 怎么实现的/XX 是什么逻辑"
  → ❶ codegraph_explore 查结构记忆（代码符号/调用链）
  → ❷ 无结果 → knowledge/INDEX.md 查解释记忆（ADR/gotchas/数据源）
  → ❸ 仍无结果 → grep/read 源码（最后手段）
```

### 文档/经验沉淀类

```
用户说"记下来/更新文档/这个教训记住"
  → ❶ 加载 doc-maintain Skill
  → ❷ 判断写哪里：架构决策→adr/ | 踩坑→gotchas.md | 规则→AGENT.md（人审）
```

## 关键边界（不可协商）

### 知识获取优先级
```
codegraph_explore（结构）
  → knowledge/INDEX.md（解释）
  → 源码 grep/read（最后手段）
```
**禁止跳过 codegraph_explore 直接 grep 源码**。

### 数据安全
- `fundctl.py check` 必须全绿才算任务完成
- nav_date 永不回退（lsjz 失败保留旧值，禁用 `datetime.now()` 推算）
- 写盘前 normalize：`normalize_share_keys()` / `normalize_holdings_keys()`
- scan 后必须接 enrich + fill，否则覆盖丢失已有数据

### 部署
- 禁止 CI 内嵌部署：仅 commit+push → `gh workflow run deploy-pages.yml --ref main`
- 不改既有 UI：红涨绿跌、主动基红色警告
- 新 JS/CSS 在 `index.html` 加 `?v=placeholder`

## Commands

```bash
cd scripts && python3 fundctl.py sync                      # scan→enrich→fill→holdings
cd scripts && python3 fundctl.py refresh                    # fill 增量
cd scripts && python3 fundctl.py add --code 008888 --to active 
cd scripts && python3 fundctl.py diagnose --cat X --json --auto-fix
cd scripts && python3 fundctl.py check                      # 门禁（必须全绿，7层校验）
cd ../web && python3 -m http.server 8765                    # 本地开发
```

## 门禁（commit 前）

```bash
cd scripts && python3 fundctl.py check    # Layer 0-7: nav_date→配置→lint→fixtures→一致性→文档→交叉验证
codegraph status                           # 图谱健康
```

任一条红 → 修复后再 commit。

> Standing Spec：任务完成 = `fundctl.py check` 全绿 + 零残留引用（feedback/、MEMORY.md 等不存在路径）。

## Skills

> 基金增/删/改前 MUST 先加载对应 Skill。**禁止直接改 config/funds.json 或跑全量 sync**。
> 改 scripts/ 核心逻辑前 MUST 加载 code-change Skill。**禁止跳过 blast radius 检查**。

```bash
fund-add            # 新增基金
fund-diagnose       # 数据诊断
doc-maintain        # 文档维护（结构同步 + 经验沉淀）
screenshot-check    # 截图分享约束检查
code-change         # 改核心逻辑安全检查（改前预检 + 改后验证）
```

## Evolve

1. 新架构决策 → 起草 `knowledge/adr/` 新 ADR
2. 新踩坑 → 追加 `knowledge/gotchas.md`
3. 同类异常 ≥3 次 → 提示"追加到 AGENT.md？"

人审门：AGENT.md 新增规则 → 提示后写入；knowledge/ → 起草后审。
