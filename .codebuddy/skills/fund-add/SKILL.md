---
name: fund-add
description: QDII Tracker 新增一只基金。当用户说"加基金""新增基金""添加追踪""加入""纳入""补充""收录"或提到基金代码+分类（如"把 457001 加入 active"）时加载。
---
<!-- yao-meta-skill: description 扩容。原 4 个触发词 → 18 个语义变体。根因：Agent 表述"纳入/加入/补充"不进"加基金"，跳过 skill 直接改 config + full sync。 -->

# fund-add — QDII Tracker 基金新增

## 输入
- 基金代码（6位数字）
- 目标分类：active / etf / sp500 / nasdaq_passive / global_index / global_other
- 基金关键词（用于分类白名单匹配，非必填）

## 流程（3 轮迭代，最多 3 轮）

### 第 1 轮
```bash
cd scripts && python3 fundctl.py add --code {CODE} --to {CAT} [--keyword "{KEYWORD}"]
python3 fundctl.py check
```
→ 通过？报告"已就绪"
→ 失败？记录错误类型，进第 2 轮

### 第 2 轮
```bash
python3 fundctl.py diagnose --cat {CAT} --auto-fix
python3 fundctl.py check
```
→ 通过？报告"已修复，基金已就绪"
→ 失败？进第 3 轮

### 第 3 轮
```bash
python3 fundctl.py diagnose --cat {CAT} --json
```
输出完整诊断报告（已尝试修复 + 失败原因）
标记：需人工介入
在 feedback/anomalies.md 追加一条异常记录

## 约束（来自 AGENT.md Critical Rules）
- scan 后必须接 enrich + fill
- nav_date 永不回退
- force_include 不跨分类继承
- 新增后用 check 验证，不过不算完

## 相关知识
- 架构全景 + 核心概念速查：`knowledge/INDEX.md`
- 代码结构追踪：使用 `codegraph_explore` 理解流水线调用链
- 分类规则 SSOT：`config/funds.json`
- 常见坑点：`knowledge/gotchas.md`

## Gotchas
- 新基金第 2 天才有净值，check 报 missing_nav 不是 bug（T+1 特性）
- add 后 check 报"代码不存在于数据"：scan 没扫到，检查基金是否已上市
- keywords 只对 active 分类生效（匹配 active_whitelist）
- 不要 add 后紧接着 sync——add 已做局部 scan+enrich+fill
- **🚫 严禁手动改 `config/funds.json` + 跑 `fundctl.py sync` 来「加基金」**：那是全量管线（scan→enrich→fill→holdings），不是增量新增。正确做法：`fundctl.py add --code {CODE} --to {CAT}`。实际事故：2026-07-31，Agent 未加载本 Skill，手动改 funds.json whitelist + force_include 再跑全量 sync，把「增量新增」做成了「手动改配置 + 全量sync」。
