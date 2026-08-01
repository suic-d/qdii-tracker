---
name: doc-maintain
description: 文档维护（结构同步 + 经验沉淀）。触发：新增/删除/改名文件 / 踩坑后沉淀 / 架构决策后记录
---

# Doc Maintain — 文档同步 + 经验沉淀

> 合并自原 `doc-sync-structure` + `doc-sync-evolve` 两个 Skill。

## 触发条件

| 用户意图 | 触发 |
|---------|------|
| 新增/删除/重命名/移动文件 | 结构同步 |
| "把这个教训记下来""沉淀到规则里" | 经验沉淀 |
| "更新AGENT.md" | 规则追加 |

---

## Part A: 结构同步

### 需要更新的文件

| 文件 | 更新内容 |
|------|---------|
| `knowledge/INDEX.md` | 分区速查表 + 技术栈 + 目录索引 |
| `README.md` | 目录树 |

### 不需要更新的文件

- **AGENT.md**：只更新行为相关路径，不更新目录树
- **knowledge/adr/**：不删除（持久记录）

### 执行步骤

1. 确认变更范围（git diff --name-only / 用户指定）
2. 更新 `knowledge/INDEX.md` 的分区速查表
3. 更新 `README.md` 的目录树
4. 如涉及 skills → 同步更新 `.codebuddy/skills/` 内引用
5. `test/ui_scenarios/` 也需反映新增场景

---

## Part B: 经验沉淀

### 判定去哪里

1. **这是每次任务都要遵守的行为约束？**
   → 写入 AGENT.md（Critical Rules）
   → 代码级细节不写（CodeGraph 可查）

2. **这是跨会话必须记住的变更事实？**
   → 写入 `knowledge/gotchas.md`（标注类型：变更事实）

3. **这是需要长期记录的架构决策？**
   → 起草 `knowledge/adr/` 新 ADR（完整格式）

4. **这是某类场景的踩坑经验？**
   → 追加 `knowledge/gotchas.md`（含状态/日期）

### 写入原则

- `knowledge/` = 唯一权威知识源
- AGENT.md = 精简，只存 Critical Rules
- 不确定是否该加 → 先写到 knowledge/ 对应文件，确认后再提 AGENT.md
- 新规则与现有规则矛盾 → 先指出冲突，让人裁决

---

## Part C: 变更后检查

改完代码后检查：
- 新架构决策 → 起草 `knowledge/adr/` 新 ADR
- 新踩坑 → 追加 `knowledge/gotchas.md`
- 模块边界变化 → 更新 `knowledge/pipeline-contracts.md`
- 同类异常 ≥3 次 → 提示"是否追加到 AGENT.md？"
