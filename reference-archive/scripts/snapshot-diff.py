#!/usr/bin/env python3
"""snapshot-diff.py —— 把两个目录树做逐文件 sha1 对账，回答「上游到底改了什么」。

归档快照与上游增量对账的核心工具。回答四个问题：
  1. 上游有、本地没有 —— 官方新增了什么
  2. 本地有、上游没有 —— 官方删除了什么
  3. 两边都有但内容不同 —— 官方改了什么
  4. 两边都有且内容相同 —— 确认无变化（这一步最费时，但能挡掉「疑似大改」的误判）

「官方把目录改名但代码一个字节没动」这种假大改，只有逐文件 sha1 比对才能识破。

用法：
    python snapshot-diff.py --upstream <上游目录> --local <本地快照目录> [--json out.json]

退出码：0 = 比对完成；1 = 参数错误。
"""

import argparse
import hashlib
import json
import os
import sys

CHUNK = 1 << 20


def sha1_of(path):
    digest = hashlib.sha1()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def index_tree(root, skip_dirs=(".git", "__pycache__", "node_modules")):
    """返回 {相对路径: (大小, sha1)}。"""
    index = {}
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in names:
            full = os.path.join(base, name)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            index[relative] = (os.path.getsize(full), sha1_of(full))
    return index


def compare(upstream, local):
    up = index_tree(upstream)
    lo = index_tree(local)
    added = sorted(set(up) - set(lo))
    removed = sorted(set(lo) - set(up))
    changed = sorted(r for r in (set(up) & set(lo)) if up[r][1] != lo[r][1])
    identical = len(set(up) & set(lo)) - len(changed)
    return {
        "upstream_files": len(up),
        "local_files": len(lo),
        "identical": identical,
        "added": added,
        "removed": removed,
        "changed": changed,
        "local_bytes": sum(size for size, _ in lo.values()),
    }


def render(result, upstream, local, limit=25):
    print("upstream: {}".format(upstream))
    print("local:    {}".format(local))
    print("upstream files: {}   local files: {}".format(result["upstream_files"], result["local_files"]))
    print("identical (sha1 match): {}".format(result["identical"]))
    print("ADDED   (upstream only): {}".format(len(result["added"])))
    for item in result["added"][:limit]:
        print("   + {}".format(item))
    print("REMOVED (local only):    {}".format(len(result["removed"])))
    for item in result["removed"][:limit]:
        print("   - {}".format(item))
    print("CHANGED (sha1 differs):  {}".format(len(result["changed"])))
    for item in result["changed"][:limit]:
        print("   ~ {}".format(item))
    if len(result["added"]) > limit or len(result["removed"]) > limit or len(result["changed"]) > limit:
        print("   ... (truncated at {} per category)".format(limit))


def main():
    parser = argparse.ArgumentParser(description="目录树逐文件 sha1 对账")
    parser.add_argument("--upstream", required=True, help="上游目录（新拉的快照）")
    parser.add_argument("--local", required=True, help="本地归档快照目录")
    parser.add_argument("--json", default=None, help="把完整结果写到这个 JSON 文件")
    args = parser.parse_args()

    for path in (args.upstream, args.local):
        if not os.path.isdir(path):
            print("not a directory: {}".format(path), file=sys.stderr)
            return 1

    result = compare(args.upstream, args.local)
    render(result, args.upstream, args.local)

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        print("full result -> {}".format(args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
