#!/usr/bin/env python3
"""check-links.py —— 检查一个 Markdown 归档目录的内部链接与图片引用是否自洽。

三个维度：
  1. 缺失引用  —— md 里写的相对路径在磁盘上不存在
  2. 未引用资源 —— 资源目录里的文件没有任何 md 引用它
  3. 外链清单  —— 只统计，不联网校验（离线归档允许外链存在）

用法：
    python check-links.py <archive-dir> [--asset-dir assets] [--recursive] [--json]

默认只检查归档目录**顶层**的 .md——归档里通常还镜像了上游源码树（`reference-source/`），
那些第三方 README 里的相对链接指向上游仓库内部路径，在本地并不成立，不算缺失。
要连嵌套目录一起查，加 --recursive。

退出码：0 = 无缺失；1 = 有缺失引用；2 = 参数或目录错误。
"""

import argparse
import json
import os
import re
import sys
import urllib.parse

# 内联链接/图片：目标允许 () 内一层嵌套括号，以及 <...> 包裹的带空格路径
INLINE_PATTERN = re.compile(r"(!?)\[([^\]]*)\]\(((?:[^()]|\([^()]*\))*)\)", re.S)
FENCE_PATTERN = re.compile(r"```.*?```", re.S)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")

# 这些 scheme 不是本地文件，既不外链也不查缺失（避免把 data:/ftp: 误判为断链）
NON_LOCAL_SCHEMES = {"mailto", "data", "ftp", "ftps", "javascript", "tel", "ssh", "git"}
HTTP_SCHEMES = {"http", "https"}


# reference-style 定义：[1]: path "可选标题" —— 兼容脚注式与图片式引用
REF_DEF_PATTERN = re.compile(
    r"^\s{0,3}\[([^\]]+)\]:\s*<?([^\s>]+)>?(?:\s+\"[^\"]*\")?\s*$", re.M
)
REF_USE_PATTERN = re.compile(r"(!?)\[([^\]]*)\]\[([^\]]*)\]")


def collect_markdown(root, recursive=False):
    files = []
    if recursive:
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for name in names:
                if name.lower().endswith(".md"):
                    files.append(os.path.join(base, name))
    else:
        for name in os.listdir(root):
            full = os.path.join(root, name)
            if os.path.isfile(full) and name.lower().endswith(".md"):
                files.append(full)
    return sorted(files)


def clean_target(raw):
    """把链接目标规整成 (target, is_local)；解析 <...>、标题、查询串与 scheme。"""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        # 去掉可选的空格+标题：`path "title"`
        target = target.split(" ", 1)[0]
    if not target:
        return None, False
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme in HTTP_SCHEMES:
        return target, False
    if parsed.scheme in NON_LOCAL_SCHEMES:
        return None, False
    # 本地路径：去查询串与锚点，百分号解码（空格/中文路径常见）
    local = urllib.parse.unquote(parsed.path)
    if not local:
        return None, False
    return local, True


def scan(root, asset_dirs, recursive=False):
    missing = []
    external = []
    used = set()

    for path in collect_markdown(root, recursive):
        relative = os.path.relpath(path, root)
        with open(path, encoding="utf-8") as handle:
            text = FENCE_PATTERN.sub("", handle.read())
        text = INLINE_CODE_PATTERN.sub("", text)

        # 先收集本文件的 reference-style 定义（全文范围）
        definitions = {label.lower(): target for label, target in REF_DEF_PATTERN.findall(text)}

        candidates = []
        for match in INLINE_PATTERN.finditer(text):
            candidates.append(("IMG" if match.group(1) else "LNK", match.group(3)))

        for match in REF_USE_PATTERN.finditer(text):
            label = (match.group(3) or match.group(2)).strip().lower()
            if label in definitions:
                candidates.append(("IMG" if match.group(1) else "LNK", definitions[label]))

        for kind, raw in candidates:
            target, is_local = clean_target(raw)
            if target is None:
                continue
            if not is_local:
                external.append({"file": relative, "kind": kind, "target": target})
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            used.add(resolved)
            if not os.path.exists(resolved):
                missing.append({"file": relative, "kind": kind, "target": raw.strip()})

    unused = []
    for asset_dir in asset_dirs:
        absolute = os.path.join(root, asset_dir)
        if not os.path.isdir(absolute):
            continue
        for base, _dirs, names in os.walk(absolute):
            for name in names:
                full = os.path.normpath(os.path.join(base, name))
                if full not in used:
                    unused.append(os.path.relpath(full, root))
    unused.sort()
    return missing, external, unused


def main():
    parser = argparse.ArgumentParser(description="检查 Markdown 归档的内部链接与图片引用")
    parser.add_argument("archive_dir", help="归档目录（其下有若干 .md）")
    parser.add_argument("--asset-dir", action="append", default=None,
                        help="资源子目录名，可重复；默认 assets")
    parser.add_argument("--recursive", action="store_true",
                        help="连子目录一起查（默认只查顶层 .md）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args()

    if not os.path.isdir(args.archive_dir):
        print("archive dir not found: {}".format(args.archive_dir), file=sys.stderr)
        return 2
    asset_dirs = args.asset_dir if args.asset_dir else ["assets"]
    missing, external, unused = scan(args.archive_dir, asset_dirs, args.recursive)

    if args.json:
        print(json.dumps({
            "missing": missing,
            "external_count": len(external),
            "unused": unused,
        }, ensure_ascii=False, indent=2))
    else:
        print("markdown files: {}".format(len(collect_markdown(args.archive_dir, args.recursive))))
        print("MISSING local refs: {}".format(len(missing)))
        for item in missing:
            print("   {} {} -> {}".format(item["file"], item["kind"], item["target"]))
        print("unused assets: {}".format(len(unused)))
        for item in unused:
            print("   UNUSED {}".format(item))
        print("external links: {}".format(len(external)))

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
