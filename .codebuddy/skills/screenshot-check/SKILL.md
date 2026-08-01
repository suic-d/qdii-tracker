---
name: screenshot-check
description: 修改截图分享相关代码时加载。触发：改 screenshot.js / app.css / index.html 截图相关结构，或用户说"截图""分享""snapPng"
---

# Screenshot Check — 截图分享约束

> 从 AGENT.md 迁移。修改截图相关代码后的强制检查清单。

## 结构约束

- **screenshot.js**：IIFE，`html-to-image` CDN 懒加载；CSS 独立 `app.css`
- **卡片结构**：外层 `.ss-phone-wrap`（唯一带边框）+ 内层 `.ss-inner` × 2（无边框）→ **不改结构**
- **宽度自适应**：wrap `fit-content` + dialog `rAF` 同步 `style.width`
- **窄屏**：`.ss-chip-group`/`.ss-col-grid` `min-width:0`；`.ss-tbl-wrap { overflow-x: auto }`
- **净值列**：日期内联 `<span>·MM-DD</span>`，不换行
- **列筛选**：`locked:true` 不显示面板；`sortable:true` 可排序
- **表头对齐**：申购居中 / 数字右对齐 / 其余左对齐

## 视觉约束

- **iPhone**：截前在克隆体上移除 `backdrop-filter`，`navigator.share()` 存相册
- **玻璃态 UI**：Chip/Tab/分享按钮激活态中性渐变跟随主题（亮=深底白字，暗=浅底深字）；市场卡/弹窗 `backdrop-filter:blur`；`-webkit-` 前缀必配
- **申购历史**：`_update_history()` → `buy_status_history[]`；状态+额度都没变则保持原日期；任一变化追加新条目
- **指标卡**：轮廓用 `border`，不用 `box-shadow`；7 风格覆盖 `border-color`，`box-shadow:none`

## snapPng() 约束

- `cloneNode` 离屏渲染 → 不改可见 DOM
- 克隆体 `position:absolute` + `#ss-preview{position:relative}`（必须挂 preview 下）
- 截前 `clone.style.boxShadow='none'` 去外框阴影 + `classList.remove('dark')` 强制亮色
- 截后恢复暗色
- 详见 `knowledge/adr/002-clonenode-off-screen-render.md`

## 每次修改后检查

- [ ] 保存 PNG 无外框阴影 → `snapPng()` 截前 `clone.style.boxShadow = 'none'`
- [ ] 克隆体 `position:absolute` + 挂 `#ss-preview` → 不丢 CSS 上下文
- [ ] 指标卡 border + no box-shadow → 7 风格全覆盖
- [ ] 手机端表格 → `.ss-tbl-wrap { overflow-x: auto }`
