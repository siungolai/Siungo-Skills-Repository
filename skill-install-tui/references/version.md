# skill-install-tui 修订记录

> 按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0.1 | 2026-10-24 | §6.5 从「上游裸技能名不重写」改写为「上游构建脚本给技能名加 `zh-` 前缀，`/原名` 调用不存在的真凶」：补上 `copy-skills.mjs` 的 `SKILL_PREFIX` 默认值与 `rewrite-references.mjs` 的行为、dsh-tui `/` 命令注册链对两种名字都放行的验证结论，并把解法从「报告里说明」改为「用 `SKILL_PREFIX=''` 重跑上游构建脚本打本地 bundle」。`references/pitfalls.md` 新增第三节（该机制 + `/` 命令注册链判据）、原第三~七节顺延为第四~八节，并在第七节补一条"断言要对着真实文件核对"的教训（`/grilling` 与反引号 `` `grilling` `` 之别）。 |
| 1.0.0 | 2026-10-24 | 首次创建：把「装 `@vinvcn/dsh-mattpocock-skills-zh` 与 `glue-engineer` 两个技能并验证生效」的实操提炼为流程——先认装载路径（两个 profile 独立、dsh-tui 的 skill-filesystem 被 disabled、rank 小者盖）、路线 A（npm 包：双 profile 安装 + `pnpm approve` 撞 `ERR_PNPM_NO_AGENT_SKILLS_DIR` 的解法 + 重启 TUI）、路线 B（纯目录技能打本地 bundle，五个必备件与三个坑）、五层验证（包自检 → provider 直跑 → dump-config 挂载 → 运行态 skill_search → 重名冲突），以及五类症状排查（重启遗漏、profile 装错、skill_search 的 AND 语义假阴性、pnpm skills.dirs 与 dsh filesystem roots 两套机制、上游裸技能名不重写）。 |
