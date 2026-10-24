# skill-authoring 修订记录

> 按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.1.1 | 2026-10-24 | 上游 mattpocock 技能换用原名版本地 bundle：`@vinvcn/dsh-mattpocock-skills-zh`（构建期给每个 `name` 加 `zh-` 前缀，导致 `/grill-me` 等仓库原名无法调用）已从两个 profile 卸下，改为本地 bundle `mattpocock-skills-zh-local`（用上游同一套构建脚本以 `SKILL_PREFIX=''` 重跑生成，37 个技能名 = 上游原名）。`external-skills.md` 的台账行、位置列、「上游命名规则」节随之改为原名版事实；`~/.dsh/skills/` 下 37 个软链由 `zh-<name>` 改为 `<name>`。SKILL.md / standard.md / templates.md / agent-team-setup / reference-archive 里引用上游技能的写法由 `zh-<name>` 统一改回原名（`check-skills.py` 的 M7 按 `~/.dsh/skills/<name>/SKILL.md` 查找）。README 技能表简介同步。 |
| 1.1.0 | 2026-10-24 | 修订 `references/external-skills.md` 台账，使其与磁盘相符：上游 mattpocock 技能的真实形态从「`~/.dsh/skills/` 下 29 个 + `.installed-manifest.json`」（该 manifest 从未存在，属失实引用）改为「web 与 dsh-tui 两个 profile 的 node_modules 插件包 `@vinvcn/dsh-mattpocock-skills-zh` v1.3.1 共 37 个 `zh-*` 技能 + `~/.dsh/skills/zh-*` 软链」；补登本地 bundle `glue-engineer` 与随包的 `dsh-tui-guide`；删除磁盘上已不存在的 `handoff-doc`、`raw-moving`、`~/.dsh/.agent-presets/siungo-web/` 三行，`office-*` 行改为 npx 缓存里的真实路径并补齐 `office-export-pdf`/`office-render`/`office-recalculate`。新增两节：dsh 的 filesystem roots（rank 100–600，dsh-tui 已 disabled）与 pnpm 的 `skills.dirs`（只满足 approve 前置校验，与 dsh 能否加载无关）的机制区分，以及上游 `zh-` 前缀命名规则（含"裸写技能名不重写"的已知局限）。SKILL.md 与 standard.md / templates.md 里引用上游技能的写法统一改为带 `zh-` 前缀（此前 `check-skills.py` 的 M7 判 `code-review` 不存在）。 |
| 1.0.0 | 2026-10-03 | 首次创建：把此前散落在四个自建技能里的成文约定提炼为一份规范——管辖范围（本仓库自建技能）、六个必备 + 两个条件性构件的规定骨架、frontmatter 六键、全阿拉伯章节编号与 `§` 引用解析规则、M/D/P 三档条文、按场景分组的自检清单、四份模板、仓库外技能台账，以及 `scripts/check-skills.py` 校验脚本。 |
