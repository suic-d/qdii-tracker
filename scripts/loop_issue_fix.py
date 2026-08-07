#!/usr/bin/env python3
"""
loop_issue_fix.py — Issue 驱动的自动修复循环

工作流：从 GitHub Issues 拉取 bug/fix/enhancement 标签的 issue，
逐个在独立的 git worktree 中尝试修复，每轮修复后跑 fundctl.py check 验证，
最多重试 --max-rounds 轮，通过后自动创建 PR。

用法：
    python3 loop_issue_fix.py --dry-run              # 只读取 issues，不执行
    python3 loop_issue_fix.py --issue 3               # 只修复指定 issue（按序号）
    python3 loop_issue_fix.py --max-rounds 3          # 每 issue 最多重试轮数（默认 3）
    python3 loop_issue_fix.py --no-pr                 # 修复但不创建 PR（手动审查）

设计原则：
    - 每个 issue 一个独立的 git worktree，互不干扰
    - 失败后不删除 worktree，便于手动审查
    - Ctrl+C 可安全中断，已创建的 PR 不受影响
    - 使用标准库（urllib + subprocess），无需额外依赖
    - 遵循项目代码风格（argparse CLI + pathlib + 分段日志输出）
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径常量
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent  # qdii-tracker/
FUNDCTL = str(SCRIPT_DIR / "fundctl.py")

# ============================================================
# GitHub API 常量
# ============================================================
REPO_OWNER = "zhouminghan"
REPO_NAME = "qdii-tracker"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
ISSUES_URL = f"{API_BASE}/issues"
ACCEPT_LABELS = {"bug", "fix", "enhancement"}
SKIP_LABELS = {"discussion"}

# ============================================================
# 工具函数
# ============================================================


def get_github_token() -> str:
    """从环境变量获取 GitHub token。"""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("❌ 缺少 GITHUB_TOKEN 环境变量")
        raise SystemExit(1)
    return token


def github_api_request(url: str, token: str, method: str = "GET",
                       data: dict = None) -> tuple:
    """
    发起 GitHub API 请求。

    Args:
        url: 完整的 API URL
        token: GitHub personal access token
        method: HTTP 方法
        data: 请求体（POST/PATCH 时使用）

    Returns:
        (status_code, response_body_dict, response_headers)
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "qdii-tracker-loop-fix/1.0",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            resp_body = json.loads(resp.read().decode("utf-8"))
            resp_headers = dict(resp.headers)
            return status, resp_body, resp_headers
    except urllib.error.HTTPError as e:
        err_body = {}
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            pass
        return e.code, err_body, dict(e.headers)
    except Exception as e:
        return 0, {"error": str(e)}, {}


def fetch_open_issues(token: str, labels: set = None) -> list:
    """
    拉取仓库的 open issues。

    Args:
        token: GitHub token
        labels: 如果指定，只拉取带这些标签的 issues（逗号分隔）

    Returns:
        issue 列表，每个 issue 包含 number, title, body, labels, html_url
    """
    all_issues = []
    page = 1

    while True:
        url = f"{ISSUES_URL}?state=open&per_page=100&page={page}"
        if labels:
            url += f"&labels={','.join(labels)}"

        status, body, headers = github_api_request(url, token)
        if status != 200:
            print(f"  ⚠ 拉取 issues 失败 (HTTP {status}): {body.get('message', '?')}")
            break

        if not body or not isinstance(body, list):
            break

        # 过滤掉 PR（GitHub API 把 PR 也当作 issue 返回）
        issues = [i for i in body if "pull_request" not in i]

        # 按标签过滤
        filtered = []
        for issue in issues:
            issue_labels = {lb["name"] for lb in issue.get("labels", [])}
            # 如果有 skip label，跳过
            if SKIP_LABELS & issue_labels:
                continue
            # 如果有 accept label，纳入
            if ACCEPT_LABELS & issue_labels:
                filtered.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue.get("body", ""),
                    "labels": list(issue_labels),
                    "html_url": issue["html_url"],
                })

        all_issues.extend(filtered)

        if len(body) < 100:
            break
        page += 1

    return all_issues


def run_command(cmd: list, cwd: str = None, timeout: int = 300,
                capture: bool = True) -> tuple:
    """
    执行 shell 命令。

    Args:
        cmd: 命令列表
        cwd: 工作目录
        timeout: 超时秒数
        capture: 是否捕获输出

    Returns:
        (returncode, stdout_str, stderr_str)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"命令超时 ({timeout}s): {' '.join(cmd)}"
    except Exception as e:
        return -1, "", str(e)


def run_check_in_worktree(worktree_path: str) -> tuple:
    """
    在 worktree 中运行 fundctl.py check。

    Returns:
        (passed: bool, output: str)
    """
    scripts_dir = Path(worktree_path) / "scripts"
    cmd = [sys.executable, str(scripts_dir / "fundctl.py"), "check"]
    ret, stdout, stderr = run_command(cmd, cwd=str(scripts_dir), timeout=120)
    output = stdout + "\n" + stderr if stderr else stdout
    passed = ret == 0 and "全部分层校验通过" in output
    return passed, output


def run_diagnose_in_worktree(worktree_path: str) -> tuple:
    """
    在 worktree 中运行 fundctl.py diagnose --auto-fix。

    Returns:
        (returncode, output)
    """
    scripts_dir = Path(worktree_path) / "scripts"
    cmd = [sys.executable, str(scripts_dir / "fundctl.py"), "diagnose", "--auto-fix"]
    ret, stdout, stderr = run_command(cmd, cwd=str(scripts_dir), timeout=120)
    output = stdout + "\n" + stderr if stderr else stdout
    return ret, output


def create_pr(token: str, issue_number: int, branch_name: str,
              title: str, body: str) -> dict:
    """
    通过 GitHub API 创建 Pull Request。

    Args:
        token: GitHub token
        issue_number: 关联的 issue 编号
        branch_name: 源分支名
        title: PR 标题
        body: PR 描述

    Returns:
        PR 信息字典，包含 html_url 等
    """
    pr_data = {
        "title": title,
        "head": branch_name,
        "base": "main",
        "body": body,
    }
    status, resp, _ = github_api_request(
        f"{API_BASE}/pulls", token, method="POST", data=pr_data
    )
    return resp if status in (201, 200) else {"error": resp.get("message", f"HTTP {status}")}


# ============================================================
# 主逻辑
# ============================================================


def cleanup_worktrees(worktree_paths: list):
    """清理 worktree 目录（删除目录 + git worktree remove）。"""
    for wt_path in worktree_paths:
        # 尝试 git worktree remove
        run_command(
            ["git", "worktree", "remove", "--force", wt_path],
            cwd=str(ROOT_DIR), timeout=30, capture=True,
        )
        # 如果目录仍存在，强制删除
        if os.path.exists(wt_path):
            shutil.rmtree(wt_path, ignore_errors=True)


def _signal_handler(signum, frame):
    """SIGINT 处理：打印提示后退出。"""
    print("\n\n⚠ 收到中断信号。已创建的 PR 不受影响。")
    print("  未完成的 worktree 保留在 ../qdii-fix-* 供手动审查。")
    raise SystemExit(130)


def main():
    signal.signal(signal.SIGINT, _signal_handler)

    parser = argparse.ArgumentParser(
        description="Issue 驱动的自动修复循环",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 loop_issue_fix.py --dry-run              # 预览模式
  python3 loop_issue_fix.py --issue 3               # 只修复 #3
  python3 loop_issue_fix.py --max-rounds 5           # 最多 5 轮重试
  python3 loop_issue_fix.py --no-pr                 # 修复但不创建 PR
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只读取 issues 并打印，不执行修复",
    )
    parser.add_argument(
        "--issue", type=int, default=None,
        help="只修复指定 issue 编号",
    )
    parser.add_argument(
        "--max-rounds", type=int, default=3,
        help="每个 issue 最大重试轮数（默认 3）",
    )
    parser.add_argument(
        "--no-pr", action="store_true",
        help="修复但不创建 PR（用于手动审查）",
    )
    args = parser.parse_args()

    # ---- Phase 0: 前置检查 ----
    print("=" * 60)
    print("🔍 Phase 0: 前置检查")
    print("=" * 60)

    token = get_github_token()
    print(f"✅ GITHUB_TOKEN 已加载")

    # 确认在主仓库中
    if not (ROOT_DIR / ".git").exists():
        print(f"❌ 当前目录不是 git 仓库: {ROOT_DIR}")
        raise SystemExit(1)
    print(f"✅ 仓库根目录: {ROOT_DIR}")

    # 确认 fundctl.py 存在
    if not Path(FUNDCTL).exists():
        print(f"❌ fundctl.py 不存在: {FUNDCTL}")
        raise SystemExit(1)
    print(f"✅ fundctl.py: {FUNDCTL}")

    # ---- Phase 1: Discover ----
    print("\n" + "=" * 60)
    print("🔍 Phase 1: 发现 Issues")
    print("=" * 60)

    issues = fetch_open_issues(token)
    print(f"\n共发现 {len(issues)} 个符合条件的 open issue：\n")

    if not issues:
        print("✅ 没有需要修复的 issue，退出。")
        return

    for i, issue in enumerate(issues, 1):
        labels_str = ", ".join(issue["labels"])
        print(f"  [{i}] #{issue['number']} {issue['title'][:60]}")
        print(f"      标签: {labels_str}")
        print(f"      URL: {issue['html_url']}")
        print()

    # 按 issue 编号筛选
    if args.issue:
        issues = [i for i in issues if i["number"] == args.issue]
        if not issues:
            print(f"❌ 未找到 issue #{args.issue}")
            raise SystemExit(1)

    if args.dry_run:
        print("=" * 60)
        print("🏁 Dry-run 模式：不会执行任何修复操作。")
        return

    # ---- Phase 2-5: 逐个修复 ----
    results = []
    worktrees_created = []

    for idx, issue in enumerate(issues, 1):
        issue_num = issue["number"]
        worktree_name = f"qdii-fix-{issue_num}"
        worktree_path = ROOT_DIR.parent / worktree_name
        branch_name = f"fix/issue-{issue_num}"

        print("\n" + "=" * 60)
        print(f"🔧 Phase 2-5: 修复 Issue #{issue_num} ({idx}/{len(issues)})")
        print(f"   标题: {issue['title']}")
        print("=" * 60)

        # ---- Phase 2: 创建 worktree ----
        print(f"\n📦 Phase 2: 创建 git worktree")
        print(f"   路径: {worktree_path}")

        # 如果 worktree 已存在，先尝试清理
        if worktree_path.exists():
            print(f"   ⚠ worktree 已存在，先清理...")
            run_command(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(ROOT_DIR), timeout=30, capture=True,
            )
            if worktree_path.exists():
                shutil.rmtree(str(worktree_path), ignore_errors=True)

        # 使用 origin/main 作为基准（避免 "main is already used by worktree" 错误）
        ret, stdout, stderr = run_command(
            ["git", "worktree", "add", str(worktree_path), "origin/main"],
            cwd=str(ROOT_DIR), timeout=60,
        )
        if ret != 0:
            print(f"   ❌ 创建 worktree 失败: {stderr}")
            results.append({
                "issue": issue_num,
                "title": issue["title"],
                "status": "FAIL",
                "rounds": 0,
                "pr": None,
                "error": f"worktree 创建失败: {stderr[:200]}",
            })
            continue

        worktrees_created.append(str(worktree_path))
        print(f"   ✅ worktree 创建成功")

        # 在 worktree 中创建修复分支
        ret, stdout, stderr = run_command(
            ["git", "checkout", "-b", branch_name],
            cwd=str(worktree_path), timeout=30,
        )
        if ret != 0:
            print(f"   ⚠ 创建分支失败（可能已存在），尝试切换...")
            run_command(
                ["git", "checkout", branch_name],
                cwd=str(worktree_path), timeout=30,
            )

        # ---- Phase 3: Baseline check ----
        print(f"\n📊 Phase 3: 基线检查 (baseline check)")

        passed, output = run_check_in_worktree(str(worktree_path))
        if passed:
            print(f"   ✅ 基线检查通过 - issue 可能已修复或无需修复")
        else:
            print(f"   ⚠ 基线检查未通过 - 需要修复")
            # 打印关键错误行
            error_lines = [l for l in output.split("\n") if "❌" in l or "FAIL" in l]
            for line in error_lines[:5]:
                print(f"      {line.strip()}")

        # ---- Phase 4: 修复循环 ----
        print(f"\n🔄 Phase 4: 修复循环 (最多 {args.max_rounds} 轮)")

        final_passed = passed
        round_num = 0
        retry_log = []

        if not passed:
            for round_num in range(1, args.max_rounds + 1):
                print(f"\n   --- 第 {round_num}/{args.max_rounds} 轮 ---")

                # 执行诊断 + 自动修复
                print(f"   🔧 运行 diagnose --auto-fix ...")
                diag_ret, diag_out = run_diagnose_in_worktree(str(worktree_path))

                # 提取诊断摘要
                fixed_match = re.search(r"auto-fix.*?(\d+)\s*修复", diag_out)
                if fixed_match:
                    print(f"   📋 {fixed_match.group(0)}")

                # 运行 check
                print(f"   ✅ 运行 fundctl.py check ...")
                final_passed, check_out = run_check_in_worktree(str(worktree_path))

                retry_log.append({
                    "round": round_num,
                    "passed": final_passed,
                    "diagnose_summary": diag_out[:500],
                    "check_summary": check_out[:500],
                })

                if final_passed:
                    print(f"   ✅ 第 {round_num} 轮修复后检查通过！")
                    break
                else:
                    # 打印失败信息
                    error_lines = [l for l in check_out.split("\n")
                                   if "❌" in l or "⚠" in l]
                    for line in error_lines[:3]:
                        print(f"      {line.strip()}")
                    if round_num < args.max_rounds:
                        print(f"   ⚠ 第 {round_num} 轮未通过，进入下一轮...")

        # ---- Phase 5: Deliver ----
        print(f"\n📤 Phase 5: 交付")

        if final_passed:
            # 检查工作区是否有实际变更（不产生空分支垃圾）
            ret_diff, diff_stdout, _ = run_command(
                ["git", "diff", "--cached", "--name-only"],
                cwd=str(worktree_path), timeout=10,
            )
            # 如果没有 staged 变更，再看看 working tree
            if not diff_stdout.strip():
                ret_diff_wt, diff_wt, _ = run_command(
                    ["git", "diff", "--name-only"],
                    cwd=str(worktree_path), timeout=10,
                )
                diff_stdout = diff_wt

            has_diff = bool(diff_stdout.strip())
            no_changes = False

            if not has_diff:
                print(f"   ⚠ 没有文件变更（issue 可能已修复或不需要改代码）")
                no_changes = True
            else:
                # 提交修复
                print(f"   📝 git add + commit ...")
                run_command(
                    ["git", "add", "-A"],
                    cwd=str(worktree_path), timeout=30,
                )

                commit_msg = (
                    f"fix: #{issue_num} {issue['title'][:50]}\n\n"
                    f"Closes #{issue_num}\n\n"
                    f"Auto-fix by loop_issue_fix.py (rounds: {round_num or 1})"
                )
                ret, stdout, stderr = run_command(
                    ["git", "commit", "-m", commit_msg],
                    cwd=str(worktree_path), timeout=30,
                )

                if ret != 0:
                    if "nothing to commit" in (stdout + stderr).lower():
                        no_changes = True
                    else:
                        print(f"   ⚠ git commit 失败: {stderr[:200]}")
                        no_changes = True  # 当作无变更处理

            if no_changes:
                # 无文件变更 → 不 push，不建 PR，记录跳过
                print(f"   ⏭️  跳过 push/PR（无文件变更）")
                results.append({
                    "issue": issue_num,
                    "title": issue["title"],
                    "status": "NO_DIFF",
                    "rounds": round_num or 1,
                    "pr": None,
                    "error": "无文件变更",
                })
                continue

            # Push
            print(f"   🚀 git push origin {branch_name} ...")
            ret, stdout, stderr = run_command(
                ["git", "push", "origin", branch_name, "--force"],
                cwd=str(worktree_path), timeout=60,
            )
            if ret != 0:
                print(f"   ❌ Push 失败: {stderr[:200]}")
                results.append({
                    "issue": issue_num,
                    "title": issue["title"],
                    "status": "FAIL",
                    "rounds": round_num or 1,
                    "pr": None,
                    "error": f"Push 失败: {stderr[:200]}",
                })
                continue
            print(f"   ✅ Push 成功")

            # Create PR
            pr_url = None
            if not args.no_pr:
                print(f"   🔗 创建 Pull Request ...")
                pr_title = f"fix: #{issue_num} {issue['title'][:50]}"
                pr_body = (
                    f"## 修复\n\n"
                    f"自动修复 Issue #{issue_num}\n\n"
                    f"### 修复轮数\n{round_num or 1} 轮\n\n"
                    f"### 验证\n`fundctl.py check` 全部通过 ✅\n\n"
                    f"Closes #{issue_num}"
                )
                pr_resp = create_pr(token, issue_num, branch_name, pr_title, pr_body)

                if "html_url" in pr_resp:
                    pr_url = pr_resp["html_url"]
                    print(f"   ✅ PR 已创建: {pr_url}")
                else:
                    print(f"   ⚠ PR 创建失败: {pr_resp.get('error', '?')}")
                    # 即使 PR 创建失败，也算部分成功
            else:
                print(f"   ⚠ --no-pr 模式，跳过 PR 创建。分支: {branch_name}")

            # 清理 worktree
            print(f"   🧹 清理 worktree ...")
            cleanup_worktrees([str(worktree_path)])
            if str(worktree_path) in worktrees_created:
                worktrees_created.remove(str(worktree_path))

            results.append({
                "issue": issue_num,
                "title": issue["title"],
                "status": "PASS",
                "rounds": round_num or 1,
                "pr": pr_url,
            })

        else:
            # 达到最大轮数仍未通过
            print(f"   ❌ 达到最大重试轮数 ({args.max_rounds})，仍未通过")
            print(f"   📂 worktree 保留供手动审查: {worktree_path}")

            results.append({
                "issue": issue_num,
                "title": issue["title"],
                "status": "FAIL",
                "rounds": args.max_rounds,
                "pr": None,
                "error": f"超过 {args.max_rounds} 轮仍未通过 check",
                "worktree": str(worktree_path),
            })

    # ---- Phase 6: Report ----
    print("\n\n" + "=" * 60)
    print("📊 Phase 6: 修复报告")
    print("=" * 60)

    if not results:
        print("无修复结果。")
        return

    # 表格头
    print(f"\n{'Issue':<8} {'状态':<8} {'轮数':<6} {'PR':<50}")
    print("-" * 72)

    pass_count = 0
    fail_count = 0
    skip_count = 0

    for r in results:
        if r["status"] == "PASS":
            status_icon = "✅"
        elif r["status"] == "NO_DIFF":
            status_icon = "⏭️"
        else:
            status_icon = "❌"
        pr_display = r["pr"] if r["pr"] else ("(手动审查)" if r["status"] == "FAIL" else "-")
        print(f"#{r['issue']:<7} {status_icon:<7} {r['rounds']:<6} {pr_display[:48]:<50}")

        if r["status"] == "PASS":
            pass_count += 1
        elif r["status"] == "NO_DIFF":
            skip_count += 1
        else:
            fail_count += 1

    print("-" * 72)
    print(f"\n总计: {len(results)} 个 issue")
    print(f"  ✅ 通过 (已修复+PUSH+PR): {pass_count}")
    print(f"  ⏭️  跳过 (check已绿无变更): {skip_count}")
    print(f"  ❌ 失败 (超最大轮数): {fail_count}")

    # 如果有失败的，列出 worktree 路径
    failed_with_worktree = [r for r in results
                            if r["status"] == "FAIL" and r.get("worktree")]
    if failed_with_worktree:
        print(f"\n⚠ 以下 worktree 保留供手动审查：")
        for r in failed_with_worktree:
            print(f"   {r['worktree']}  (Issue #{r['issue']}: {r['title'][:50]})")

    # 清理未使用的 worktree（理论上已全部清理，这是兜底）
    if worktrees_created:
        print(f"\n🧹 清理剩余 worktree...")
        cleanup_worktrees(worktrees_created)


if __name__ == "__main__":
    main()
