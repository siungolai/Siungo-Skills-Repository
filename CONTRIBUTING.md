# 贡献总纲（issue-pr-loop）

本仓库所有改动走 issue → PR → 门禁 → 评审 → squash 合并 → 回签关单这一条线。口径事实源是 `issue-pr-loop/SKILL.md`，本文件只作指针与落地状态说明。

## 三条硬律

1. PR 是唯一入口：主干 `main` / `master` / `slim` 只读，一切改动经 PR 排队合并。
2. 一张 PR = 一张单：一张 PR 只对应一张 issue，正文承载五样东西（改动内容、门禁原始输出、评审结论、回签计划、单号）。
3. 主干只接受排队合并：含单号的 squash 提交，基线之后不允许直推与孤儿提交。

唯一例外是进不了仓库的操作（服务器手工命令、线下配置），须在单上留「可复制粘贴的命令、执行人、原始输出」三样。

## 动作授权前提

本技能默认代用户执行 PR 通道内的开 PR、合并、推送功能分支，无需逐轮再向用户请示授权；口径事实源是 `issue-pr-loop/SKILL.md` 的「动作授权前提」段与 §14 第 1 条。禁止直推主干、绕过 PR、force push 主干不变，三层落地状态仍以本表为准。

## 八阶段

| 阶段 | 指针 |
| --- | --- |
| 开单 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| plan 追评 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 分支 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 开 PR | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 门禁 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 评审 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 合并 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |
| 回签关单 | 产出物与判据见 `issue-pr-loop/SKILL.md` §3 八阶段表 |

拆分与分层：开单拆分信号见 `ISSUE_GUIDE.md`；依赖分层见 `issue-pr-loop/references/flow.md` 的「分层规则」一节；同文件永不同层。

## 三层机制落地状态

| 层 | 状态 |
| --- | --- |
| 平台分支保护 | 待维护者在 GitHub 仓库设置开启，本轮不代配置 |
| 本地钩子 | `scripts/deny-main-push.sh` 已入库，安装命令见 `issue-pr-loop/references/pr-contract.md` §8 |
| 对账 | `scripts/gates.json` 的 `reconcile` 段，配合 `scripts/check-issue-pr-loop.py --reconcile` |

三层缺任一层，都不得声称机制已强制；本机状态以本表为准。

## 门禁清单与存量对账基线

- 门禁清单唯一事实源：`scripts/gates.json`（文档不复制真实门禁命令）。
- C14 存量对账基线：`d8fc6978460c8537540c87f6aaad9eb40633a435`（PR #1 引入 2.0.0 的合并提交）。
- 基线之前 23 个不带单号提交属规则建立前的存量，不追溯补 PR；基线之后对账输出必须为空，`--reconcile` 发现孤儿提交即退出 1。

## 接手六步

读总纲（只看红线和八阶段）→ 找一张已关闭的 issue 看四要素 → 看它的 plan 评论 → 打开对应 PR 看评审结论 → 自己开一张只有现象与复现的单 → 用派发脚本派一轮评审。

## 四个数字

报告与台账只看四个数字：存活 PR 数／合并间隔中位数／单小时合并峰值／直推·孤儿提交数（基线之后必须为 0）。

## 相关文档

`ISSUE_GUIDE.md`（开单）、`PR_GUIDE.md`（正文与合并七项）、`REVIEW_DISPATCH.md`（评审派发）。报告要求「四个文档 + 一个门禁清单 + 三个脚本」是否同步，见 `issue-pr-loop/SKILL.md` §15。
