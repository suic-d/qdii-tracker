---
name: code-change
description: 修改 scripts/ web/ config/ 时加载。触发：改 pipeline/core 模块、前端文件、配置文件，或用户说"改代码""重构""优化""加功能"
---

# Code Change — 安全修改流程

> 两步走：blast-radius → 执行 → 验证 → 文档同步。不再啰嗦。

## Step 1: Blast Radius

改前必须 `codegraph_explore "<目标符号>"` 确认影响范围。

| 改了 | 会波及 |
|------|--------|
| `pipeline/scan.py` | enrich → fill → holdings 全链 |
| `pipeline/fill.py` | nav_date 逻辑 → web/data/*.json |
| `core/constants.py` | 所有引用 CATEGORIES/DATA_DIR 的模块 |
| `config/funds.json` | codegen → web/js/config.js |
| `web/js/*.js` | index.html 引用 |
| `web/css/*.css` | index.html 引用 |

## Step 2: Modify + Verify + Sync

```bash
# 修改代码
# ...

# 验证
cd scripts && python3 fundctl.py check

# 新 JS/CSS 文件 → 在 index.html 加 ?v= 版本戳
cd scripts && python3 stamp_asset_version.py
```

## 改中约束

| 触及模块 | 硬约束 |
|----------|--------|
| `pipeline/scan.py` | 改后 MUST 接 enrich + fill，否则覆盖已有数据 |
| `pipeline/fill.py` | **nav_date 永不回退**，lsjz 失败保留旧值 |
| `checks/verify_data.py` | fixtures 格式变更 → 同步 `knowledge/golden-fixtures.md` |
| `core/constants.py` | 改 CATEGORIES → 必须重跑全量 sync |
| `config/funds.json` | **禁止直接编辑**，通过 `fund-ops` Skill |
| `web/js/*.js` `web/css/*.css` | 新文件在 `index.html` 加 `?v=` 版本戳 |
| `web/js/screenshot.js` | 改后浏览器打开 → 截图 → 确认 PNG 正常（防空白/错位）|
| `web/css/app.css` | 改后检查暗色模式、玻璃态效果、响应式布局 |

## Step 3: 文档同步

改完后检查是否需要更新文档：

- 新架构决策 → 起草 `knowledge/adr/` 新 ADR
- 新踩坑 → 追加 `knowledge/gotchas.md`
- 模块边界变化 → 更新 `knowledge/pipeline-contracts.md`
- 文件新增/删除/改名 → 同步 `knowledge/INDEX.md` + `README.md`

## 不做的

- ~~改前逐项向用户确认~~ — blast-radius 已经说明影响，直接动手
- ~~逐篇读 ADR~~ — codegraph_explore 已索引相关知识
- ~~加载所有 knowledge 文件~~ — 按需读取
