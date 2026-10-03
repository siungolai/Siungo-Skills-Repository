# commit-report 修订记录

按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.3.1 | 2026-10-03 | 按 skill-authoring 规范对齐：章节号改阿拉伯数字；两个 H3 补编号（`### 3.1 第 1 区`／`### 3.2 第 2 区`）；`第六节 §6.4` 简化为 `§6.4`；触发加载检查块改为环境中立句式；版本号补为三段式。 |
| 1.3 | 2026-09-25 | 修订记录从 `SKILL.md` §八 移出为独立文件（即本文件），SKILL.md 的定位行保留指针；章节由八节变为七节 |
| 1.2 | 2026-09-25 | 实战修订（dsh-lan-web 实测）：§五 新增「已知执行故障（Windows）」——`.git/COMMIT_EDITMSG` 带 Hidden 属性时 Git for Windows 报 Permission denied，`attrib -h` 后重试；并记录伴随的 `.git` 内 `._*` 垃圾引发 non-monotonic index |
| 1.1 | 2026-09-07 | 实战修订：新增场景 B（本地领先上游的未推送提交审阅，两区模板）；触发加载检查（技能快照过期兜底）；push 前网络探测判定表；降级通道增强（中文/空格路径 -z、SHA 三重校验、tracking ref 同步）；随技能分发通用降级脚本 scripts/push-via-api.py；场景 B 历史提交改写边界（§6.6）；description 补充中文触发场景 |
| 1.0 | 2026-09-07 | 初版：强制审阅门流程（分析 → 审阅展示 → 确认 → 提交/推送） |
