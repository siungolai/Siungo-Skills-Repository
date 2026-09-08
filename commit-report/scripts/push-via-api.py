#!/usr/bin/env python3
"""通用降级推送脚本：git push 直连不可达但 api.github.com 可达时，用 gh api git data API 推送。

用法：
    python3 push-via-api.py [分支名]

行为：
    1. 解析当前仓库 remote origin 的 owner/repo（无 origin 时用参数或报错）；
    2. 计算待推送提交链（@{u}..HEAD；无上游时推送 HEAD 全链需谨慎，默认拒绝并提示）；
    3. 对每个提交：上传变更 blob → 重建全量 tree → 原样重建 commit（author/committer/message
       逐字段一致，保证 SHA 与本地完全相同）→ 依次作为父链；
    4. PATCH 远端 ref（force=false，快进校验）；
    5. 成功后将本地 remote-tracking ref 同步到新 sha（git 直连不通时 fetch 会失败，需手动同步）。

前置条件：
    - gh CLI 已安装并登录（gh auth status；token 需含 repo 权限）
    - 本脚本只改变传输通道，不改变提交内容与范围 —— 须先经 commit-report 审阅门确认

已知陷阱（对应 SKILL.md §五.3）：
    - 中文/空格路径：git 输出统一用 -z（NUL 分隔）读取
    - blob content 用 base64 编码上传
    - author/committer date 用 ISO 8601（git log %aI/%cI），epoch 格式会被 API 拒绝
    - gh api 布尔字段用 -F（-f 会把 false 变字符串导致 422）
"""

import base64
import json
import subprocess
import sys

BRANCH = sys.argv[1] if len(sys.argv) > 1 else "main"
UPSTREAM_REF = "@{u}"  # 不经 f-string 拼接，避免花括号被求值


def git(args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def gh(method, path, data=None):
    cmd = ["gh", "api", "--method", method, path]
    if data is not None:
        cmd += ["--input", "-"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(data) if data is not None else None,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {method} {path} 失败: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def parse_remote():
    url = git(["remote", "get-url", "origin"]).strip()
    if url.startswith("https://github.com/"):
        return url.removeprefix("https://github.com/").removesuffix(".git")
    if url.startswith("git@github.com:"):
        return url.removeprefix("git@github.com:").removesuffix(".git")
    raise RuntimeError(f"无法从 remote origin 解析 GitHub 仓库: {url}")


def commit_meta(commit):
    """读取 commit 原始头，提取原样重建所需的 author/committer/message/tree/parents。"""
    out = git(["cat-file", "commit", commit])
    headers, _, message = out.partition("\n\n")
    meta = {"message": message}
    iso = git(["log", "-1", "--format=%aI|%cI", commit]).strip().split("|")
    for line in headers.split("\n"):
        key, _, value = line.partition(" ")
        if key == "author":
            name, rest = value.rsplit(" <", 1)
            meta["author"] = {"name": name, "email": rest.rsplit("> ", 1)[0], "date": iso[0]}
        elif key == "committer":
            name, rest = value.rsplit(" <", 1)
            meta["committer"] = {"name": name, "email": rest.rsplit("> ", 1)[0], "date": iso[1]}
        elif key == "tree":
            meta["tree"] = value
        elif key == "parent":
            meta.setdefault("parents", []).append(value)
    return meta


def ls_tree_blobs(commit):
    """列出 commit 全部 blob 条目 (path/mode/sha)，-z 防中文/空格路径转义。"""
    out = git(["ls-tree", "-rz", commit])
    entries = []
    for chunk in out.split("\0"):
        if not chunk:
            continue
        meta_part, _, path = chunk.partition("\t")
        mode, typ, sha = meta_part.split(" ")
        if typ == "blob":
            entries.append({"path": path, "mode": mode, "type": "blob", "sha": sha})
    return entries


def changed_paths(old, new):
    """old..new 中新增/修改的文件路径（-z 防转义）。"""
    out = git(["diff", "--name-only", "--diff-filter=AM", "-z", old, new])
    return [p for p in out.split("\0") if p]


def upload_blobs(repo, commit, paths):
    """把变更文件内容上传为远端 blob；返回 path -> sha。"""
    result = {}
    for path in paths:
        content = git(["show", f"{commit}:{path}"])
        blob = gh(
            "POST",
            f"repos/{repo}/git/blobs",
            {"content": base64.b64encode(content.encode("utf-8")).decode(), "encoding": "base64"},
        )
        result[path] = blob["sha"]
    return result


def has_upstream():
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", UPSTREAM_REF],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def main():
    repo = parse_remote()
    if not has_upstream():
        sys.exit("错误: 当前分支无上游，降级通道默认拒绝推送未知全链；请先设置上游或明确推送范围。")

    upstream_sha = git(["rev-parse", UPSTREAM_REF]).strip()
    chain = [c for c in git(["rev-list", f"{UPSTREAM_REF}..HEAD"]).splitlines() if c][::-1]
    if not chain:
        sys.exit("无事可推送（无领先提交）。")

    print(f"仓库: {repo}  分支: {BRANCH}  待推送 {len(chain)} 个提交")
    prev_remote = upstream_sha

    for commit in chain:
        meta = commit_meta(commit)
        short = commit[:12]
        print(f"\n=== {short}（parent {prev_remote[:12]}） ===")
        paths = changed_paths(prev_remote, commit)
        if paths:
            print(f"  上传 {len(paths)} 个变更 blob…")
            upload_blobs(repo, commit, paths)
        # 全量 tree（本地 sha 即内容寻址，新 blob 已上传；远端未变对象天然存在）
        tree = gh("POST", f"repos/{repo}/git/trees", {"tree": ls_tree_blobs(commit)})
        if tree["sha"] != meta["tree"]:
            sys.exit(f"✗ tree 不一致: 远端 {tree['sha']} != 本地 {meta['tree']}，中止")
        created = gh(
            "POST",
            f"repos/{repo}/git/commits",
            {
                "message": meta["message"],
                "tree": tree["sha"],
                "parents": [prev_remote],
                "author": meta["author"],
                "committer": meta["committer"],
            },
        )
        if created["sha"] != commit:
            sys.exit(f"✗ commit 不一致: 远端 {created['sha']} != 本地 {commit}，中止")
        print("  tree/commit SHA 均与本地一致 ✓")
        prev_remote = created["sha"]

    ref = gh(
        "PATCH",
        f"repos/{repo}/git/refs/heads/{BRANCH}",
        {"sha": prev_remote, "force": False},
    )
    final = ref["object"]["sha"]
    if final != chain[-1]:
        sys.exit(f"✗ ref 不一致: {final} != {chain[-1]}，中止")
    print(f"\n✓ refs/heads/{BRANCH} -> {final}")

    # git 直连不通时 fetch 也会失败：手动同步本地 tracking ref，消除「假领先」
    subprocess.run(["git", "update-ref", f"refs/remotes/origin/{BRANCH}", final], check=True)
    print(f"✓ 本地 refs/remotes/origin/{BRANCH} 已同步")
    print("降级推送完成")


if __name__ == "__main__":
    main()
