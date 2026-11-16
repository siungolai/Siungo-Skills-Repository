# 开单指引（issue-pr-loop）

本文件只讲开单；流程判据以 `issue-pr-loop/SKILL.md` §4 为准。

## 四要素

每张单写全四样：现象 / 期望 / 复现命令 / 影响面。缺复现命令的单打 `needs-repro`，不进 plan。

## 拆分信号

一条单是否要拆、按哪三条独立性判据拆，拆分信号表见 `issue-pr-loop/references/flow.md` 的「开单与拆分」一节；本文件不复制判据。同文件永不同层。

## 唯一例外（C4）

只有进不了仓库的操作（服务器手工命令、线下配置）可以就地留证，必须留三样：可复制粘贴的命令、执行人、原始输出。除此之外，改动一律进 PR；单只记录问题与证据，不承载补丁。

## 回签模板

行为类改动合并后挂 `needs-live-verify`，换人真机回签；回签记录模板见 `issue-pr-loop/references/flow.md` 的「回签与关单」一节，关单写法见 `issue-pr-loop/SKILL.md` §10。

## 标签

常见标签与含义见 `issue-pr-loop/SKILL.md` §12；开单后由执行线在 plan 评论里追评，评审线另起新上下文。
