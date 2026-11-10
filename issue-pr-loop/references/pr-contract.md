# PR 契约（pr-contract）

> 本文件是 `SKILL.md` §6、§9、§11 的展开：一张 PR 长什么样、什么时候能合、怎么把「不许直推主干」变成跑不动的机制，以及违规之后怎么收拾。**读法**：`SKILL.md` 说「必须走 PR」，这里说「PR 具体怎么写、怎么拦、怎么查」。

---

## 1. 唯一入口原则

| 改动类型 | 能不能直接推主干 | 必须开 PR | 必须新上下文评审 | 关单写法 |
|---|---|---|---|---|
| 改运行时行为（代码、配置、数据迁移、对外输出） | 不能 | 必须 | 必须 | `Refs` + `needs-live-verify` |
| 纯重构（行为不变，有门禁兜底） | 不能 | 必须 | 可免（正文声明） | `Closes` |
| 纯文档（`docs/`、`README`、注释） | 不能 | 必须 | 可免（正文声明） | `Closes` |
| 改门禁清单 / CI 配置 | 不能 | 必须 | 必须 | `Refs`（改规矩就是改行为） |
| 回车、空格、错别字 | 不能 | 必须 | 可免 | `Closes` |
| 服务器手工命令、线下配置 | 进不了仓库 | 在 issue 里留命令与执行人 | 不适用 | issue 里记录 |

最后一行是**唯一**的例外，且它要求「可复制粘贴 + 谁执行的 + 原始输出」三样都在 issue 里，否则视为没发生。任何一句「这次特殊」「先合了再说」都是在拆这条原则。

---

## 2. 标题

```
<type>(<scope>): <一句话说清改了什么> (#<单号>)
```

- `type`：`feat` / `fix` / `refactor` / `docs` / `test` / `chore`；
- `scope`：模块、目录或功能名，一个词；
- 括号里必须是**单号**，让主干提交历史自己带出线索。

反例：「update」「fix bug」「改动」「WIP」。这些标题在三个月后无法回答「这个提交为什么存在」。

---

## 3. 正文五段

```markdown
## 问题
未传完时进度环已画满，用户误以为传输完成。`Refs #378`

## 改动
- `ui/progress_ring.cpp`：进度从 `transferred / total` 取，`total` 为 0 时显示不确定态
- `test/progress_ring_test.cpp`：新增「未开始传输」与「传输到一半」两条用例

## 验证
- 新增 2 条用例，改动前红、改动后绿
- 手工：选一个 200MB 文件，进度环在 0% 时显示不确定态

## 门禁
```
$ <lint 命令>
...原始输出...

$ <test 命令>
...原始输出...
```

## 回签
改运行时行为，待 `needs-live-verify`；复跑命令：`<一行命令>`
```

纪律：

1. **门禁段贴原文**，不贴「已通过」。评审人要拿它跟自己复跑的输出对照——这正是评审能抓到「门禁跑的是旧基线」的地方。
2. **与 plan 不一致必须写明原因**。悄悄偏离 plan 是评审最常打回的一类。
3. **不写自我表扬**：「大幅优化」「彻底解决」不是证据。
4. **一行一个问题**。正文里出现两个「顺便」就说明该拆 PR 了。

---

## 4. 生命周期

```
draft（还没门禁绿）
  → open（正文五段齐全）
  → needs-review（派发脚本派出，挂标签）
  → approved（三段结论 APPROVE）
  → queued（进入合并队，等最新基线门禁绿）
  → merged（squash 进主干）
  → closed（回签完成，issue 关闭）

任一状态 → changes-requested（评审打回，追加提交后回 open）
任一状态 → abandoned（关掉 PR，删分支；单子回 needs-fix）
```

状态由**事实**决定，不由人声明：正文齐全才算 `open`，门禁绿才算可评审，`APPROVE` 才进队列。聊天里说「差不多了」不进任何状态。

---

## 5. 合并方式与回滚

- **一律 squash**：一张 PR 进主干就是一个提交。理由不是洁癖，是回滚单位——`git revert <squash 提交>` 精确撤掉一件事。
- **合并提交标题**沿用 PR 标题（含单号），这样 `git log --first-parent` 读起来就是一张张单子。
- **不许**在主干上做「先合再改」「合完再补一个修正提交」——那会让一次改动分裂成两个不可分割又不可单独回滚的提交。
- 回滚要开 PR：`revert(<type>): 撤销 #<单号> 的改动 (#<新单号>)`，正文贴原 PR 与回滚原因。回滚也是改动，也走 PR。

---

## 6. 通道被堵住时怎么办

PR 通道本身不能成为阻塞借口。三种常见堵点与处置：

| 堵点 | 处置 |
|---|---|
| 门禁因环境问题红（不是本 PR 引起） | 开一张独立单修环境，本 PR 在正文贴「基线已知红」的证据并等修好；不许把环境修复合进本 PR |
| 评审人迟迟不回 | 先在别人空闲时捡（标签 `needs-review`）；超过一轮仍未评，把存活 PR 数报出来，不加新线 |
| 主干刚被人合了，基线变了 | 本 PR rebase 到新主干，重跑门禁，重贴输出；评审结论仍然有效（除非改动涉及冲突文件，那要重派评审） |
| 需求要变，PR 已经开了一半 | 关掉 PR、单子回 `needs-fix` 重写 plan；不要在开着的 PR 上「顺便改需求」 |

---

## 7. 分支保护清单（首选机制）

在平台仓库设置里逐项确认，缺一项就等于没有机制：

| 项 | GitHub | GitLab |
|---|---|---|
| 主干必须经 PR/MR 才能进 | Branch protection → Require a pull request before merging | Protected branches → Allowed to push: No one |
| 必须通过必需检查 | Require status checks to pass | Merge checks → Pipelines must succeed |
| 禁止直推 | 与第一条同时生效 | 同上（Allowed to push: No one） |
| 禁止 force push | Do not allow force pushes | Allowed to force push: 关闭 |
| 禁止删分支 | Do not allow deletions | 同上 |
| 可选：必须一位评审 | Require approvals = 1 | Approval rules = 1 |

单人仓库的现实问题：**平台不允许自己批准自己的 PR**。这时正确做法是把「必需评审」交给**另一个上下文的会话**（它在本机以独立会话身份读 PR、跑门禁、贴三段结论），而不是关掉这条保护。评审的独立性来自「另一个上下文 + 自己跑的证据」，不来自账号不同。

---

## 8. 本地钩子（兜底机制）

平台保护管得住远端，管不住「我以为我在分支上」。装一个 `pre-push` 钩子，把误推挡在本地：

```bash
#!/bin/sh
# 拒绝任何指向主干的推送。安装在 .git/hooks/pre-push
remote="$1"
zero=0000000000000000000000000000000000000000

while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main|refs/heads/master|refs/heads/slim)
      echo "拒绝直推主干：$remote_ref" >&2
      echo "所有改动必须经 PR：git push origin <你的分支>，再开 PR。" >&2
      exit 1
      ;;
  esac
done

exit 0
```

安装（仓库根执行一次，钩子本身不入库）：

```bash
cp scripts/deny-main-push.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

要点：

- 主干分支名要按仓库实际填（`main` / `master` / `slim` 都见过）；
- 钩子文件放 `scripts/deny-main-push.sh` 入库，`.git/hooks/` 不入库——这样换机器一条命令就能装；
- 钩子挡的是手滑，不是恶意。真正的保证是平台保护 + 下面的对账。

---

## 9. 对账（可审计的第三层）

```bash
# 主干第一父链上最近 30 个提交的标题
git log --first-parent --oneline -30 origin/main

# 只看标题里没有单号的提交（正常应为空）
git log --first-parent --format='%h %s' -30 origin/main | grep -vE '\(#[0-9]+\)$'
```

第二条输出为空才算合规。出现孤儿提交时的处置顺序：

1. 先确认它是不是「合并提交本身」（squash 模式下不应存在）；
2. 是真实改动 → 补开一张 PR 说明这次改动，把提交内容作为 PR 的回溯记录，并在 PR 正文写「违规回溯」；
3. 记一笔：谁、什么时候、绕过了哪一层（平台 / 钩子），以及需要补哪一层机制。

对账频率：每轮收口一次，写进 `SKILL.md` §15 的第 5 项。

---

## 10. 反例（本契约要防的四种绕法）

1. **「只改一行」**——绕过评审的入口一旦打开，例外会膨胀到覆盖全部改动。一行也是 PR。
2. **「纯文档，不用 PR 吧」**——免的是评审，不是 PR。文档 PR 正文首行写「纯文档」+ 贴门禁绿即可，成本不到一分钟。
3. **「先合了再补 PR」**——补的 PR 是表演：门禁没在合并前跑，评审没在合并前看，回滚单位已经丢了。
4. **「PR 开着，我在本地继续改」**——评审看的是分支，你手上是另一个版本。要么推上去，要么停手。
