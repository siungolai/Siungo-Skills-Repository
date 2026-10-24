---
name: skill-install-tui
description: 把上游或第三方 SKILL 装进本机 dsh-tui 会话并验证它真的生效：装 npm 包式技能、给纯目录技能打本地 bundle、改 skill_search 查不到的问题时使用。
agent_created: true
version: 1.0.1
last_updated: 2026-10-24
author: siungolai
---

# skill-install-tui：把技能装进 dsh-tui 并验证它真的生效

> ⚠️ **触发加载检查**：收到任何「装这个 SKILL / 装到 TUI 里 / 装好了但 skill_search 查不到 / 给技能打包」类意图时，**先确认本技能已加载**——若本技能不在当前会话的可用技能列表里（技能快照可能早于本技能安装或更新），先用当前环境的技能加载机制加载它，然后按其流程执行。切忌在未确认宿主装载路径的情况下直接照上游 README 的 `ln -s ~/.claude/skills` 动手。

定位：与 `skill-authoring`（技能该怎么写）、`deploy-report`（变更何时上线）分工——本技能只管**把一个已成形的技能搬进本机 dsh 环境并让它被会话看见**，上游资产本身一个字不改。核心机制是「认准装载路径 → 两个 profile 都装 → 授权 → 重启 → 分层验证」，五层验证缺一层就不算装好。踩过的坑与判定细节见 [`references/pitfalls.md`](references/pitfalls.md)，版本历史见 [`references/version.md`](references/version.md)。

## 1. 何时使用

| 情形 | 动作 |
|---|---|
| 上游给的是 npm 包 / dsh 插件（`dsh plugin add <包名>`） | 走 §3 路线 A |
| 上游只给一个 SKILL.md 目录，或只教 `ln -s ~/.claude/skills` | 走 §4 路线 B（打本地 bundle） |
| 装完了，但 `skill_search` 查不到 / 查不全 | 先走 §6.3 的匹配自查，再怀疑安装 |
| 只是把**自己仓库里**的技能同步到 `~/.dsh/skills/` | 不是本技能；那是 `skill-authoring` 的 M11 |
| 上游技能内容不合用，要改写 | 不是本技能；上游资产默认原样落地 |

## 2. 先认准装载路径

**动作**：动手前确认三件事，全部成立才继续。

**判据**：

1. 能说出目标 profile 是哪个——本机有 `web` 与 `dsh-tui` 两个，**bundle 列表各自独立**，只装一个另一个就失效。
2. 能说出该 profile 是否扫描 skills 目录——`dsh --profile <p> --dump-config` 里 `skill-filesystem` 是否为 `disabled: true`。本机 dsh-tui **是**，所以 TUI 会话不扫 `~/.dsh/skills/`，只认 provider（rank 600）。
3. 知道 rank 谁盖谁：filesystem 根 100–600、provider/bundle 600；**rank 小者赢**。装在 `~/.dsh/skills/`（rank 400）会盖过 rank 600 的 provider，同名技能要意识到这一点。

**理由**：本机实测过「装进 web profile 但会话跑在 dsh-tui 适配器下」→ `skill_search` 全查不到，一度误判为安装失败。路径没认准，后面每一步验证都会给出假阴性。

**细则**：dsh 的 filesystem roots 与 pnpm 的 `skills.dirs` 是**两套独立机制**，容易混——见 §6.4 与 [`references/pitfalls.md`](references/pitfalls.md)。

## 3. 路线 A：npm 包式技能

**动作**：两个 profile 各装一次。

```bash
dsh plugin --profile web    add <包名>
dsh plugin --profile dsh-tui add <包名>
```

**判据**：`/root/.dsh/profiles/<p>/package.json` 同时出现两处——`dependencies` 里的 `"<包名>": "^<版本>"`，以及 `dsh.profile.bundles` 数组里的 `"<包名>"`。只写进一处都不算装好。

### 3.1 授权

**动作**：在装过包的 profile 目录下跑 `pnpm approve --all -y`。

**判据**：输出 `There are no packages awaiting approval`（exit 0）才算已批。

**会撞的墙**：

1. 裸跑 `pnpm approve` → `Error: × IO error: not a terminal`，必须带 `--all -y`。
2. 带参后报 `ERR_PNPM_NO_AGENT_SKILLS_DIR`。解法是在该 profile 的 `pnpm-workspace.yaml` 声明
   `skills: dirs: [.dsh/skills]` 与 `permissions: '<包名>': skills: true`。
   **只能写 `.dsh/skills`**：写 `.claude/skills` 无效，写绝对路径 `/root/.dsh/skills` 也被拒（只认 profile 相对名）。

**理由**：`skills.dirs` 声明的是 profile 相对路径，建不建目录、链不链接，与 dsh 能否加载**毫无关系**，它只满足 pnpm approve 的前置校验。别把它当成"技能的安装位置"。

### 3.2 重启 TUI

**判据**：bundle 列表只在进程启动时由 `dsh-app-boot` 的 `loadProfileDirectory` 重读，所以 tmux 'dsh' 会话里的 TUI（`dsh-tui.js` / `host-entry.js` 父子进程）**必须重启**，否则后面所有验证都查不到。

**理由**：这是整条流程里最容易漏、且症状最像"装失败"的一步——包在磁盘上、`--dump-config` 也认，但会话里就是没有。

## 4. 路线 B：打本地 bundle

**触发**：上游只给 SKILL.md 目录，或只教 Claude 路线（`ln -s <dir> ~/.claude/skills`、`setup.sh` 拷贝到 `~/.claude/agents`）。本机 `~/.claude` 不存在，这套安装法一律不适用。

**动作**：在 `/root/deepseekharness/Github/local-skill-bundles/<name>-bundle/` 建五个必备件。

**判据**：

| 文件 | 必须满足 |
|---|---|
| `index.js` | 自包含 provider：`RANK=600`、`SOURCE='bundled'`，读 `skills/<name>/SKILL.md` 的 frontmatter；`invocationFrom(data)` = `{modelInvocable: data['disable-model-invocation']!==true, userInvocable: data['user-invocable']!==false}`；`apply(ctx)` 调 `ctx.skills.registerProvider`；另 export `name` 与 `inject=['skills']` |
| `package.json` | 含 `dsh.bundle.patch: "./cordis.patch.yml"`——**少这个键挂不上**；`files` 列出 index.js / cordis.patch.yml / README.md / skills |
| `cordis.patch.yml` | `- insert:` 下给出 `- id: <name>-bundle` 与 `name: '<name>-bundle'` |
| `skills/<name>/` | 上游全量拷贝，**清掉 `__pycache__`** |
| `scripts/verify.mjs` | 包自检，见 §5 第 ① 层 |

**三个坑**：

1. bundle 目录裸跑 `node` 报 `Cannot find package 'yaml'` → 先在该目录 `pnpm install`。
2. `dsh plugin add ./<目录>` 生成的 link 路径会重复且为相对写法，解析到 `/root/.dsh/deepseekharness/...` 断链，报 `Error: dsh: cannot resolve profile bundle "<name>"`。**解法：package.json 里手写绝对路径** `"<name>-bundle": "link:/root/deepseekharness/Github/local-skill-bundles/<name>-bundle"` 再 `pnpm install`；`link:../xxx` 这种短相对写法也不对。
3. 改 `package.json` 的 bundles 数组**别用 sed**（会切坏 `dependencies` 行导致 JSON 破损），用 python json 重写或整文件覆盖。

装完同样两个 profile、同样 §3.1 授权、同样 §3.2 重启。

## 5. 分层验证

**动作**：从便宜到贵逐层过，**每层都要看到通过标准才进下一层**。

**判据**：

| 层 | 手段 | 通过标准 |
|---|---|---|
| ① 包自检 | `node scripts/verify.mjs` | 全 PASS。至少覆盖：`list()` 计数与 `name` 正确、`rank=600`、`source=bundled`、`get()` 正文非空且已剥掉 frontmatter、`get()` 缺文件返回 `undefined`、`cordis.patch.yml` 含 insert id、`package.json` 声明了 `dsh.bundle.patch`、`skills/` 下无 `__pycache__` |
| ② provider 直跑 | import bundle 后 `createProvider().list({})`，逐个 `get()` | 条目数、`name`、`invocation` 与 frontmatter 一致；`get()` 全成功 |
| ③ profile 挂载 | `dsh --profile <p> --dump-config` | patch 栈尾部出现 `# == <bundle>` 与 `- id: <bundle>`，且无相关报错 |
| ④ 运行态 | 重启后 `skill_search '<词>'` + `skill_load <name>` | 命中并注入正文。**只有这一层算数** |
| ⑤ 重名冲突 | 与 `~/.dsh/skills/` 的自建技能名对比 | 零重名；有重名时按 §2 的 rank 规则判断谁盖谁 |

**理由**：前三层全绿而第四层查不到是完全可能的（没重启、scope 不可见、查询词不匹配），把④当成唯一验收标准才不会被假阳性骗过去。

## 6. 常见症状与排查

### 6.1 装完了但 `skill_search` 查不到

按序排查，**不要一上来就重装**：

1. **重启了吗**（§3.2）——最高频原因。
2. **装对 profile 了吗**（§2）——会话跑在哪个适配器下。
3. **查询词太长了**（§6.3）。
4. 前三层里哪一层没过，回哪一层修。

### 6.2 怀疑装载链路断了

读宿主源码确认，别猜：`skill-search.mjs` 的 `apply` 注册 `skill_search` / `skill_load`，其 `ctx.skills.list({scope: exec?.agent ?? ctx, cwd, signal})` 读的就是技能注册表，与 provider 来源无关；`dsh-skill` 的 `collectFresh` = global 层 + scope 链，插件在 profile 组合里 apply（无 scope）→ 注册进 global 层 → agent scope 读得到。

### 6.3 查询词不匹配（最像"安装失败"的假阴性）

`skill_search` 是 **AND 语义**：每个查询词都必须出现在 haystack 里，haystack 只含 `name + description + whenToUse`。**查询词里只要有一个词不在描述里就 0 命中。**（宿主实现为遍历查询词的 all-match 判定，源码见 preset 的 `skill-search.mjs`。）

**判据**：先用单个特征词试（`'glue'`、`'胶水程序员'`），命中即证明安装没问题、是查询词问题。实测：`'glue engineer compose libraries system design'` 全灭，而 `'glue'` 秒中——因为描述里写的是 `composing existing open-source libraries`，没有 `compose` 和 `system`。

### 6.4 `skills.dirs` 与 dsh 能否加载无关

**判据**：pnpm 的 `skills.dirs` 指向 profile 相对目录（`/root/.dsh/profiles/<p>/.dsh/skills/`），它只服务 pnpm 的 approve 前置校验；dsh 的 filesystem roots 是另一套（project `.dsh/skills`=100 / project `.agents/skills`=200 / customSkillDirs=300 / `~/.dsh/skills`=400 / `~/.agents/skills`=500 / bundled=600），且 dsh 取技能名用 **frontmatter 的 `name`，不用目录名**。两者互不影响，别用一个的结论推另一个。

### 6.5 上游构建脚本给技能名加前缀（`/原名` 无法调用的真凶）

上游 npm 包的构建脚本 `dsh-plugin/scripts/copy-skills.mjs`（`const prefix = process.env.SKILL_PREFIX ?? 'zh-'`）会把每个 frontmatter `name:` 改成 `zh-<name>`，`rewrite-references.mjs` 再把正文里的 `/grilling` 改成 `/zh-grilling`——但**裸写的技能名不重写**：实测 `skills/grill-me/SKILL.md` 仍写 `` `grilling` ``、`grill-with-docs` 仍写 `` `grilling` `` 与 `` `domain-modeling` ``。于是 `/grill-me` 不存在（实际是 `/zh-grill-me`），而正文里的跨技能调用仍指向无前缀名。

**判据**：遇到「上游 README 说调用 `/xxx` 但 TUI 里没有这个命令」时，先查 `list()` 里技能的真实 `name`，别急着怀疑安装。若确认是上游前缀所致，**不要改上游文件**（会被上游更新覆盖）——改用路线 B 打本地 bundle，以 `SKILL_PREFIX=''` 重跑上游同一套构建脚本，即可得到原名版；并在完成后报告里说明该调用在本机指向的名字。

## 7. 安全边界（硬性，任何路径下均适用）

1. **上游技能内容零改**——本技能只负责搬运与验证。要改上游资产先说明理由并单独确认，否则下次 `dsh plugin add` 升级就被覆盖。
2. **不擅自 commit / push**——仓库是公开仓库，推送即永久公开；提交与推送都要用户明确许可（`skill-authoring` 的 M9、M10）。
3. **凭据与私有信息零入库**——写 bundle 的 README 与 `references/` 时不得带入 token、PAT、内网地址、带用户名的 host 别名；引用本机路径只写到目录层级，不写凭据文件名。
4. **重启前先确认影响面**——TUI 进程可能正跑着别的会话，重启前说明会中断什么，不要静默 kill。
5. **不把 `link:` 依赖指向临时目录**——`/tmp` 会被清理，bundle 必须落在持久路径（`/root/deepseekharness/Github/local-skill-bundles/`）。

## 8. 完成后报告

装完一次性向用户报告（不要分段挤牙膏）：

1. **装了什么**：包名 / bundle 名 + 版本 + 上游来源（仓库与 commit 或 npm 版本）；
2. **落在哪**：两个 profile 的 `package.json` 与 `node_modules` 路径；`~/.dsh/skills/` 是否建了软链、对哪个 profile 有意义；
3. **验证结果**：§5 五层各自的通过情况与关键数字（list 计数、get 成功数、`skill_search` 命中的查询词）；
4. **重启情况**：旧/新进程 pid、哪些会话受影响；
5. **已知局限**：上游未重写的裸技能名、本机命令差异（如无 `python` 只有 `python3`）等；
6. **遗留项**：本次故意没做的事，以及建议下一步。
