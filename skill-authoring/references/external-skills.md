# 仓库外技能台账（external-skills）

> 登记**会与本仓库技能同场加载、但不在本仓库里**的技能。用途有两个：① 让读者知道当前环境里还有什么在响应同一批触发词；② 明确哪些东西**不受本规范管辖**——不受管辖的只登记，不改造、不纳入同步范围（M11）。
> 只说位置与来源，不复制它们的内容。

| 技能 | 所在位置 | 来源 | 是否受本规范管辖 |
|---|---|---|---|
| 上游技能 × 37（`ask-matt` … `writing-shape`，与上游仓库同名无前缀） | ① `/root/.dsh/profiles/{web,dsh-tui}/node_modules/mattpocock-skills-zh-local/skills/`（本地 bundle，自带 provider，rank 600）；② `~/.dsh/skills/<name>/`（软链到该 bundle，供 web profile 的 skill-filesystem 扫） | GitHub 公开仓库 [vinvcn/mattpocock-skills-zh-CN](https://github.com/vinvcn/mattpocock-skills-zh-CN)（HEAD `604ad61c`，2026-10-20），对应上游同步 mattpocock/skills@24fe0ef（v1.3.1，2026-10-08），2026-10-24 打包成本地 bundle `mattpocock-skills-zh-local` 装入两个 profile。**安装时未删改任何 frontmatter 键**——`disable-model-invocation`、`argument-hint`、`metadata` 均保持上游原样。上游官方 npm 包 [`@vinvcn/dsh-mattpocock-skills-zh`](https://www.npmjs.com/package/@vinvcn/dsh-mattpocock-skills-zh) v1.3.1 曾被装过，但其构建期会给每个 `name` 加 `zh-` 前缀，导致 `/grill-me` 等原名无法调用，已于 2026-10-24 卸下。 | 否（上游资产，会被上游更新覆盖） |
| `glue-engineer` | `/root/deepseekharness/Github/local-skill-bundles/glue-engineer-bundle/skills/glue-engineer/`，经 `dsh plugin --profile dsh-tui add` 以 link 依赖装入 dsh-tui | GitHub 公开仓库 [ID-VerNe/skill-forge](https://github.com/ID-VerNe/skill-forge) 的 `glue-engineer/` 子目录（v4.0.0，HEAD `60a6610`，2026-10-11），2026-10-24 打包成本地 bundle（自带 provider，rank 600） | 否（上游资产） |
| `dsh-tui-guide` | `/root/.dsh/profiles/dsh-tui/node_modules/@deepseek-harness-tui/dsh-tui/guide/dsh-tui-guide/` | dsh-tui 包（v0.17.0）随包用户手册，由 `bin/dsh-tui.js` 的 `withGuideSkillDir()` 注入 `DSH_BUNDLED_SKILL_DIR` 环境变量，交给 dsh-skill-filesystem 的随包技能根（rank 600）读取 | 否（应用资产） |
| `office-docx`、`office-pptx`、`office-xlsx`、`office-export-pdf`、`office-render`、`office-recalculate`、`diagnose-windows-sandbox-acl` | `/root/.npm/_npx/1e7f6d9597241db0/node_modules/@deepseek-ai/dsh-skill-office/assets/` 与 `.../dsh-sandbox-windows-acl/assets/` | DeepSeek Harness 应用捆绑（不可编辑） | 否（应用资产） |

**判据**：本文件的行必须与磁盘相符；新增或删除仓库外技能时同步这一行。本仓库自建技能**不登记在这里**——它们在 README 的技能表里。

**两套扫描机制，不要混**：
- **dsh 的 filesystem roots**（`dsh-skill-filesystem`，rank：project `.dsh/skills`=100 / project `.agents/skills`=200 / `customSkillDirs`=300 / `~/.dsh/skills`=400 / `~/.agents/skills`=500 / `bundled`=600）——只有 profile 的 `skill-filesystem` 未 disabled 时才扫。**dsh-tui 的 `cordis.patch.yml` 已把它 disabled: true**，所以 TUI 会话不扫任何 skills 目录，只走 provider。
- **pnpm 的 `skills.dirs`**（`pnpm-workspace.yaml` 的 `skills: dirs:`，profile 相对路径 + `permissions:` 授权）——`dsh plugin add` 后跑 `pnpm approve --all -y` 时用来生成 `pnpm-@<scope>+<pkg>-<name>` 形式的符号链接并写 `.gitignore`（内容 `pnpm-*`）。它只满足 approve 的前置校验，**与 dsh 能否加载无关**。

**上游命名规则**：上游仓库里的技能就叫 `grill-me` / `grilling` / `grill-with-docs` 这样的原名。上游**官方** npm 包的构建脚本 `dsh-plugin/scripts/copy-skills.mjs`（`const prefix = process.env.SKILL_PREFIX ?? 'zh-'`）会把每个 frontmatter `name:` 改成 `zh-<name>`，`rewrite-references.mjs` 再把正文里的 `/grilling` 改写成 `/zh-grilling`——但**裸写的技能名不重写**（已知局限）：`skills/grill-me/SKILL.md` 仍写 `` `grilling` ``、`skills/grill-with-docs/SKILL.md` 仍写 `` `grilling` `` 和 `` `domain-modeling` ``。本机改用本地 bundle、以 `SKILL_PREFIX=''` 重跑同一套构建脚本，故本机技能名 = 上游原名。本仓库正文引用上游技能时直接写原名（`check-skills.py` 的 M7 按 `~/.dsh/skills/<name>/SKILL.md` 查找，原名才能命中）。
