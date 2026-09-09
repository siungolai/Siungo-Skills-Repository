# Siungo-Skills-Repository

> siungo 的个人 Skill 仓库 — 自建 AI 智能体技能定义与领域规范（SKILL.md + references），持续更新中。

![License](https://img.shields.io/badge/license-MIT-green) ![Skills](https://img.shields.io/badge/skills-3-blue)

## 简介

本仓库集中存放 [siungo](https://github.com/siungolai) 自建的智能体技能（Skills）。每个技能以独立文件夹组织，遵循 `SKILL.md` 规范（YAML 元数据 + 正文指令），可被 WorkBuddy 等支持该规范的智能体环境直接加载调用；细分的领域知识与配套脚本置于各技能的 `references/`、`scripts/` 子目录，按需加载，保持主文件精炼。

## 收录技能

| 技能 | 版本 | 简介 | 结构 |
|---|---|---|---|
| [`commit-report`](./commit-report/) | 1.1 | Git 提交审阅门技能。执行"分析变更 → 匹配既有提交风格生成 commit 信息 → 展示变更总揽与提交信息供审阅 → 确认后提交（可选推送）"流程；内置三选项回应路径协议、敏感文件与大文件预警、执行通道降级（git 故障时经 GitHub API 单次提交，随附通用脚本）、完成后报告与安全边界（禁 force push、禁 --no-verify 等）。 | SKILL.md + scripts/ |
| [`design-doc-review`](./design-doc-review/) | 2.1.0 | 面向公开分发的通用设计文档审计技能。覆盖全篇审计、数值脚本核验、交叉引用完整性、提案先行、文档重构验证与同步校验；`references/` 保留按领域分层的通用模式与持续扩充的项目级陷阱目录（条数不写死，避免引用漂移）。 | SKILL.md + references/ |
| [`deploy-report`](./deploy-report/) | 1.0 | 部署审阅门技能。执行"变更盘点 → 部署方案审阅（变更总揽/步骤/备份与回滚路径/验证计划）→ 确认后执行上线 → 三档验收（基础/冒烟/回归）→ 完成报告"流程；部署档案驱动（gitignore 私有档案）、git/无 git 双轨兼容、失败不自动回滚、凭据零入库硬性边界（附发布前敏感自检清单）。 | SKILL.md + references/ |

## 目录结构

```
Siungo-Skills-Repository/
├── LICENSE
├── README.md
├── commit-report/
│   ├── SKILL.md                      # 技能主文件：审阅门流程、回应路径协议、安全边界
│   └── scripts/
│       └── push-via-api.py           # 降级推送脚本：git 直连故障时经 GitHub API 重建提交链
└── design-doc-review/
    ├── SKILL.md
    └── references/                   # 领域知识与模式参考（common/web/game 分层）
└── deploy-report/
    ├── SKILL.md                      # 技能主文件：部署审阅门流程、执行/验收/回滚、安全边界
    └── references/
        ├── deploy-profile.template.md # 部署档案字段模板（实例 gitignore，凭据指针式）
        ├── pitfalls-and-patterns.md   # 部署坑与模式库（原子替换/备份/构建/验证通道，脱敏）
        └── publish-check.md           # 发布前敏感信息自检清单
```

## License

[MIT](./LICENSE) © 2026 烧鹅濑
