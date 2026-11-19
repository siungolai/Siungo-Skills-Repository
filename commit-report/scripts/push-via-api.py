#!/usr/bin/env python3
"""降级推送脚本：git push 直连不可达但 api.github.com 可达时，用 gh api git data API 推送。

用法：
    python3 push-via-api.py [目标分支] [起始提交]

    目标分支省略时取当前分支名；禁止把 main / master / slim 作为目标分支——
    本脚本只推功能分支，任何落进主干的改动必须走 PR（issue-pr-loop 三条硬律）。
    起始提交省略时用上游（@{u}）作为基线；无上游时须显式给出起始提交，
    否则拒绝推送未知全链。

行为：
    1. 解析当前仓库 remote origin 的 owner/repo（无 origin 时用参数或报错）；
    2. 计算待推送提交链（<起始提交>..HEAD，按 --topo-order）；
    3. 对每个提交：上传变更 blob → 重建全量 tree → 按原始父链重建 commit
       （author/committer/message 逐字段一致，保证 SHA 与本地完全相同）→ 依次作为父链；
    4. PATCH 远端 ref（force=false，快进校验）；
    5. 成功后将本地 remote-tracking ref 同步到新 sha（git 直连不通时 fetch 会失败，需手动同步）。

前置条件：
    - gh CLI 已安装并登录（gh auth status；token 需含 repo 权限）
    - 本脚本只改变传输通道，不改变提交内容与范围；主干只读，PR 通道内的推送按
      issue-pr-loop 的动作授权前提执行，无需逐轮确认，但仍禁止绕过 PR

限制：
    - 带 gpgsig 等非标准头、或非 UTF-8 编码的 commit 无法经 git-data API 原样重建，
      SHA 校验会中止推送；此时改用 PR 通道，不在本脚本里降级。

已知陷阱（对应 SKILL.md §五.3）：
    - 中文/空格路径：git 输出统一用 -z（NUL 分隔）读取
    - blob content 用 base64 编码上传，原始数据按字节读取（不能 text=True）
    - author/committer date 用 ISO 8601（git log %aI/%cI），epoch 格式会被 API 拒绝
    - gh api 用 --input - 传 JSON（布尔字段在 JSON 里就是 true/false）
"""

import base64
import json
import subprocess
import sys

PROTECTED_BRANCHES = ("main", "master", "slim")
UPSTREAM_REF = "@{u}"  # 不经 f-string 拼接，避免花括号被求值


def git_bytes(args):
    """按字节执行 git，返回原始 stdout（blob 内容可能是二进制或 CRLF）。"""
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def git(args):
    """按文本执行 git，返回解码后的 stdout（仅用于元数据/列表输出）。"""
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


def strip_suffix(value, suffix):
    return value[:-len(suffix)] if value.endswith(suffix) else value


def parse_remote():
    url = git(["remote", "get-url", "origin"]).strip()
    if url.startswith("https://github.com/"):
        return strip_suffix(url[len("https://github.com/"):], ".git")
    if url.startswith("git@github.com:"):
        return strip_suffix(url[len("git@github.com:"):], ".git")
    raise RuntimeError(f"无法从 remote origin 解析 GitHub 仓库: {url}")


def commit_meta(commit):
    """读取 commit 原始头，提取原样重建所需的 author/committer/message/tree/parents。"""
    out = git(["cat-file", "commit", commit])
    headers, _, message = out.partition("\n\n")
    meta = {"message": message, "parents": []}
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
            meta["parents"].append(value)
        elif key in ("gpgsig", "encoding"):
            # git-data API 不传这些头，重建出的 SHA 必不一致；提前给出可操作提示。
            sys.exit(
                f"✗ commit {commit[:12]} 含 {key} 头，git-data API 无法原样重建；"
                "请改用 PR 通道推送"
            )
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
        content = git_bytes(["show", f"{commit}:{path}"])
        blob = gh(
            "POST",
            f"repos/{repo}/git/blobs",
            {"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"},
        )
        result[path] = blob["sha"]
    return result


def upstream_sha_or_none():
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{UPSTREAM_REF}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def main():
    repo = parse_remote()

    if len(sys.argv) > 2:
        branch = sys.argv[1]
        start = sys.argv[2]
    elif len(sys.argv) > 1:
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        start = None  # argv[1] 视为起始提交
        # 单参数兼容：若传入的名字就是当前分支名，按分支名处理。
        if sys.argv[1] == branch:
            start = upstream_sha_or_none()
    else:
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        start = upstream_sha_or_none()

    if branch in PROTECTED_BRANCHES or branch.startswith("refs/heads/"):
        sys.exit(f"错误: 拒绝把 {branch} 作为降级推送目标；主干只读，改动必须走 PR。")

    if start is None:
        sys.exit("错误: 当前分支无上游；请显式给出起始提交（python3 push-via-api.py <分支名> <起始提交>）。")

    start_sha = git(["rev-parse", f"{start}^{{commit}}"]).strip()
    chain = [
        c for c in git(["rev-list", "--topo-order", f"{start_sha}..HEAD"]).splitlines() if c
    ][::-1]
    if not chain:
        sys.exit("无事可推送（无领先提交）。")

    print(f"仓库: {repo}  分支: {branch}  起始: {start_sha[:12]}  待推送 {len(chain)} 个提交")
    prev_remote = start_sha

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
        # 父链逐字照抄本地提交：重建是字节级一致的（tree/author/committer/message 全同），
        # 每个父 SHA 在远端与本地天然相同——无需也不能按 prev_remote 改写。
        # 旧实现把 parents[-1] 当第一父校验/替换，普通 merge 下 prev_remote 恰是次父，
        # 必然误报「第一父不一致」且会替换错父，故直接原样传递。
        original_parents = meta["parents"]
        if len(original_parents) > 1:
            print(f"  merge commit：{len(original_parents)} 个 parent 按原顺序逐字重建")
        parents = original_parents
        created = gh(
            "POST",
            f"repos/{repo}/git/commits",
            {
                "message": meta["message"],
                "tree": tree["sha"],
                "parents": parents,
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
        f"repos/{repo}/git/refs/heads/{branch}",
        {"sha": prev_remote, "force": False},
    )
    final = ref["object"]["sha"]
    if final != chain[-1]:
        sys.exit(f"✗ ref 不一致: {final} != {chain[-1]}，中止")
    print(f"\n✓ refs/heads/{branch} -> {final}")

    # git 直连不通时 fetch 也会失败：手动同步本地 tracking ref，消除「假领先」
    remote_name = "origin"
    subprocess.run(
        ["git", "update-ref", f"refs/remotes/{remote_name}/{branch}", final], check=True
    )
    print(f"✓ 本地 refs/remotes/{remote_name}/{branch} 已同步")
    print("降级推送完成")


if __name__ == "__main__":
    main()
