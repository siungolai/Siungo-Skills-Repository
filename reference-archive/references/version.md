# reference-archive 修订记录

> 按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|

| 1.1.0 | 2026-11-19 | 三个纯标准库脚本修复 P1/P2：`html-to-markdown.py` 的 admonition 改状态栈以支持嵌套、代码围栏关闭前补换行、`urljoin` 还原相对/绝对链接、Markdown 正文转义、抓取只对瞬时错误重试且末次不 sleep、输出文件名校验防 `../` 逃逸；`check-links.py` 重写链接正则，支持 `<...>` 目标/嵌套括号/查询串/reference-style，剔除围栏与行内代码，跳过 mailto/data/ftp 等非本地 scheme；`snapshot-diff.py` 加 `--hash sha256`、跳过通配目录、符号链接断链保护。§7 安全边界补作用域说明：PR 通道内的开 PR/合并/推功能分支按 issue-pr-loop 默认授权执行。 |
| 1.0.0 | 2026-10-22 | 首次创建：把厂商文档站、上游仓库与发布资产固化成可离线查阅、可回溯的参考归档。含归档骨架规划、一手资料固化、四路交叉验证的硬件事实核对、增量对账流程、四项归档自检与安全边界；自带三个纯标准库脚本（`html-to-markdown.py` / `check-links.py` / `snapshot-diff.py`）；附 ESP32-S3-RLCD-4.2 实例。 |
