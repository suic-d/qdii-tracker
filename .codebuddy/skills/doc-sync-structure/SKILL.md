---
name: doc-sync-structure
description: 当用户新增/删除/重命名/移动项目文件或目录，需要更新文档中的目录结构时加载
---

# Doc Sync Structure — 文档目录同步

> 职责：改动目录结构后，提议更新以下文档，人确认后提交。

## 触发条件

以下操作之一发生时加载：
- 新增/删除/重命名/移动文件或目录
- 用户说"更新文档""同步目录结构""refresh docs"

## 需要更新的文档

| 文档 | 更新内容 | 原因 |
|------|---------|------|
| `README.md` | 目录树章节 | 人类访客看这里了解结构 |
| `knowledge/INDEX.md` | 架构全景 + 知识分区速查表 | Agent 看这里导航到正确知识 |
| `knowledge/gotchas.md` | 如果改动引入新坑 | 踩坑记录 |

## 不需要更新的文档

- **AGENT.md**：只更新行为相关路径（如 `fundctl.py check` 命令），不更新目录树。AGENT.md 是给 Agent 的约束基线，不是项目结构文档。
- **MEMORY.md**：只在追加"最近关键变更"时需要，被动触发而非结构化同步。

## Gotchas

- README 目录树只列对人 **有意**的目录（不列 `.codegraph/` / `.loop/` 等运行时产物）
- 软链接在目录树中标注 `→ (软链接)`，如 `plans/QDII基金追踪.md → (软链接到 brain 方案文档)`
- 不删除 `knowledge/adr/` 下的任何文件（ADR 是持久记录）
- `feedback/` 下的 `ui_scenarios/` 也需反映新增场景文件
- 同步 `knowledge/gotchas.md` 时标注日期和状态
