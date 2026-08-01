---
name: code-change
description: 修改 scripts/ 核心逻辑时加载。触发：改 pipeline/core 模块，或用户说"改代码""重构""优化"
---

# Code Change — 安全检查清单

> 防止改代码时破坏数据管线或前端。

## 改前检查

1. **加载知识**：`AGENT.md` → `knowledge/INDEX.md` → `codegraph_explore "<目标模块>"`
2. **查 blast radius**：`codegraph_explore` 找到所有调用方
3. **读 ADR**：如果有相关架构决策，先读 `knowledge/adr/`

### 改前预检（生成清单）

在开始改代码前，向用户确认：
1. 本次改动会影响哪些模块？（用 `codegraph_explore "<目标符号>"` 查 blast radius）
2. 影响的模块在 `knowledge/pipeline-contracts.md` 中的契约是什么？
3. `fundctl.py check` 的哪一层可能失败？
4. 是否需要更新 `knowledge/` 下的文档？

确认后再动手改代码。

## 改中约束

| 模块 | 约束 |
|------|------|
| `pipeline/scan.py` | 改 scan 逻辑后 MUST 接 enrich + fill，否则覆盖已有数据 |
| `pipeline/fill.py` | nav_date 永不回退，lsjz 失败保留旧值 |
| `pipeline/verify_data.py` | fixtures 格式变更后同步 `knowledge/golden-fixtures.md` |
| `core/constants.py` | 改 CATEGORIES 后必须 `fundctl.py reclassify --all` |
| `config/funds.json` | **禁止不通过 fund-add Skill 直接改 JSON** |
| `web/js/*.js` | 新文件在 `index.html` 加 `?v=placeholder` |
| `web/css/*.css` | 同上 |

## 改后验证

```bash
cd scripts && python3 fundctl.py check    # 必须全绿
codegraph status                           # 图谱健康
```

## 文档更新

改完后检查是否需要更新：
- 新架构决策 → `knowledge/adr/` 新 ADR
- 新踩坑 → `knowledge/gotchas.md`
- 模块边界变化 → `knowledge/pipeline-contracts.md`
