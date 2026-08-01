---
name: fund-ops
description: QDII Tracker 基金全生命周期操作。当用户说"加基金""删基金""移除基金""调整分类""诊断""修复""检查数据"或提及基金代码+操作意图时加载。覆盖 add/delete/move/fix/check 全部场景。
---

# fund-ops — 基金全生命周期

> 一次对话搞定。内部自动循环（执行→验证→诊断→修复→再验证），用户无需手动跟进。

## 操作类型识别

| 用户意图 | 命令 | 关键词 |
|---------|------|--------|
| 新增基金 | `add` | 加/新增/添加/纳入/追踪/收录/补充 |
| 删除基金 | `remove` | 删/移除/去掉/下架/不再追踪 |
| 调整分类 | `move` | 移到/调整/换分类/改分类 |
| 快速诊断 | `diagnose` | 诊断/检查/有没有异常/数据正常吗 |
| 全量检查 | `check` | check/校验/门禁 |

## 核心协议：3 轮 auto-loop

**每轮操作后自动执行 `fundctl.py check`。失败则自动进入下一轮，无需询问用户。最多 3 轮。**

```
用户输入 → 解析意图 → 执行操作
  ↓
[第1轮] 执行命令 → fundctl.py check
  ├─ 全绿 → 报告"✅ 已就绪" → 结束
  └─ 不绿 → 自动进入第2轮（不告知用户）
  ↓
[第2轮] fundctl.py diagnose --auto-fix → fundctl.py check
  ├─ 全绿 → 报告"✅ 已修复，已就绪" → 结束
  └─ 不绿 → 自动进入第3轮（不告知用户）
  ↓
[第3轮] fundctl.py diagnose --json → 输出完整诊断
  → 报告"⚠ 已执行但 N 项数据待补全: ...（下次 refresh 会自动补上）"
```

**禁止在循环中间停下来问用户"要不要继续修"**。

## 各操作具体步骤

### add — 新增基金

```bash
# 第1轮
cd scripts && python3 fundctl.py add --code {CODE} --to {CAT} [--keyword "{KEYWORD}"]
python3 fundctl.py check
```

### remove — 删除基金

```bash
# 第1轮
cd scripts && python3 fundctl.py remove --code {CODE}
python3 fundctl.py check
```

> 注意：删除会从 config force_include 和所有分类 JSON 中移除该基金的所有份额。

### move — 调整分类

```bash
# 第1轮
cd scripts && python3 fundctl.py move --keyword "{KEYWORD}" --from {FROM_CAT} --to {TO_CAT}
python3 fundctl.py check
```

### diagnose / fix — 诊断修复

```bash
# 直接进入第2轮（第1轮等同于 diagnose）
cd scripts && python3 fundctl.py diagnose --cat {CAT} --auto-fix
python3 fundctl.py check
```

### check — 全量门禁

```bash
# 只跑 check，不自动修复
cd scripts && python3 fundctl.py check
```

## 约束

- 禁止直接改 `config/funds.json`，必须通过 `fundctl.py` CLI
- 禁止跳过 `fundctl.py check`
- remove 操作不可逆（数据从 JSON 删除），执行前向用户确认基金代码和名称
- scan 后必须接 enrich + fill（add 命令已内置）
- nav_date 永不回退
