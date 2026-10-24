# Siungo-Skills-Repository

> siungo 的个人 Skill 仓库 — 自建 AI 智能体技能定义与领域规范（SKILL.md + references），持续更新中。

![License](https://img.shields.io/badge/license-MIT-green) ![Skills](https://img.shields.io/badge/skills-8-blue)

## 简介

本仓库集中存放 [siungo](https://github.com/siungolai) 自建的智能体技能（Skills）。每个技能以独立文件夹组织，遵循 `SKILL.md` 规范（YAML 元数据 + 正文指令），可被 WorkBuddy 等支持该规范的智能体环境直接加载调用；细分的领域知识与配套脚本置于各技能的 `references/`、`scripts/` 子目录，按需加载，保持主文件精炼。

## 收录技能

| 技能 | 版本 | 简介 | 结构 |
|---|---|---|---|
| [`agent-team-setup`](./agent-team-setup/) | 1.0.0 | DSH 智能体团队配置器。执行「读盘探测项目事实 → 判定席位与写作范围 → 展示团队契约（席位表/任务图/验证计划/停止条件）供用户确认 → 才组建成员并在共享任务板派活 → 编排、停滞裁决与打回 → 报告后解散」流程；内置 `web` 网页开发团队预设（含各席位 spawn prompt 骨架与验证命令探测顺序），随附团队模型、改派与依赖边纪律、宿主能力与上限的事实表。 | SKILL.md + references/ + CONTEXT.md |
| [`commit-auto`](./commit-auto/) | 1.4.1 | 节奏驱动的自动提交技能。执行「授权判定 → 识别功能完成信号 → 切分提交范围（显式路径清单、垃圾排除）→ 读盘复用 commit-report 的审阅门生成并执行提交」流程；会话级授权一次覆盖整段节奏、不逐笔打断，push 不在范围内；内置硬红线（凭据零入库、破坏性 git 操作）与干跑模式；随附领域词汇表与 5 条 ADR。 | SKILL.md + references/ + CONTEXT.md + docs/adr/ |
| [`commit-report`](./commit-report/) | 2.0.0 | Git 提交审阅门技能。执行"托管与可见性判定 → 隐私扫描 → 分析变更 → 匹配既有提交风格生成 commit 信息 → 展示变更总揽与提交信息供审阅 → 确认后提交（可选推送）"流程；先分公共托管与私人托管、再分仓库是否私有，只有「私人托管 ＋ 私有仓库」才把隐私类命中降为提示，凭据类在任何托管下都硬阻断；内置两区审阅模板（已存在待推送提交链与本次待创建提交分开审）、四级分级闸门（🔴 凭据类与 🔴 隐私类/🟠 需确认/🟡 提示/🟢 放行，附正则清单与本机真实值复现）、三选项回应路径协议、敏感文件与大文件预警、执行通道降级（git 故障时经 GitHub API 重建提交链，随附通用脚本与三重 SHA 校验）、push 前重判托管、完成后报告与安全边界（禁 force push、禁 --no-verify、隐私零入库、审阅单禁贴真实隐私值）。 | SKILL.md + scripts/ + references/ |
| [`design-doc-review`](./design-doc-review/) | 2.2.0 | 面向公开分发的通用设计文档审计技能。覆盖全篇审计、数值脚本核验、交叉引用完整性、提案先行、文档重构验证与同步校验；`references/` 保留按领域分层的通用模式与持续扩充的项目级陷阱目录（条数不写死，避免引用漂移）。 | SKILL.md + references/ |
| [`deploy-report`](./deploy-report/) | 1.1.1 | 部署审阅门技能。执行"变更盘点 → 部署方案审阅（变更总揽/步骤/备份与回滚路径/验证计划）→ 确认后执行上线 → 三档验收（基础/冒烟/回归）→ 完成报告"流程；部署档案驱动（gitignore 私有档案）、git/无 git 双轨兼容、失败不自动回滚、凭据零入库硬性边界（附发布前敏感自检清单）。 | SKILL.md + references/ |
| [`esp32-firmware-bringup`](./esp32-firmware-bringup/) | 1.0.0 | ESP32 固件 bringup 与硬件诊断技能。执行「需求冻结 → 硬件事实采集（记录实测读数而非规格书参数）→ bringup 阻塞前置（地址应答 / 单路不互扰 / 拔外设节拍不漂移）→ 节拍与驱动实现（非阻塞 + 从机离线保护）→ 验收与长跑」流程；内置诊断阶梯（电源真值 → 万用表通断 → 总线静态电平 → 地址扫描 → 错误码判读 → 才看固件）、本机硬件速查（GPIO 禁脚 / 地址 / 上拉归属）、四份器件专项 reference、日志与凭据约定、安全边界（先接线后上电、5V 电平先量再连、不重复加上拉）。 | SKILL.md + references/ + CONTEXT.md |
| [`reference-archive`](./reference-archive/) | 1.0.0 | 官方资料参考归档技能。执行「规划归档骨架 → 固化一手资料（文档页转 Markdown + 图片本地化 + 上游仓库与发布资产镜像）→ 四路交叉核对硬件事实 → 官方更新后做增量对账 → 四项归档自检」流程；内置三档结论定级与不确定项纪律、位图接口表与原理图网表的还原方法、纯标准库脚本（网页转 MD / 链接与资源自检 / 目录树 sha1 对账）；随附 ESP32-S3-RLCD-4.2 实例与 2 份 ADR。 | SKILL.md + references/ + CONTEXT.md + docs/adr/ + scripts/ |
| [`skill-authoring`](./skill-authoring/) | 1.0.0 | 自建技能编写规范。新建或改造技能时执行「查重定界 → 定骨架 → 写 SKILL.md → 落 references → 自检（check-skills.py + publish-check）→ 同步到 ~/.dsh/skills/ → 更新 README 与版本表」流程；条文按「必须（M）/ 默认（D）/ 禁止（P）」逐条编号（见 `references/standard.md`），随附场景化自检清单、四份模板（SKILL.md / version.md / CONTEXT.md / ADR）与只读检查脚本；只管"规范"，不管"句子该怎么写"——那属于上游技能 `writing-for-agents`。 | SKILL.md + references/ + scripts/ |

## 目录结构

```
Siungo-Skills-Repository/
├── LICENSE
├── README.md
├── agent-team-setup/                 # 团队配置器：谁来做、各写哪些目录、按什么依赖边推进
│   ├── SKILL.md                      # 技能主文件：事实探测、契约展示、组建派活、编排与裁决、安全边界
│   ├── CONTEXT.md                    # 领域词汇表（席位/写范围/只读席位/团队契约/停滞/解散…）
│   └── references/
│       ├── team-model.md             # 团队模型：席位能力矩阵、写范围规则、任务链模板、spec 八段
│       ├── dsh-constraints.md        # 宿主事实表：上限、生成接口参数、任务板 action 语义、错误码
│       ├── presets/web.md            # web 预设：席位表、各席位 prompt 骨架、契约版式、验证命令探测
│       └── version.md                # 修订记录（版本历史，按时间倒序）
├── commit-auto/                      # 节奏层：变更以什么节奏进入仓库
│   ├── SKILL.md                      # 技能主文件：授权判定、完成信号、范围切分、红线、干跑
│   ├── CONTEXT.md                    # 领域词汇表（提交单元/提交节奏/功能完成信号/会话级授权…）
│   ├── references/
│   │   ├── exclusions.md             # 垃圾排除清单与硬红线判定（凭据形态、破坏性 git 操作）
│   │   └── version.md                # 修订记录（版本历史，按时间倒序）
│   └── docs/adr/                     # 决策记录 0001–0005（分层、会话授权、push 边界…）
├── commit-report/                    # 审阅门：变更能否进入仓库，按托管口径分级
│   ├── SKILL.md                      # 技能主文件：托管判定、隐私扫描、审阅门流程、两区模板、安全边界
│   ├── references/
│   │   ├── host-visibility.md        # 托管与可见性判定：公共清单、私人证据、匿名可读探测、URL 脱敏
│   │   ├── privacy-scan.md           # 隐私分级闸门：分级表、正则清单、扫描命令、误报豁免、钩子分工
│   │   └── version.md                # 修订记录（版本历史，按时间倒序）
│   └── scripts/
│       └── push-via-api.py           # 降级推送脚本：git 直连故障时经 GitHub API 重建提交链
├── design-doc-review/
│   ├── SKILL.md                      # 技能主文件：审计方法论、编写指南、通用陷阱、安全边界
│   └── references/
│       ├── common/pitfalls-catalog.md # 项目级陷阱库（持续扩充）
│       ├── game/game-patterns.md      # 游戏设计审计模式（数值平衡、可达性、经济闭环…）
│       ├── web/web-patterns.md        # Web 设计文档审计模式（配置一致性、API schema…）
│       └── version.md                 # 修订记录（版本历史，按时间倒序）
├── deploy-report/                    # 部署审阅门：变更何时进入线上
│   ├── SKILL.md                      # 技能主文件：部署审阅门流程、执行/验收/回滚、安全边界
│   └── references/
│       ├── deploy-profile.template.md # 部署档案字段模板（实例 gitignore，凭据指针式）
│       ├── pitfalls-and-patterns.md   # 部署坑与模式库（原子替换/备份/构建/验证通道，脱敏）
│       ├── publish-check.md           # 发布前敏感信息自检清单
│       └── version.md                 # 修订记录（版本历史，按时间倒序）
├── esp32-firmware-bringup/            # 固件层：规格书参数如何变成本机实测事实
│   ├── SKILL.md                      # 技能主文件：bringup 优先五步流程、诊断阶梯、硬件速查、安全边界
│   ├── CONTEXT.md                    # 领域词汇表（bringup/拓扑/节拍/从机/物理层/判读/离线保护…）
│   └── references/
│       ├── hardware-facts.md          # 本机硬件速查：板子、GPIO 禁脚、编译固定段、WS2812 判读、资源口径
│       ├── i2c-bus-cookbook.md        # I2C 总线手册：错误码判读、上拉归属、事务分块、5V 电平转换选型
│       ├── ssd1306-driver-notes.md    # SSD1306 驱动要点：显存布局、初始化序列、事务分块、字模方向
│       ├── sensor-protocol-notes.md   # 传感器协议要点：DHT11 时序、位判决自校准、错误码与物理故障对应
│       ├── display-multiplexer-notes.md # 多路复用与显示调度：PCA9548A 选通字节、STOP 生效、刷新分层
│       ├── diagnostic-tools.md        # 诊断工具台：七个工具用法、诊断阶梯六层、日志判读约定
│       └── version.md                 # 修订记录（版本历史，按时间倒序）
├── reference-archive/                 # 归档层：官方散落资料如何固化成可回溯的本地归档
│   ├── SKILL.md                      # 技能主文件：归档骨架、一手资料固化、事实交叉验证、增量对账、自检、安全边界
│   ├── CONTEXT.md                    # 领域词汇表（归档/原文存档/一手资料镜像/整理文档/出处标记/不确定项/对账…）
│   ├── references/
│   │   ├── archive-layout.md         # 归档骨架细则：目录职责、编号规则、文件头格式、索引必备五块、固件清单、镜像取舍
│   │   ├── cross-validation.md       # 交叉验证方法：四条取证路径各自怎么做、读图与网表的坑、结论定级、冲突处理
│   │   ├── scripts.md                # 三个脚本的用途、参数、已知局限与使用纪律
│   │   ├── rlcd-4.2-case.md          # 实例：一次真实归档的完整记录（五坑 + 对账实例 + 不确定项形态）
│   │   └── version.md                # 修订记录（版本历史，按时间倒序）
│   ├── scripts/
│   │   ├── html-to-markdown.py       # 文档站渲染页 → Markdown，图片本地化，站点常量外置到 JSON 配置
│   │   ├── check-links.py            # 归档自检：缺失引用 / 未引用资源 / 外链清单
│   │   └── snapshot-diff.py          # 目录树逐文件 sha1 对账：新增 / 删除 / 变更 / 无变化
│   └── docs/adr/                     # 决策记录 0001–0002（文件三分类互不混装、脚本只保留三个核心）
└── skill-authoring/                  # 规范层：自建技能怎么写
    ├── SKILL.md                      # 技能主文件：编写/改造流程、硬红线、自检与同步
    ├── references/
    │   ├── standard.md               # 条文全文（M 必须 / D 默认 / P 禁止，逐条编号）
    │   ├── checklist.md              # 场景化自检清单（新建 / 改造 / 发布前）
    │   ├── templates.md              # 四份模板（SKILL.md 骨架 / version.md / CONTEXT.md / ADR）
    │   ├── external-skills.md        # 仓库外技能台账（登记不受本规范管辖的技能）
    │   └── version.md                # 修订记录（版本历史，按时间倒序）
    └── scripts/
        └── check-skills.py           # 只读检查脚本：frontmatter / 引用 / 派生面 / README 一致性
```

## License

[MIT](./LICENSE) © 2026 烧鹅濑
