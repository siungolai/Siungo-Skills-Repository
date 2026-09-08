# Siungo-Skills-Repository

> siungo 的个人 Skill 仓库 — 自建 AI 智能体技能定义与领域规范（SKILL.md + references），持续更新中。

![License](https://img.shields.io/badge/license-MIT-green) ![Skills](https://img.shields.io/badge/skills-2-blue)

## 简介

本仓库集中存放 [siungo](https://github.com/siungolai) 自建的智能体技能（Skills）。每个技能以独立文件夹组织，遵循 `SKILL.md` 规范（YAML 元数据 + 正文指令），可被 WorkBuddy 等支持该规范的智能体环境直接加载调用；细分的领域知识置于各技能的 `references/` 子目录，按需加载，保持主文件精炼。

## 收录技能

| 技能 | 简介 | 结构 |
|---|---|---|
| [`commit-report`](./commit-report/) | Git 提交审阅门技能。执行"分析变更 → 匹配既有提交风格生成 commit 信息 → 展示变更总揽与提交信息供审阅 → 确认后提交（可选推送）"流程；内置三选项回应路径协议、敏感文件与大文件预警、执行通道降级（git 故障时经 GitHub API 单次提交）、完成后报告与安全边界（禁 force push、禁 --no-verify 等）。 | SKILL.md |
| [`design-doc-review`](./design-doc-review/) | 面向公开分发的通用设计文档审计技能。覆盖全篇审计、数值脚本核验、交叉引用完整性、提案先行、文档重构验证与同步校验；`references/` 保留按领域分层的通用模式与 45 条项目级陷阱目录。 | SKILL.md + references/ |

## 目录结构

```
Siungo-Skills-Repository/
├── LICENSE
├── README.md
├── commit-report/
│   └── SKILL.md                      # 技能主文件：审阅门流程、回应路径协议、安全边界
└── design-doc-review/
    ├── SKILL.md
    └── references/                   # 领域知识与模式参考
```

## License

[MIT](./LICENSE) © 2026 烧鹅濑
