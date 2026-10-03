# 仓库外技能台账（external-skills）

> 登记**会与本仓库技能同场加载、但不在本仓库里**的技能。用途有两个：① 让读者知道当前环境里还有什么在响应同一批触发词；② 明确哪些东西**不受本规范管辖**——不受管辖的只登记，不改造、不纳入同步范围（M11）。
> 只说位置与来源，不复制它们的内容。

| 技能 | 所在位置 | 来源 | 是否受本规范管辖 |
|---|---|---|---|
| 上游技能 × 29（`writing-for-agents`、`domain-modeling`、`ask-matt`、`grill-with-docs`、`handoff-doc` 之外的其余技能等） | `~/.dsh/skills/<name>/` | GitHub 公开仓库 [vinvcn/mattpocock-skills-zh-CN](https://github.com/vinvcn/mattpocock-skills-zh-CN)，commit `9fe7e7a3bb352851b986725bab1c7cfb17610a97`，2026-09-11 安装（安装时删除了 `disable-model-invocation` 键，理由见 `~/.dsh/skills/.installed-manifest.json` 的 `adaptation` 字段）。**权威名单不在此重复——见该 manifest。** | 否（上游资产，会被上游更新覆盖） |
| `handoff-doc` | `~/.dsh/skills/handoff-doc/` | 非本人创建・作者未知 | 否 |
| `web-backend`、`web-frontend`、`windows-dev-shell` | `~/.dsh/.agent-presets/siungo-web/skills/` | 本机 agent 预设包 | 否（预设资产，随预设分发） |
| `raw-moving`（无 `SKILL.md`，只有 `scripts/move-by-list.ps1`） | `~/.dsh/skills/raw-moving/` | 本机自制脚本 | 否（不是技能，未登记为技能） |
| `office-docx`、`office-pptx`、`office-xlsx`、`diagnose-windows-sandbox-acl` | 随应用捆绑（不可编辑） | DeepSeek Harness 应用捆绑 | 否（应用资产） |

**判据**：本文件的行必须与磁盘相符；新增或删除仓库外技能时同步这一行。本仓库自建技能**不登记在这里**——它们在 README 的技能表里。
