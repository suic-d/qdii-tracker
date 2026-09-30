#!/bin/sh
# 启用本地 git hooks：pre-commit 自动 doc_sync，pre-push 自动跑单测 + 数据门禁。
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git config core.hooksPath .githooks
echo "✅ core.hooksPath = .githooks"
echo "   pre-commit：doc_sync 自动同步文档"
echo "   pre-push：pytest + fundctl check --offline --agent-rules"
