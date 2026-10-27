---
name: skill-authoring
description: 本仓库自建 skill 的创建与修改规范：新建 skill、改写 SKILL.md、增改 references/ 或 scripts/、更新 README 技能表、把技能同步到 ~/.dsh/skills/ 时使用。
agent_created: true
version: 1.1.2
last_updated: 2026-10-27
author: siungolai
---

# skill-authoring：技能创建与修改规范

> ⚠️ **触发加载检查**：收到任何「新建技能 / 改写 SKILL.md / 增改 references 或 scripts / 更新 README 技能表 / 同步技能」类意图时，**先确认本技能已加载**——若本技能不在当前会话的可用技能列表里（技能快照可能早于本技能安装或更新），先用当前环境的技能加载机制加载它，然后按其流程执行。切忌在未加载规范的情况下直接动手写技能。

定位：本技能管「技能该怎么写」——骨架、frontmatter、编号与引用、版本记录、公开前门槛、仓库与用户级副本的同步。**「句子该怎么写」不在这里**：措辞、指针措辞、信息分层、完成判据的写法交给上游技能 `writing-for-agents`（只引用，不复制其条文）。完整条文见 [`references/standard.md`](references/standard.md)（M 必须 / D 默认 / P 禁止），逐场景勾选见 [`references/checklist.md`](references/checklist.md)，骨架与模板见 [`references/templates.md`](references/templates.md)。版本历史见 [`references/version.md`](references/version.md)。

**适用范围**：本仓库内的自建技能。`~/.dsh/skills/` 下的上游技能（mattpocock 系列、`glue-engineer` 等）、`dsh-tui-guide` 等随包技能，以及随应用捆绑的技能——**均不受本规范管辖、不纳入同步范围**，名单与来源见 [`references/external-skills.md`](references/external-skills.md)。

## 1. 何时使用

| 情形 | 动作 |
|---|---|
| 用户要「新建一个技能」 | 走 §3 创建流程，7 步全做完 |
| 改动既有技能的 `SKILL.md` / `references/` / `scripts/` | 走 §4 修改流程，5 步全做完 |
| 只改 README 技能表或目录结构块，不动技能文件 | 走 §4 的第 3–5 步 |
| 把技能同步到 `~/.dsh/skills/` | 走 §4 第 5 步（M11） |
| 只是读取技能内容、不改任何文件 | 不需要本技能 |

**不适用**：`AGENTS.md` / `CLAUDE.md` 这类给 agent 的说明文档——那是上游技能 `writing-for-agents` 的领域，不套本技能的骨架。

## 2. 定位与边界

三件事各有归属，不要串：

- **本技能**：技能的物理约定——目录与命名、frontmatter、骨架、章节编号与引用、版本记录、公开前门槛、副本同步。
- **`writing-for-agents`**（上游技能）：文档的写法——context pointer 怎么措辞、材料该内联还是下放、完成判据怎么写、leading word、pruning。遇到「这句话该怎么写」就加载它。
- **`domain-modeling`**（上游技能）：技能里出现的术语与决策——术语进 `CONTEXT.md`（只定义语言），难以反转的决策进 `docs/adr/`。

三者冲突时：格式与约定以本技能为准，写法以 `writing-for-agents` 为准，术语与 ADR 的格式以 `domain-modeling` 为准。

## 3. 创建流程（7 步）

每一步的判据必须逐条满足才能进下一步。判据不满足就停在这一步修，不要"先往下做、回头再补"。

### 3.1 查重

在仓库与本机技能目录各搜一遍现有技能名与职责（M8）。

**判据**：能写出「本技能与既有技能 `X` 的分工依据」——谁管什么、边界在哪。写不出来，或发现是同一件事的两种说法，说明该并进既有技能，而不是新建一个。

### 3.2 起名

**判据**：`name` 与目录名逐字相同，只含小写英文与连字符（M1）；能一句话说清职责；技能名用英文标识符，标题与正文用中文（D8）。

### 3.3 定骨架

按 [`references/templates.md`](references/templates.md) 的骨架模板裁剪，六个必备构件齐全、顺序正确（M2）。

**判据**：两个条件性构件各自有明确结论——「何时使用」只有一个触发分支时**不写**，有两个及以上分支时必须写且必须是第 1 章；技能会执行不可逆动作（写文件、提交、推送、部署、删除、对外发消息）时必须写「安全边界」，位置在「完成后报告」之前。

### 3.4 写 SKILL.md

**判据**：frontmatter 六键齐全且顺序正确（M3）；`description` 写清了触发场景（M4）；每个 H2/H3 有阿拉伯编号，`§` 引用只写 `§N` / `§N.M`（M6）；正文里每一条 `§`、每一个 `references/…` 路径都真实存在（M7）；正文没有重述 `references/` 里已有的材料，只留 pointer（D2）。

### 3.5 写 references/

至少一个 `version.md`（M5）；有领域术语就加 `CONTEXT.md`；有难以反转的决策就加 `docs/adr/`（D6）。

**判据**：`references/` 下每个文件在 `SKILL.md` 正文里都有一个 pointer，没有孤儿文件（P7）；`version.md` 已记入首个版本。

### 3.6 更新 README

**判据**：技能表加了一行（名称链接 / 版本 / 简介 / 结构）；「目录结构」块补上了该技能；徽章数字与技能数一致（D5）。

### 3.7 自检与同步

**判据**：`python skill-authoring/scripts/check-skills.py` 全部通过、无 FAIL；`deploy-report/references/publish-check.md` 已过一遍并在报告中声明结果（M9、M10）；技能目录已同步到 `~/.dsh/skills/<name>/`（M11）。

## 4. 修改流程（5 步）

### 4.1 定改动级别

**判据**：说得出这次是 `patch`（无行为变化，如错字、编号重排、坏引用修复）、`minor`（条文增删、结构与章节重组）还是 `major`（职责、触发范围、安全边界发生变化），并说得出理由（D3）。

### 4.2 改文件

**判据**：改完先在仓库全树 grep 一次——`§` 编号、`references/…` 与 `docs/adr/…` 路径、「见 `X` 技能」的 X 全部仍然真实存在且指向正确（M7）。重排章节编号后，所有指向旧编号的引用都已跟着改。

**例外**：`references/version.md` 与 `docs/adr/` 里的**历史记录条目不改写**——它们记录的是当时的状态，改写等于伪造历史。

### 4.3 记版本

**判据**：`version` 已按 4.1 的级别 bump；`references/version.md` 追加了一行（版本 / 日期 / 变更）；`last_updated` = 本次日期；表首行 = frontmatter `version`（M5、D4）。

### 4.4 同步派生面

**判据**：README 技能表的版本与简介已跟上；「目录结构」块与磁盘一致；徽章数字对得上（D4、D5）。偏离这条时，必须在完成后报告里说明原因。

### 4.5 自检与同步

**判据**：同 §3.7。

## 5. 安全边界（硬性，任何路径下均适用）

命中任一条即**中止当前动作**，修好再继续；不得"先落地、回头再补"。括号里是完整定义所在的条文编号。

1. **凭据与私有信息零入库**（M9、P3）——这是公开仓库，推出去就撤不回来。
2. **frontmatter 六键齐全且顺序正确**（M3）。
3. **`name` 与目录名一致**，只用小写英文与连字符（M1）。
4. **正文所有引用真实存在**（M7）——`§` 编号、`references/…` 路径、ADR 编号、「见 `X` 技能」的 X。
5. **新建技能前必须查重**，职责不得与既有技能重叠（M8、P4）。
6. **推送前必须跑 publish-check 并声明结果；改动后必须同步到 `~/.dsh/skills/`**（M10、M11）。

## 6. 完成后报告

改动完成后一次性向用户报告（不要分段挤牙膏）：

1. **改了什么**：文件清单，逐个一句话说明；
2. **版本变化**：每个技能「旧版本 → 新版本」与级别（patch / minor / major）；
3. **自检结果**：`check-skills.py` 的通过情况；publish-check 的扫描文件数与命中数；
4. **同步结果**：哪些技能目录已同步到 `~/.dsh/skills/`，哪些没动及原因；
5. **遗留项**：本次故意没做的事，以及建议下次做的事。
