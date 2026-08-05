# 已知坑点（Gotchas）

> 含源码行号 + 生命周期管理。同一坑 3 次复发 → 提示升级到 AGENT.md Critical Rules。

| ID | 现象 | 根因 | 源码位置 | 状态 | 发现日期 | 修复日期 |
|----|------|------|----------|------|----------|----------|
| G001 | 截图空白 | cloneNode `left:-99999px` 离屏 → html-to-image 渲染空白 | `web/js/screenshot.js:snapPng()` | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G002 | 表格错位 | 克隆挂 `document.body` → 丢 CSS 上下文（`.ss-preview td` 等选择器匹配不到） | `web/js/screenshot.js:snapPng()` | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G003 | 指标卡脏阴影 | html-to-image 渲染 `box-shadow` 在半透明背景上显脏影 | `web/css/app.css:.ss-mkt-card` | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G004 | backdrop-filter 无效果 | 缺 `-webkit-` 前缀 → Safari/iOS 无效 | `web/css/app.css:玻璃态规则` | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G005 | 远程 API ERR_EMPTY_RESPONSE | 东方财富 push2/push2his 对 GitHub Pages 跨站来源限制访问（本地正常） | `web/js/market-indices.js:fetchAll()` / `web/js/market-trend.js:fetchDayKFromHost()` | ⚠️已知限制 | 2026-07 | — |
| G006 | 截图弹窗暗色消失 | `snapPng()` 截完恢复暗色时 `classList.add('dark')` 覆盖了截前的 `classList.remove` → 截完可能丢失暗色 | `web/js/screenshot.js:snapPng()` | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G007 | NAV 日期 `<div>` 换行 | 表头 `<div>` 自动换行导致两行过高 | `web/index.html` 净值列 | ✅已修复 | 2026-07-13 | 2026-07-13 |
| G008 | scan 后不接 enrich+fill | scan 覆盖现有 JSON → 丢失 enrich 填充的规模和费率数据 | `scripts/fundctl.py::cmd_sync()` | ✅已修复 | — | — |
| G009 | LOF chg_ytd 为空 | LOF 场内份额不暴露场外收益字段 | `scripts/pipeline/fill.py:_fill_ytd()` → 取同系列兄弟份额兜底 | ✅已修复 | — | — |
| G010 | 份额 key 顺序不一致 | 多脚本写盘时 dict key 顺序依赖插入顺序 → diff 噪音 | `scripts/core/utils.py::normalize_share_keys()` | ✅已修复 | — | — |
| G011 | 主动基金「每日可购买」显示错误恒定值 ¥7200 | `renderGroupNotice()` 使用 `daily_purchase` 字段求和，但该字段从未被 pipeline 更新，72 个份额全是死值 100 | `web/js/main.js:renderGroupNotice()` → 改用 `daily_limit`（AKShare 真实数据） | ✅已修复 | 2026-08-05 | 2026-08-05 |
| G012 | 详情 Modal「日买入限额」始终不显示「暂停」 | `render-modal.js:103` 用了不存在的字段 `share.purchase_state`，实际字段是 `share.buy_status` | `web/js/render-modal.js:103` | ✅已修复 | 2026-08-05 | 2026-08-05 |
| G013 | 截图弹窗 + 申购浮层在亮色模式下完全无样式 | `.ss-*` 和 `.buy-hist-tip` 只有暗色覆盖（`html.dark`），亮色基础 CSS 全部缺失 | `web/css/app.css` → 补全 ~420 行亮色样式 | ✅已修复 | 2026-08-05 | 2026-08-05 |
| G014 | 版本戳 `?v=` 漏打 ES module 单引号路径 | `stamp_asset_version.py` 正则只匹配双引号 `"`，5 处 `import from '...'` 从不更新 | `scripts/checks/stamp_asset_version.py` → 正则兼容双引号+单引号 | ✅已修复 | 2026-08-05 | 2026-08-05 |

## Gotchas 生命周期规则
- 已修复 → 保留条目，标记 `✅已修复`（不删——后人要知道坑存在过）
- 新发现 → 追加，标记 `🐛待修复`
- 同一坑 3 次复发 → 提示升级到 AGENT.md Critical Rules
- 每月审查一次：标记 `✅已修复` 超过 6 个月的条目可考虑归档

## 编码约定 → 见 AGENT.md Critical Rules

## 诊断严重度分档理由

| 检测项 | 严重度 | 分档理由 |
|--------|--------|----------|
| `nav_stale` | error | 数据 >3 天未更新，前端显示严重过期，用户直接感知 |
| `missing_nav` | warning | 单只基金净值缺失，可自动修复（refresh），不影响整体可用性 |
| `missing_fee` | warning | 费率数据缺失，不影响核心净值展示，但影响费率 tooltip 展示 |
| `buy_status_no_date` | info | 申购状态日期字段不完整，纯信息性，下次 fill 自动补充 |
