# Siungo-Skills-Repository

> siungo 的个人 Skill 仓库 — 自建 AI 智能体技能定义与领域规范（SKILL.md + references），持续更新中。

![License](https://img.shields.io/badge/license-MIT-green) ![Skills](https://img.shields.io/badge/skills-2-blue)

## 简介

本仓库集中存放 [siungo](https://github.com/siungolai) 自建的智能体技能（Skills）。每个技能以独立文件夹组织，遵循 `SKILL.md` 规范（YAML 元数据 + 正文指令），可被 WorkBuddy 等支持该规范的智能体环境直接加载调用；细分的领域知识置于各技能的 `references/` 子目录，按需加载，保持主文件精炼。

## 收录技能

| 技能 | 简介 | 结构 |
|---|---|---|
| [`hk-gov-correspondence`](./hk-gov-correspondence/) | 香港特区政府中文公函（书信类公文）写作规范（简体中文版）。依据公务员事务局法定语文事务部《政府公文写作手册（第三版）·公函》蒸馏而成，涵盖格式组件、称谓规则、行文原则、公务电邮与致内地机关函件规范；内置语言强制规则（一律简体输出）与调用与语体约束（生活化提问的公文式回复、回复型公文最小要素集）。 | SKILL.md + 6 个参考文件 |
| [`commit-report`](./commit-report/) | Git 提交审阅门技能。执行"分析变更 → 匹配既有提交风格生成 commit 信息 → 展示变更总揽与提交信息供审阅 → 确认后提交（可选推送）"流程；内置三选项回应路径协议、敏感文件与大文件预警、执行通道降级（git 故障时经 GitHub API 单次提交）、完成后报告与安全边界（禁 force push、禁 --no-verify 等）。 | SKILL.md |

## 目录结构

```
Siungo-Skills-Repository/
├── LICENSE
├── README.md
├── hk-gov-correspondence/
│   ├── SKILL.md                      # 技能主文件：核心原则、执行流程、输入/输出定义、强制规则
│   └── references/
│       ├── format-spec.md            # 横式公函 14 组件 / 直式公函 / 信封 / 联署信
│       ├── address-terms.md          # 称谓用语全表
│       ├── mainland-notes.md         # 致内地政府单位公函 8 项注意事项
│       ├── email-notes.md            # 公务电邮结构与 11 项注释
│       ├── common-phrases.md         # 公函常见用语（中英对照精选）
│       └── examples-index.md         # 原书 107 例分类索引
└── commit-report/
    └── SKILL.md                      # 技能主文件：审阅门流程、回应路径协议、安全边界
```

## License

[MIT](./LICENSE) © 2026 烧鹅濑

技能正文蒸馏自香港公务员事务局法定语文事务部《政府公文写作手册（第三版）·公函》，原书版权归原机构所有；本仓库内容仅作个人学习与写作辅助用途。
