# 坑与判定细节（pitfalls）

> `SKILL.md` 只放流程与判据；本文件收「为什么会这样」的机制细节、真实报错原文与判定分歧。
> 都是本机实测踩出来的，跨宿主不一定成立——换环境时先复现再采信。

---

## 一、两套扫描机制，不要混

这是本技能最容易出错的地方：pnpm 与 dsh 各有一套"技能目录"概念，名字都叫 skills，指向完全不同的东西。

### 1.1 dsh 的 filesystem roots

`dsh-skill-filesystem` 的 `roots(cwd)` 按 rank 排序，**rank 小者赢**：

| 来源 | rank |
|---|---|
| project `.dsh/skills` | 100 |
| project `.agents/skills` | 200 |
| customSkillDirs | 300 |
| `~/.dsh/skills`（user-dsh） | 400 |
| `~/.agents/skills` | 500 |
| bundled / provider | 600 |

取技能名用 **frontmatter 的 `name`，不用目录名**（`stringField(parsed.data, "name")`）——所以目录名可以随便起，技能名仍由 frontmatter 决定。

### 1.2 pnpm 的 `skills.dirs`

`skills: dirs: [.dsh/skills]` 声明的是 **profile 相对路径**，即 `/root/.dsh/profiles/<p>/.dsh/skills/`，与 `~/.dsh/skills/` 毫无关系。

实测：手动 `mkdir` 该目录后跑 `pnpm install`，会立刻生成一批符号链接，命名规则 `pnpm-@<scope>+<包名>-<技能名>`，指向 `../../node_modules/<包>/skills/<技能名>`，并自动写一个 `.gitignore`（内容 `pnpm-*`）。

写成绝对路径会直接被拒：

```text
There is no agent skill directory to link the approved skills of @vinvcn/dsh-mattpocock-skills-zh into
```

help 提示只认 `.claude/skills` 这类相对名。

### 1.3 结论

**pnpm 的 `skills.dirs` 与 dsh 能否加载技能无关**，它只满足 `pnpm approve` 的前置校验。技能是包自带 provider 通过 `ctx.skills.registerProvider` 注册的，不走链接。

所以：声明了 `skills.dirs` 但目录是空的、或者链接建好了，都不构成"装好了"的证据；反过来，目录没建也不影响 provider 路线生效。

---

## 二、dsh-tui 为什么不扫 skills 目录

dsh-tui 的 `cordis.patch.yml` 把 `skill-filesystem` 与 `tool-skill` 都置 `disabled: true`：

```yaml
- id: skill-filesystem
  disabled: true
```

读 preset 的注释确认这是有意的设计：skill 注册表在 host composition 里按 scope 分层，`skill-filesystem` 只贡献本地根发现，而 TUI 不扫文件系统技能；`dsh-tool-skill`（约 9KB 的 `<available_skills>` 全量目录注入）被刻意移除，换成 preset 的 `skill-search.mjs` 提供 `skill_search` / `skill_load` 两个小工具。

scope 可见性因此成立：`dsh-skill` 的 `collectFresh` = `[this.layers.global, ...this.layers.chainLayers(options.scope)]`，`dsh-scope` 的 merge 是"global 条目在前、scope 链由远及近遮蔽，最近的 scope 同名者赢"。插件在 profile 组合里 apply（无 scope）→ 注册进 global 层 → preset 的 agent scope 读得到。

**推论**：往 `~/.dsh/skills/` 建软链，对 dsh-tui 毫无作用，只对 filesystem 仍启用的 profile（本机是 web）有意义。别用"我在 skills 目录里看到它了"来证明 TUI 装好了。

---

## 三、上游构建脚本加 `zh-` 前缀：`/原名` 调用不存在的真凶

上游 `vinvcn/mattpocock-skills-zh-CN` 官方 npm 包 `@vinvcn/dsh-mattpocock-skills-zh` 的构建脚本：

- `dsh-plugin/scripts/copy-skills.mjs`：`const prefix = process.env.SKILL_PREFIX ?? 'zh-'`，把每个 frontmatter `name:` 改成 `zh-<name>`；
- `dsh-plugin/scripts/rewrite-references.mjs`：只重写 `/技能名` 形式的引用，**裸写的技能名不重写**（上游 README 已声明的已知局限）。

后果：`/grill-me` 在 TUI 里不存在（实际是 `/zh-grill-me`），而 `skills/grill-me/SKILL.md` 正文仍写 `` `grilling` ``、`skills/grill-with-docs/SKILL.md` 仍写 `` `grilling` `` 与 `` `domain-modeling` ``——跨技能调用指向无前缀名，与注册名对不上。

**解法（不要改上游文件）**：用上游同一套构建脚本、`SKILL_PREFIX=''` 重跑，得到原名版 `skills/`，再打本地 bundle（路线 B）。实测两版文件逐字节 diff 只差 `name:` 行与 `/handoff` 这类内部引用。

**顺带确认**：`dsh-tui` 的 `/` 命令注册链（`lib/types/dsh-adapter/channel/skill-catalog.js:129` 的 `parseCommandName('/'+skill.name)?.name === skill.name` + `!isLocalCommandName`，与 `lib/types/commands.js:380` 的正则 `^\/([a-z][a-z0-9_-]*)(?=$|[\t\n\r ])`）对 `zh-grill-me` 与 `grill-me` **都放行**，都不是 LOCAL/HIDDEN 命令——前缀不阻断注册，只是名字变了。

---

## 四、真实报错原文对照表

| 报错 | 触发条件 | 解法 |
|---|---|---|
| `Error: × IO error: not a terminal` | 裸跑 `pnpm approve` | 带 `--all -y` |
| `ERR_PNPM_NO_AGENT_SKILLS_DIR` | 未声明 `skills.dirs` | 在 profile 的 `pnpm-workspace.yaml` 补 `skills: dirs: [.dsh/skills]` 与 `permissions: '<包名>': skills: true` |
| `Cannot find package 'yaml' imported from .../index.js` | bundle 目录没装依赖 | 在该目录 `pnpm install` |
| `Error: dsh: cannot resolve profile bundle "<name>" from the dsh installation or /root/.dsh/profiles/<p>` | `dsh plugin add ./<目录>` 生成的相对 link 路径解析错 | package.json 里写绝对路径 `link:/root/deepseekharness/Github/local-skill-bundles/<name>-bundle` |
| `dsh: [billion-context] patch: entry "preset-standard" not found` | dsh-tui 组合里没有这些 entry | 无害，dsh-tui app 自身行为 |
| `skill_search` 返回 `No skills match ...` | 查询词含描述里没有的词（AND 语义） | 先用单个特征词试，见 SKILL.md §6.3 |

---

## 五、`dsh --profile dsh-tui --help` 会挂住

实测 `timeout 20` / `timeout 25` 均 exit 124，而 web profile 的 `--help` 正常。这是 dsh-tui app 的自身行为，**不是安装失败的症状**，别顺着这条线索排查。

同理，dsh-tui profile 跑的是 TUI 适配器不是 HTTP host，`curl` 本地环回端口返回 `000`（连不上）属预期。

---

## 六、隔离冒烟：别污染运行态

想验证新装的 bundle 不影响现有会话时，不要直接重启正在用的 TUI。做法是起一个隔离实例再清理：

```bash
BILI_ZONE_PORT=<未被占用的端口> <启动命令> &
```

确认装载无异常后 kill 掉。本机的端口占用参考：web profile 的 HTTP host、billion-context sidecar、以及 TUI 实例各自的 `BILI_ZONE_PORT`——重复会撞双实例。

---

## 七、验证脚本要真递归

`scripts/verify.mjs` 里查 `__pycache__` 时，第一版写成了永远返回 `true` 的空壳（看起来全绿，实际什么都没查）。改成 `withFileTypes` 真递归才抓得到。

**教训**：自检脚本本身也要被验证——"全 PASS"可能只是检查逻辑是空的。判据是**故意制造一个失败样本，看脚本是否真的报 FAIL**。

同类教训还有一处：断言别照记忆写。第一次写"grill-with-docs 保留 `/grilling`"判 FAIL，因为正文里是反引号 `` `grilling` `` 而不是 `/grilling`——**断言也要先对着真实文件核对**。

---

## 八、本机命令差异

- 无 `python`，只有 `python3`。上游 SKILL.md 与 `agents/*.md` 里写的 `python -m polyglot` 在本机不可直接执行——验证时用 `python3`，并在完成后报告里说明这个差异（不要为了迁就上游去建全局 alias）。
- `gh` CLI 不存在，但支持 `GITHUB_TOKEN` / `GH_TOKEN` 环境变量，未设置时降级为未鉴权仍可用。

