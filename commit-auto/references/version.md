# commit-auto 修订记录

按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.4.1 | 2026-10-03 | 按 skill-authoring 规范对齐：章节号由中文数字改为阿拉伯数字（正文 `§三`／`§五` 引用同步改写，`references/exclusions.md` 的引用一并更新）；触发加载检查块改为环境中立句式（不再写死宿主工具名）；frontmatter 版本号补为三段式。 |
| 1.4 | 2026-09-25 | 修订记录从 `SKILL.md` §八 移出为独立文件（即本文件），SKILL.md 的定位行保留指针；章节由八节变为七节 |
| 1.3 | 2026-09-25 | 实战修订（技能仓库首次自主使用）：§三 明确路径一律用 `-z` 读取并以 `-LiteralPath` 校验、解析落空即中止；§五 凭据核对须覆盖全部路径且解析失败同样中止——修掉中文路径被八进制转义后静默漏扫的缺陷（实测漏掉 5 个中文名 ADR） |
| 1.2 | 2026-09-25 | 事实更正：commit-report／deploy-report 的 `disable-model-invocation` 实为 `false`（= 允许模型调用），据此重写 §四 读盘复用的理由（避免逐笔等待，而非「对方不可调用」）并同步 ADR-0001／ADR-0005 |
| 1.1 | 2026-09-25 | 实战修订（dsh-lan-web 首测）：§四 补 Windows 已知陷阱——`.git/COMMIT_EDITMSG` 带 Hidden 属性时 Git for Windows 报 Permission denied，`attrib -h` 后重试 |
| 1.0 | 2026-09-25 | 初版：会话级授权、功能完成信号四级判据、显式路径清单与垃圾排除、commit-report 读盘复用契约、硬红线、干跑模式 |
