#!/usr/bin/env python3
"""check-skills.py —— 按 skill-authoring 的条文检查本仓库技能。

用法：
    python skill-authoring/scripts/check-skills.py [--repo <仓库路径>]

检查项（括号内为条文编号，定义见 skill-authoring/references/standard.md）：
    M1  目录名 = frontmatter name，且只用小写英文与连字符
    M2  骨架构件齐全（触发加载检查块 / 定位段 / 完成后报告章）
    M3  frontmatter 六键齐全、顺序正确、无未列举键
    P1  frontmatter 不含 disable-model-invocation
    M5  references/version.md 存在；version 与其表首行一致；last_updated 同日期
    M6  章节编号全阿拉伯且连续；§ 引用可唯一解析；无 §N 式中文数字引用
    M7  正文引用的具体文件路径存在（目录式/省略式引用不检查）；「见 `X` 技能」的 X 存在
    P2  不出现中文数字章节号
    P7  references/ 无孤儿文件（每个文件在 SKILL.md 里有 pointer）
    D4/D5 README 技能表、版本、目录结构块、徽章数字与磁盘一致

只读脚本：不修改任何文件。退出码 0 = 全绿，1 = 有 FAIL。
"""

import argparse
import re
import sys
from pathlib import Path

FRONTMATTER_KEYS = ["name", "description", "agent_created", "version", "last_updated", "author"]
OPTIONAL_KEYS = {"license", "platforms", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CN_NUM_HEADING = re.compile(r"^#{2,3}\s*[一二三四五六七八九十]+[、.]")
SKILL_HOME = Path.home() / ".dsh" / "skills"

results = []  # (skill_or_scope, ok: bool, code: str, message: str)


def record(scope, ok, code, message):
    results.append((scope, ok, code, message))


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        return None if not path.exists() else ""
    except UnicodeDecodeError:
        return None


def parse_frontmatter(text):
    """返回 (键值字典, 键顺序列表, 正文, frontmatter 起始行号)。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [], text, 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, [], text, 0
    fm_lines = lines[1:end]
    order, values = [], {}
    for line in fm_lines:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$", line)
        if m:
            order.append(m.group(1))
            values[m.group(1)] = m.group(2).strip()
    body = "\n".join(lines[end + 1:])
    return values, order, body, end + 2


def headings(body):
    """返回 [(level, number, title, 行号)]，number 为 '3' 或 '3.1'，无编号则 None。"""
    out = []
    for i, line in enumerate(body.splitlines(), start=1):
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if not m:
            continue
        level, title = len(m.group(1)), m.group(2).strip()
        num = re.match(r"^(\d+(?:\.\d+)?)[.、]?\s", title)
        out.append((level, num.group(1) if num else None, title, i))
    return out


def chapter_body(body, number):
    """取第 number 章的正文（H2 标题行之后到下一个 H2 之前）。"""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = re.match(r"^##\s+(\d+)[.、]?\s", line)
        if m and m.group(1) == str(number):
            start = i + 1
            continue
        if start is not None and re.match(r"^##\s+", line):
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else None


def check_skill(repo, skill_dir):
    name = skill_dir.name
    text = read(skill_dir / "SKILL.md")
    if text is None:
        record(name, False, "M2", "SKILL.md 缺失或无法读取")
        return
    values, order, body, _ = parse_frontmatter(text)

    # M1 目录名 = name
    fm_name = values.get("name", "").strip().strip('"').strip("'")
    if fm_name != name:
        record(name, False, "M1", f"frontmatter name={fm_name!r} 与目录名 {name!r} 不一致")
    elif not NAME_RE.match(name):
        record(name, False, "M1", f"目录名 {name!r} 不符合小写英文+连字符")
    else:
        record(name, True, "M1", f"目录名 = name = {name}")

    # M3 六键齐全、顺序正确、无未列举键
    problems = []
    missing = [k for k in FRONTMATTER_KEYS if k not in values]
    if missing:
        problems.append("缺键 " + "、".join(missing))
    unknown = [k for k in order if k not in FRONTMATTER_KEYS and k not in OPTIONAL_KEYS]
    if unknown:
        problems.append("未列举键 " + "、".join(unknown))
    listed = [k for k in order if k in FRONTMATTER_KEYS]
    if listed != [k for k in FRONTMATTER_KEYS if k in values]:
        problems.append(f"键顺序为 {listed}，应为 {FRONTMATTER_KEYS[:len(listed)]}")
    if problems:
        record(name, False, "M3", "；".join(problems))
    else:
        record(name, True, "M3", "frontmatter 六键齐全、顺序正确")

    # P1 disable-model-invocation
    if "disable-model-invocation" in values:
        record(name, False, "P1", f"出现了 disable-model-invocation: {values['disable-model-invocation']}（应整个键省略）")
    else:
        record(name, True, "P1", "未出现 disable-model-invocation")

    # M2 骨架构件
    if "触发加载检查" not in body:
        record(name, False, "M2", "缺少触发加载检查块")
    elif not re.search(r"^定位：", body, re.M):
        record(name, False, "M2", "缺少以「定位：」开头的定位段")
    elif not re.search(r"^##\s+\d+[.、]\s*完成后报告", body, re.M):
        record(name, False, "M2", "缺少「完成后报告」章或未被编号")
    else:
        record(name, True, "M2", "骨架三要素齐全（加载检查块 / 定位段 / 完成后报告）")

    # M5 version.md
    ver = values.get("version", "").strip().strip('"').strip("'")
    stamp = values.get("last_updated", "").strip().strip('"').strip("'")
    vfile = skill_dir / "references" / "version.md"
    if not vfile.exists():
        record(name, False, "M5", "缺少 references/version.md")
    else:
        vtext = read(vfile) or ""
        first_row = None
        for line in vtext.splitlines():
            if line.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line.strip()):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells and re.match(r"^\d+\.\d+", cells[0]):
                    first_row = cells
                    break
        if first_row is None:
            record(name, False, "M5", "version.md 里找不到版本行")
        else:
            v_ver, v_date = first_row[0], (first_row[1] if len(first_row) > 1 else "")
            bad = []
            if v_ver != ver:
                bad.append(f"表首行版本 {v_ver} ≠ frontmatter {ver}")
            if stamp and v_date != stamp:
                bad.append(f"表首行日期 {v_date} ≠ last_updated {stamp}")
            if bad:
                record(name, False, "M5", "；".join(bad))
            else:
                record(name, True, "M5", f"version {ver} @ {stamp} 与 version.md 一致")

    # P2 / M6 章节编号
    hs = headings(body)
    cn = [h for h in hs if CN_NUM_HEADING.match("#" * h[0] + " " + h[2])]
    if cn:
        record(name, False, "P2", "中文数字章节号：" + "、".join(h[2] for h in cn))
    else:
        record(name, True, "P2", "无中文数字章节号")

    h2 = [h for h in hs if h[0] == 2]
    h3 = [h for h in hs if h[0] == 3]
    seq = []
    for i, h in enumerate(h2, start=1):
        seq.append((h[1], str(i), h[2]))
    bad_seq = [f"{got or '无编号'} 应为 {want}（{title}）" for got, want, title in seq if got != want]
    if bad_seq:
        record(name, False, "M6", "H2 编号不连续：" + "；".join(bad_seq))
    else:
        record(name, True, "M6", f"H2 编号 1–{len(h2)} 连续")

    h3_bad = []
    per_chapter = {}
    for level, num, title, _ in h3:
        chapter = num.split(".")[0] if num and "." in num else None
        if chapter is None:
            h3_bad.append(f"H3 无 N.M 编号（{title}）")
            continue
        per_chapter.setdefault(chapter, []).append(int(num.split(".")[1]))
    for chapter, nums in per_chapter.items():
        if nums != list(range(1, len(nums) + 1)):
            h3_bad.append(f"第 {chapter} 章 H3 编号为 {nums}")
    if h3_bad:
        record(name, False, "M6", "H3 编号问题：" + "；".join(h3_bad))
    elif h3:
        record(name, True, "M6", f"H3 编号逐章连续（共 {len(h3)} 个）")

    # M6/M7 § 引用可解析
    scan = re.sub(r"§(\d+)\.(\d+)\s*[–—-]\s*(\d+)", r"§\1.\2 §\1.\3", body)
    refs = re.findall(r"§(\d+)(?:\.(\d+))?", scan)
    unresolved = []
    for chapter, item in refs:
        if chapter_body(body, chapter) is None:
            unresolved.append(f"§{chapter}" + (f".{item}" if item else "") + "（无此章）")
            continue
        if not item:
            continue
        if any(h[1] == f"{chapter}.{item}" for h in h3):
            continue
        cbody = chapter_body(body, chapter) or ""
        items = {int(m.group(1)) for m in re.finditer(r"^\s*(\d+)\.\s+\S", cbody, re.M)}
        if int(item) not in items:
            unresolved.append(f"§{chapter}.{item}（既无此 H3，也无此列表项）")
    if unresolved:
        record(name, False, "M7", "§ 引用无法解析：" + "、".join(sorted(set(unresolved))))
    else:
        record(name, True, "M7", f"§ 引用全部可解析（{len(refs)} 处）")

    # M7 路径引用
    paths = set(re.findall(r"`(references/[^`]+?)`", body)) | set(re.findall(r"\((references/[^)]+?)\)", body))
    paths |= set(re.findall(r"`(docs/adr/[^`]+?)`", body))
    bad_paths = []
    checked = 0
    for p in paths:
        clean = p.split("#")[0].strip()
        last = clean.rstrip("/").split("/")[-1]
        # 目录式（`references/`、`docs/adr/`）与省略式（`references/…`）是版面约定，不检查存在性
        if clean.endswith("/") or "…" in last or "." not in last:
            continue
        checked += 1
        if not (skill_dir / clean).exists():
            bad_paths.append(p)
    if bad_paths:
        record(name, False, "M7", "路径不存在：" + "、".join(sorted(bad_paths)))
    else:
        record(name, True, "M7", f"正文引用的 {checked} 个具体文件路径都存在")

    # M7 技能引用
    skill_refs = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`\s*技能", body))
    skill_refs |= {t for t in re.findall(r"(?:见|交给|调用|复用)\s*`([a-z0-9][a-z0-9-]*)`", body) if "/" not in t and "." not in t}
    missing_skills = [
        s for s in sorted(skill_refs)
        if not (repo / s / "SKILL.md").exists() and not (SKILL_HOME / s / "SKILL.md").exists()
    ]
    if missing_skills:
        record(name, False, "M7", "引用的技能不存在：" + "、".join(missing_skills))
    elif skill_refs:
        record(name, True, "M7", f"引用的 {len(skill_refs)} 个技能都存在")

    # P7 references/ 孤儿文件
    refdir = skill_dir / "references"
    orphans = []
    if refdir.is_dir():
        for f in sorted(refdir.rglob("*")):
            if f.is_dir() or f.name.startswith("."):
                continue
            rel = f.relative_to(skill_dir).as_posix()
            short = f.relative_to(refdir).as_posix()
            if rel not in body and short not in body:
                orphans.append(rel)
    if orphans:
        record(name, False, "P7", "孤儿文件（正文无 pointer）：" + "、".join(orphans))
    elif refdir.is_dir():
        record(name, True, "P7", "references/ 无孤儿文件")


def check_readme(repo, skill_names):
    readme = repo / "README.md"
    if not readme.exists():
        record("README", False, "D5", "README.md 不存在")
        return
    text = read(readme) or ""

    linked = set(re.findall(r"\]\(\./([a-z0-9-]+)/\)", text))
    table = set(re.findall(r"^\|\s*\[`([a-z0-9-]+)`\]", text, re.M))
    missing_rows = sorted(set(skill_names) - table)
    extra_rows = sorted(table - set(skill_names))
    if missing_rows or extra_rows:
        msg = []
        if missing_rows:
            msg.append("技能表缺行：" + "、".join(missing_rows))
        if extra_rows:
            msg.append("技能表多行：" + "、".join(extra_rows))
        record("README", False, "D5", "；".join(msg))
    else:
        record("README", True, "D5", f"技能表 {len(table)} 行与磁盘技能一一对应")

    # 版本一致性
    bad_ver = []
    for m in re.finditer(r"^\|\s*\[`([a-z0-9-]+)`\]\(\./[^)]*\)\s*\|\s*([^|]+?)\s*\|", text, re.M):
        sname, rver = m.group(1), m.group(2)
        f = repo / sname / "SKILL.md"
        if not f.exists():
            continue
        vals, _, _, _ = parse_frontmatter(read(f) or "")
        if vals.get("version", "").strip() != rver:
            bad_ver.append(f"{sname}: README {rver} ≠ frontmatter {vals.get('version', '?')}")
    if bad_ver:
        record("README", False, "D4", "版本不一致：" + "；".join(bad_ver))
    else:
        record("README", True, "D4", "技能表版本与 frontmatter 一致")

    # 徽章数字
    badge = re.search(r"badge/skills-(\d+)-", text)
    if not badge:
        record("README", False, "D5", "找不到 skills-N 徽章")
    elif int(badge.group(1)) != len(skill_names):
        record("README", False, "D5", f"徽章 skills-{badge.group(1)} ≠ 实际 {len(skill_names)} 个技能")
    else:
        record("README", True, "D5", f"徽章 skills-{badge.group(1)} 与实际技能数一致")

    # 目录结构块
    missing_tree = sorted(s for s in skill_names if s not in text.split("## 目录结构")[-1].split("```")[1] if len(text.split("## 目录结构")) > 1 and len(text.split("## 目录结构")[-1].split("```")) > 1)
    if missing_tree:
        record("README", False, "D5", "目录结构块缺技能：" + "、".join(missing_tree))
    else:
        record("README", True, "D5", "目录结构块覆盖全部技能")

    unused_links = sorted(linked - set(skill_names))
    if unused_links:
        record("README", False, "M7", "README 链接指向不存在的目录：" + "、".join(unused_links))


def main():
    ap = argparse.ArgumentParser(description="按 skill-authoring 的条文检查本仓库技能")
    ap.add_argument("--repo", default=None, help="仓库根目录（默认取本脚本向上两级）")
    args = ap.parse_args()
    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parents[2]
    if not (repo / "README.md").exists():
        print(f"× 找不到仓库根目录：{repo}")
        return 2

    skill_dirs = sorted(d for d in repo.iterdir() if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists())
    stray = sorted(d.name for d in repo.iterdir() if d.is_dir() and not d.name.startswith(".") and not (d / "SKILL.md").exists())

    print(f"# check-skills.py —— {repo}")
    print(f"# 检查 {len(skill_dirs)} 个技能：{', '.join(d.name for d in skill_dirs)}")
    if stray:
        print(f"# 注意：以下目录不含 SKILL.md，已跳过 —— {', '.join(stray)}")
    print()

    for d in skill_dirs:
        check_skill(repo, d)
    check_readme(repo, [d.name for d in skill_dirs])

    failures = 0
    scope_now = None
    for scope, ok, code, message in results:
        if scope != scope_now:
            print(f"## {scope}")
            scope_now = scope
        mark = "OK  " if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  [{mark}] {code:4s} {message}")

    print()
    if failures:
        print(f"× {failures} 项 FAIL —— 修好再继续（条文定义见 skill-authoring/references/standard.md）")
        return 1
    print(f"√ 全部通过（{len(results)} 项检查）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
