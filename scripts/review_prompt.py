#!/usr/bin/env python3
"""按 PR 编号生成新上下文评审的派发物料（只用本地信息，纯标准库）。

用途：从本地 git 分支与 scripts/gates.json 解析出五项物料（PR 编号、分支名、
改动文件清单、门禁命令清单、结论三段模板），输出且只输出这五项；不读、不输出
PR 正文、issue 正文与 diff 内容，改动清单只取文件名。

失败即退出：分支不唯一、门禁清单缺失/损坏/缺字段、任一 git 命令失败时，向
stderr 打印明确错误并以状态 1 退出，stdout 不留下半截文案。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONCLUSION_TEMPLATE = (
    "结论：APPROVE / CHANGES-REQUESTED",
    "复核动作：<亲自跑了什么、读了哪些文件>",
    "证据：<门禁原始输出 / 文件行号 / 反例复现>",
)


def fail(message):
    print(f"错误：{message}", file=sys.stderr)
    sys.exit(1)


def run_git(repo, args, purpose):
    """跑一条 git 命令；返回码非 0 即明确报错退出，绝不产出半截文案。"""
    try:
        proc = subprocess.run(
            ["git", *args], capture_output=True, text=True, cwd=repo
        )
    except OSError as exc:
        fail(f"{purpose} 无法执行 git：{exc}")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        fail(f"{purpose} 失败（git {' '.join(args)}，退出码 {proc.returncode}）：{detail}")
    return proc.stdout


def ref_exists(repo, ref):
    """存在性探测：非零返回码只表示回退到 main，不是门禁命令失败。"""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            capture_output=True, text=True, cwd=repo,
        )
    except OSError:
        return False
    return proc.returncode == 0


def load_gate_data(repo):
    """从 scripts/gates.json 读出 (门禁命令清单, 基线引用名)，只取 required is True 的门禁。"""
    gates_path = repo / "scripts" / "gates.json"
    try:
        raw = gates_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"门禁清单缺失或不可读（{gates_path}）：{exc}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"门禁清单不是合法 JSON（{gates_path}）：{exc}")
    if not isinstance(data, dict) or not isinstance(data.get("gates"), list):
        fail(f"门禁清单缺 gates 数组（{gates_path}）")
    baseline = data.get("baseline")
    if not isinstance(baseline, str) or not baseline.strip():
        fail(f"门禁清单缺有效顶层 baseline（{gates_path}）")
    commands = []
    for index, gate in enumerate(data["gates"], 1):
        if not isinstance(gate, dict) or not all(k in gate for k in ("name", "cmd", "required")):
            fail(f"门禁清单第 {index} 条缺 name / cmd / required 字段（{gates_path}）")
        if gate["required"] is True:
            commands.append(str(gate["cmd"]))
    return commands, baseline


def main():
    parser = argparse.ArgumentParser(
        description="按 PR 编号生成评审派发物料（五项），只用本地 git 信息与 scripts/gates.json。"
    )
    parser.add_argument("pr", help="PR 编号（字符串即可，例如 378）")
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1],
        help="仓库根目录，默认为脚本上级目录",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    pr_number = args.pr.lstrip("#")
    if not pr_number:
        fail("PR 编号为空")
    if not (repo / ".git").exists():
        fail(f"不是 git 仓库根目录：{repo}")

    # 1) 分支：本地 refs/heads 里挑唯一含 /<编号>- 的分支。
    out = run_git(
        repo, ["for-each-ref", "--format=%(refname:short)", "refs/heads"], "枚举本地分支"
    )
    needle = f"/{pr_number}-"
    branches = [
        line.strip() for line in out.replace("\r\n", "\n").splitlines() if needle in line
    ]
    if len(branches) != 1:
        fail(
            f"PR #{pr_number} 的分支应唯一，实际匹配 {len(branches)} 个"
            f"（{', '.join(branches) or '无'}）"
        )
    branch = branches[0]

    # 2) 基线：优先 gates.json 顶层 baseline，引用不存在再依次回退 main、master。
    #    门禁命令与基线同源：均由 scripts/gates.json 派生，仓库换主干名时只改一处。
    commands, configured_baseline = load_gate_data(repo)
    baseline = None
    for candidate in (configured_baseline, "origin/main", "origin/master", "main", "master"):
        if candidate and ref_exists(repo, candidate):
            baseline = candidate
            break
    if baseline is None:
        fail(
            f"找不到基线引用（gates.json baseline={configured_baseline!r}，"
            f"已试 origin/main、origin/master、main、master；仓库：{repo}）"
        )

    merge_base = run_git(repo, ["merge-base", baseline, branch], "求合并基线").strip().splitlines()
    if not merge_base:
        fail(f"{baseline} 与 {branch} 求不出合并基线")
    base_sha = merge_base[0].strip()

    diff_out = run_git(
        repo, ["diff", "--name-only", f"{base_sha}...{branch}"], "列改动文件"
    )
    changed = [
        line.strip() for line in diff_out.replace("\r\n", "\n").splitlines() if line.strip()
    ]

    # 3) 门禁命令清单：清单缺失/损坏/缺字段时上面已失败退出。
    #    （commands 与 baseline 同源，已在步骤 2 一并从 gates.json 读出。）

    # 全部成功后一次性输出五项，失败路径不会走到这里。
    lines = [
        f"PR 编号：{pr_number}",
        f"分支名：{branch}",
        "改动文件清单：",
        *(changed or ["（无）"]),
        "门禁命令清单：",
        *(commands or ["（无）"]),
        "结论三段模板：",
        *CONCLUSION_TEMPLATE,
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
