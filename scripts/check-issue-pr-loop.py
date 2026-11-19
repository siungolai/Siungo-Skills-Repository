#!/usr/bin/env python3
"""项目级语义一致性门禁与主干提交对账（纯标准库、只读、无网络、不写文件）。

默认模式：逐项校验 scripts/gates.json 结构、八个落点文件、各文档的 REQUIRED
口径短语、限定文件集内的 BANNED 旧错句、动作授权前提（新前提在、旧前提不在）、
pr-contract.md §8 代码块、版本三方一致与 C13 回退句；失败逐条打印
FAIL <说明> 并 exit 1，全过打印通过行并 exit 0。
--reconcile：以 gates.json 的 reconcile.baseline 为起点，对账顶层 baseline 指向的主干，
筛出标题不以 (#<数字>) 结尾的孤儿提交；基线不存在或 git 失败即报错退出。
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES_JSON = "scripts/gates.json"
HOOK = "scripts/deny-main-push.sh"
PR_CONTRACT = "issue-pr-loop/references/pr-contract.md"
C13 = "跨技能读盘回退：优先"

LANDING_FILES = (
    "CONTRIBUTING.md",
    "ISSUE_GUIDE.md",
    "PR_GUIDE.md",
    "REVIEW_DISPATCH.md",
    "scripts/gates.json",
    "scripts/review_prompt.py",
    "scripts/deny-main-push.sh",
    "scripts/check-issue-pr-loop.py",
)

# 普通子串包含判断（needle in text）：不做正则、不 strip 反引号。
REQUIRED = {
    "issue-pr-loop/SKILL.md": (
        "feat / fix / refactor / docs / test / chore",
        "同文件永不同层",
        "四个时点",
        "可复制粘贴的命令、执行人、原始输出",
        "PR 编号、分支名、改动文件清单、门禁命令清单、结论三段模板",
        "四个数字",
        "纯文档与纯重构",
        "五样",
        "四个文档 + 一个门禁清单 + 三个脚本",
        "合并前后逐项过这张检查表",
        "基线之后",
        "跨技能读盘回退：优先",
        "默认代用户执行",
        "并行度自主裁量",
        "禁止绕过 PR",
    ),
    "issue-pr-loop/CONTEXT.md": (
        "五样东西",
        "纯文档与纯重构",
        "同文件永不同层",
        "合并后立刻",
        "免审通道",
    ),
    "issue-pr-loop/references/pr-contract.md": (
        "feat / fix / refactor / docs / test / chore",
        "纯文档与纯重构",
        "可复制粘贴的命令、执行人、原始输出",
        "基线之后",
        "scripts/gates.json",
    ),
    "issue-pr-loop/references/flow.md": (
        "feat / fix / refactor / docs / test / chore",
        "同文件永不同层",
        "并行度自主裁量",
        "scripts/check-issue-pr-loop.py",
        "scripts/review_prompt.py",
    ),
    "issue-pr-loop/references/ledger-and-gates.md": (
        "四个数字",
        "needs-merge",
        "基线之后",
        "跨技能读盘回退：优先",
    ),
    "issue-pr-loop/references/case-book.md": (
        "六种",
        "纯文档与纯重构",
        "references/flow.md",
        "publish-check",
    ),
    "issue-pr-loop/references/version.md": (
        "更正",
    ),
    "README.md": (
        "纯文档与纯重构",
        "scripts/gates.json",
        "CONTRIBUTING.md",
    ),
    "CONTRIBUTING.md": (
        "存量对账基线",
    ),
    "PR_GUIDE.md": (
        "feat / fix / refactor / docs / test / chore",
        "四个时点",
    ),
}

BANNED_PLAIN = (
    "同一文件不同层是违约",
    "三个时点",
    "三个数字",
    "纯文档是唯一例外",
    "免审只有一种",
    "在 issue 里留下可复制的命令与执行人",
    "在 issue 里留命令与执行人",
    "§5 摸依赖分层",
    "`SKILL.md` §5 的分层规则",
    "不替用户开 PR、合并、推送",
    "须用户明确授权",
    "授权一次只覆盖一轮",
    "这三件都是不可逆动作",
)

BANNED_REGEX = (
    r"feat / fix / refactor / docs / test(?! / chore)",
    r"PR 编号、分支名、改动文件清单、门禁命令(?!清单)",
    r"`Closes` 只给纯文档(?!与纯重构)",
)

BANNED_ROOT_MD = (
    "CONTRIBUTING.md",
    "ISSUE_GUIDE.md",
    "PR_GUIDE.md",
    "REVIEW_DISPATCH.md",
    "README.md",
)


class Checker:
    """收集逐项检查结果与失败说明，统计实际检查项数。"""

    def __init__(self):
        self.count = 0
        self.fails = []

    def check(self, condition, message):
        self.count += 1
        if not condition:
            self.fails.append(message)

    def fail(self, message):
        self.check(False, message)


def read_text(rel, checker):
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        checker.fail(f"{rel} 不可读：{exc}")
        return None


def load_gates(checker):
    raw = read_text(GATES_JSON, checker)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        checker.fail(f"{GATES_JSON} 不是合法 JSON：{exc}")
        return None


def check_gates_structure(checker, data):
    checker.check(isinstance(data, dict), f"{GATES_JSON} 顶层必须是对象")
    if not isinstance(data, dict):
        return
    top_baseline = data.get("baseline")
    checker.check(
        isinstance(top_baseline, str) and bool(top_baseline.strip()),
        f"{GATES_JSON} 顶层 baseline 必须是非空引用名（如 origin/main）",
    )
    gates = data.get("gates")
    checker.check(isinstance(gates, list), f"{GATES_JSON} 缺 gates 数组")
    if isinstance(gates, list):
        for index, gate in enumerate(gates, 1):
            valid = (
                isinstance(gate, dict)
                and all(key in gate for key in ("name", "cmd", "required"))
            )
            checker.check(valid, f"{GATES_JSON} gates 第 {index} 条缺 name / cmd / required")
            if not valid:
                continue
            # required 必须是 bool（字符串 "false" 会被真值判断误纳），cmd 必须是字符串
            checker.check(
                isinstance(gate["required"], bool),
                f"{GATES_JSON} gates 第 {index} 条 required 必须是布尔值",
            )
            checker.check(
                isinstance(gate["cmd"], str) and bool(gate["cmd"].strip()),
                f"{GATES_JSON} gates 第 {index} 条 cmd 必须是非空字符串",
            )
    # 分支保护名单单一事实源：gates.json(pr.protect) 必须与钩子、SKILL.md、CONTRIBUTING.md 一致
    protect = data.get("pr", {}).get("protect") if isinstance(data.get("pr"), dict) else None
    checker.check(
        isinstance(protect, list) and bool(protect) and all(isinstance(b, str) for b in protect),
        f"{GATES_JSON} pr.protect 必须是非空字符串数组",
    )
    if isinstance(protect, list):
        def safe_text(rel):
            try:
                return (ROOT / rel).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return None

        hook_text = safe_text(HOOK)
        # 只解析 case "$remote_ref" in ... esac 内的模式：注释里的 refs/heads/... 不算保护。
        case_text = ""
        if hook_text is not None:
            case_match = re.search(
                r'case\s+["\']?\$remote_ref["\']?\s+in\b(.*?)\besac\b',
                hook_text,
                re.DOTALL,
            )
            if case_match:
                case_text = re.sub(r"#[^\n]*", "", case_match.group(1))
        protected_refs = set(re.findall(r"refs/heads/[A-Za-z0-9._/-]+", case_text))
        checker.check(
            bool(protected_refs),
            f"钩子 {HOOK} 未解析到 case 中的 refs/heads/... 受保护分支",
        )
        for branch in protect:
            checker.check(
                f"refs/heads/{branch}" in protected_refs,
                f"钩子 {HOOK} case 模式缺 pr.protect 中的分支 {branch}",
            )
        for rel in ("issue-pr-loop/SKILL.md", "CONTRIBUTING.md"):
            text = safe_text(rel)
            checker.check(
                text is not None and all(branch in text for branch in protect),
                f"{rel} 未列全 pr.protect 的分支 {protect}",
            )
    reconcile = data.get("reconcile")
    baseline = reconcile.get("baseline") if isinstance(reconcile, dict) else None
    checker.check(
        isinstance(baseline, str) and re.fullmatch(r"[0-9a-fA-F]{40}", baseline) is not None,
        f"{GATES_JSON} reconcile.baseline 必须是 40 位十六进制 sha",
    )


def check_landing_files(checker):
    for rel in LANDING_FILES:
        checker.check((ROOT / rel).is_file(), f"缺少落点文件 {rel}")


def check_required(checker):
    for rel, needles in REQUIRED.items():
        text = read_text(rel, checker)
        if text is None:
            continue
        for needle in needles:
            checker.check(needle in text, f"{rel} 缺少口径短语 {needle}")


def banned_md_files():
    """只扫 issue-pr-loop/**/*.md、四份根 .md 与 README.md，绝不扫 .py/.json/.sh。"""
    files = []
    skill_dir = ROOT / "issue-pr-loop"
    if skill_dir.is_dir():
        files.extend(sorted(p for p in skill_dir.rglob("*.md") if p.is_file()))
    files.extend(ROOT / rel for rel in BANNED_ROOT_MD)
    unique = []
    seen = set()
    for path in files:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def check_banned(checker):
    for path in banned_md_files():
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            continue  # 缺文件由落点检查负责，避免重复报错
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            checker.fail(f"BANNED 扫描无法读取 {rel}：{exc}")
            continue
        for needle in BANNED_PLAIN:
            checker.check(needle not in text, f"{rel} 含 BANNED 旧错句 {needle}")
        for pattern in BANNED_REGEX:
            checker.check(
                re.search(pattern, text) is None,
                f"{rel} 命中 BANNED 正则 {pattern}",
            )


def shebang_block(text):
    """取第一个内容行以 #!/bin/sh 开头的 ``` 围栏代码块内部各行。"""
    lines = text.replace("\r\n", "\n").splitlines()
    body = None
    in_block = False
    for line in lines:
        if not in_block:
            if line.lstrip().startswith("```"):
                in_block = True
                body = []
            continue
        if line.lstrip().startswith("```"):
            if body and body[0].startswith("#!/bin/sh"):
                return body
            in_block = False
            body = []
            continue
        body.append(line)
    return None


def check_hook_block(checker):
    contract = read_text(PR_CONTRACT, checker)
    hook = read_text(HOOK, checker)
    if contract is None or hook is None:
        return
    block = shebang_block(contract)
    checker.check(
        block is not None,
        f"{PR_CONTRACT} 找不到首个以 #!/bin/sh 开头的围栏代码块",
    )
    if block is None:
        return
    hook_lines = hook.replace("\r\n", "\n").splitlines()
    checker.check(
        len(block) == len(hook_lines),
        f"{PR_CONTRACT} §8 代码块 {len(block)} 行与 {HOOK} {len(hook_lines)} 行不一致",
    )
    for index in range(max(len(block), len(hook_lines))):
        left = block[index] if index < len(block) else "<缺行>"
        right = hook_lines[index] if index < len(hook_lines) else "<缺行>"
        checker.check(
            left == right,
            f"{PR_CONTRACT} §8 代码块第 {index + 1} 行与 {HOOK} 不一致："
            f"文档 {left!r} / 脚本 {right!r}",
        )


def frontmatter(text):
    lines = text.replace("\r\n", "\n").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}
    fields = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(\S+)\s*$", line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def first_version_row(text):
    """M5 逻辑：表首个 | 开头且首格匹配 ^\\d+\\.\\d+ 的行。"""
    for line in text.replace("\r\n", "\n").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and re.match(r"^\d+\.\d+", cells[0]):
            return cells
    return None


def readme_skill_version(text, skill="issue-pr-loop"):
    for line in text.replace("\r\n", "\n").splitlines():
        if not line.startswith("|") or skill not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"\d+\.\d+(?:\.\d+)?", cells[1]):
            return cells[1]
    return None


def check_versions(checker):
    skill = read_text("issue-pr-loop/SKILL.md", checker)
    version_md = read_text("issue-pr-loop/references/version.md", checker)
    readme = read_text("README.md", checker)
    if skill is None or version_md is None or readme is None:
        return
    fields = frontmatter(skill)
    # 单一事实源：SKILL.md frontmatter 的 version/last_updated，其余两面须与它一致
    skill_version = fields.get("version")
    skill_date = fields.get("last_updated")
    checker.check(
        isinstance(skill_version, str) and re.fullmatch(r"\d+\.\d+\.\d+", skill_version) is not None,
        f"SKILL.md frontmatter version 必须是三段式版本（实际 {skill_version!r}）",
    )
    checker.check(
        isinstance(skill_date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", skill_date) is not None,
        f"SKILL.md frontmatter last_updated 必须是 YYYY-MM-DD（实际 {skill_date!r}）",
    )
    row = first_version_row(version_md)
    checker.check(row is not None, "references/version.md 找不到表首数据行")
    if row and skill_version:
        checker.check(
            row[0] == skill_version,
            f"references/version.md 表首版本 {row[0]} ≠ SKILL.md version {skill_version}",
        )
        checker.check(
            len(row) > 1 and row[1] == skill_date,
            f"references/version.md 表首日期 {row[1] if len(row) > 1 else None} ≠ SKILL.md last_updated {skill_date}",
        )
    readme_version = readme_skill_version(readme)
    checker.check(
        readme_version == skill_version,
        f"README.md 技能表 issue-pr-loop 行版本 {readme_version} ≠ SKILL.md version {skill_version}",
    )
    checker.check(
        skill_version == (row[0] if row else None) == readme_version,
        "SKILL.md / references/version.md / README.md 三方版本不一致",
    )


def check_readme_authoring_version(checker):
    """README 技能表里 skill-authoring 的版本须从其 SKILL.md frontmatter 派生，不写死。"""
    skill = read_text("skill-authoring/SKILL.md", checker)
    readme = read_text("README.md", checker)
    if skill is None or readme is None:
        return
    skill_version = frontmatter(skill).get("version")
    checker.check(
        isinstance(skill_version, str) and re.fullmatch(r"\d+\.\d+\.\d+", skill_version) is not None,
        f"skill-authoring/SKILL.md frontmatter version 必须是三段式（实际 {skill_version!r}）",
    )
    readme_version = readme_skill_version(readme, "skill-authoring")
    checker.check(
        readme_version == skill_version,
        f"README.md 技能表 skill-authoring 行版本 {readme_version} ≠ SKILL.md version {skill_version}",
    )


def check_c13(checker):
    for rel in ("issue-pr-loop/SKILL.md", "issue-pr-loop/references/ledger-and-gates.md"):
        text = read_text(rel, checker)
        if text is None:
            continue
        checker.check(C13 in text, f"{rel} 缺 C13 回退句前缀 {C13}")


def check_authorization_premise(checker):
    """动作授权前提：新前提逐文件落盘，旧前提由 BANNED 清零，护栏仍在；版本号不硬编码。"""
    landing = (
        "issue-pr-loop/SKILL.md",
        "README.md",
        "CONTRIBUTING.md",
        "PR_GUIDE.md",
    )
    for rel in landing:
        text = read_text(rel, checker)
        if text is None:
            continue
        checker.check("代用户执行" in text, f"{rel} 缺动作授权前提短语「代用户执行」")
    skill = read_text("issue-pr-loop/SKILL.md", checker)
    if skill is None:
        return
    skill_version = frontmatter(skill).get("version", "")
    checker.check(
        f"**动作授权前提（v{skill_version}）**" in skill,
        f"SKILL.md 动作授权前提段版本号应与 frontmatter 一致（v{skill_version}）",
    )
    checker.check(
        "1. **可替用户开 PR、合并、推送功能分支**" in skill,
        "SKILL.md §14 第 1 条未反转动作授权前提",
    )
    for guard in ("禁止直推主干", "禁止绕过 PR", "禁止 force push 主干"):
        checker.check(guard in skill, f"SKILL.md 动作授权前提缺护栏 {guard}")


def run_consistency():
    checker = Checker()
    data = load_gates(checker)
    check_gates_structure(checker, data)
    check_landing_files(checker)
    check_required(checker)
    check_banned(checker)
    check_hook_block(checker)
    check_versions(checker)
    check_readme_authoring_version(checker)
    check_c13(checker)
    check_authorization_premise(checker)
    if checker.fails:
        for message in checker.fails:
            print(f"FAIL {message}")
        return 1
    print(f"√ issue-pr-loop 语义一致性通过（{checker.count} 项检查）")
    return 0


def run_reconcile():
    try:
        config = json.loads((ROOT / GATES_JSON).read_text(encoding="utf-8"))
        baseline = config["reconcile"]["baseline"]
        # 主干引用从顶层 baseline 配置派生（换 main/master/slim 只改一处）
        main_ref = config.get("baseline", "origin/main")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"错误：无法读取 {GATES_JSON} 的 baseline 配置：{exc}", file=sys.stderr)
        return 1
    if not isinstance(baseline, str) or re.fullmatch(r"[0-9a-fA-F]{40}", baseline) is None:
        print(f"错误：reconcile.baseline 不是 40 位十六进制 sha：{baseline!r}", file=sys.stderr)
        return 1

    def git(args):
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True
        )

    try:
        probe = git(["rev-parse", "--verify", "--quiet", f"{baseline}^{{commit}}"])
        if probe.returncode != 0:
            print(f"错误：基线不存在：{baseline}", file=sys.stderr)
            return 1
        log = git(["log", "--first-parent", "--format=%h %s", f"{baseline}..{main_ref}"])
    except OSError as exc:
        print(f"错误：无法执行 git：{exc}", file=sys.stderr)
        return 1
    if log.returncode != 0:
        detail = (log.stderr or log.stdout or "").strip()
        print(f"错误：git log 失败（退出码 {log.returncode}）：{detail}", file=sys.stderr)
        return 1
    orphans = [
        line
        for line in log.stdout.replace("\r\n", "\n").splitlines()
        if line.strip() and re.search(r"\(#\d+\)\s*$", line) is None
    ]
    if orphans:
        for line in orphans:
            print(f"孤儿提交：{line}")
        return 1
    print("√ 基线之后无孤儿提交")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="项目级语义一致性门禁（默认）与基线之后孤儿提交对账（--reconcile）。"
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="以 scripts/gates.json 的 reconcile.baseline 为起点，对账顶层 baseline 指向的主干",
    )
    args = parser.parse_args()
    if args.reconcile:
        sys.exit(run_reconcile())
    sys.exit(run_consistency())


if __name__ == "__main__":
    main()
