---
name: fund-diagnose
description: QDII Tracker 数据健康检查。当用户说"检查数据""诊断""有没有异常""数据正常吗"时加载。
---

# fund-diagnose — QDII 数据健康巡检

## 执行
```bash
cd scripts && python3 fundctl.py diagnose
```

## 输出解读

| 输出 | 含义 | 行动 |
|------|------|------|
| `✅ 数据正常` | 全部绿 | 不需要动作 |
| `[WARNING] missing_nav: ...` | 某基金净值缺失 | `--auto-fix` 自动补 |
| `[ERROR] nav_stale: ...` | 某分类 >3 天未更新 | 检查 CI pipeline.fill |
| `[INFO] buy_status_no_date: ...` | 申购状态日期缺字段 | 下次 fill 自动补 |
| `[WARNING] missing_fee: ...` | 费率数据缺失 | `fundctl.py sync` 重拉 |

## 自动修复（--auto-fix）
- 只修 missing_nav（执行 refresh）
- 单次尝试，不重试（避免 CI timeout）
- 修复后跑 check 验证

## 诊断严重度分档理由

| 检测项 | 严重度 | 分档理由 |
|--------|--------|----------|
| `nav_stale` | error | 数据 >3 天未更新，前端显示严重过期，用户直接感知 |
| `missing_nav` | warning | 单只基金净值缺失，可自动修复，不影响整体可用性 |
| `missing_fee` | warning | 费率数据缺失，不影响核心净值展示，但影响费率 tooltip |
| `buy_status_no_date` | info | 申购状态日期字段不完整，纯信息性，下次 fill 自动补 |

## 相关知识
- 数据源异常模式：`knowledge/data-sources.md` 中各 API 的已知限制
- 代码结构追踪：使用 `codegraph_explore` 理解 diagnose 调用链
- 常见坑点：`knowledge/gotchas.md`

## Gotchas
- 入库 ≤3 天的新基金无净值是正常现象，diagnose 不报
- auto-fix 只跑一次，不重试
- nav_stale 不会自己好，需要排查上游 pipeline
- **Builder 的 diagnose 输出与 Judge 裁决是两轮独立调用**：Builder 跑 `diagnose --json` 生成修复前基线，Judge 在新上下文中独立跑 `diagnose --json` 做修复后验证
