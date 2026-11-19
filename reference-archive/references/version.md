# reference-archive 修订记录

> 按时间倒序。每条对应 `SKILL.md` frontmatter 里的 `version` 与 `last_updated`。

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.2.1 | 2026-11-19 | 去冗余：授权前提改指针式引用；六类问题机制与抓取节制压成指针；rlcd 案例统一 25/20 资产表述、「两处」改「三处」。 |

| 1.2.0 | 2026-11-19 | 修复审计 P0：`html-to-markdown.py` 的 `extract_article` 回退 `<article>` 时按实际起始标签配对，不再在首个 `</div>` 处截断正文；图片本地化保留查询串并编码进文件名避免同名覆盖、改用锚定 Markdown 目标替换避免污染无关 URL；未闭合 `<li>` 遇 `<p>` 补块断；ZERO_WIDTH 改为逐字符剥离。 |
| 1.1.0 | 2026-11-19 | 三个纯标准库脚本修复 P1/P2：`html-to-markdown.py` 的 admonition 改状态栈以支持嵌套、代码围栏关闭前补换行、`urljoin` 还原相对/绝对链接、Markdown 正文转义、抓取只对瞬时错误重试且末次不 sleep、输出文件名校验防 `../` 逃逸；`check-links.py` 重写链接正则，支持 `<...>` 目标/嵌套括号/查询串/reference-style，剔除围栏与行内代码，跳过 mailto/data/ftp 等非本地 scheme；`snapshot-diff.py` 加 `--hash sha256`、跳过通配目录、符号链接断链保护。§7 安全边界补作用域说明：PR 通道内的开 PR/合并/推功能分支按 issue-pr-loop 默认授权执行。 |
| 1.0.0 | 2026-10-22 | 首次创建：把厂商文档站、上游仓库与发布资产固化成可离线查阅、可回溯的参考归档。含归档骨架规划、一手资料固化、四路交叉验证的硬件事实核对、增量对账流程、四项归档自检与安全边界；自带三个纯标准库脚本（`html-to-markdown.py` / `check-links.py` / `snapshot-diff.py`）；附 ESP32-S3-RLCD-4.2 实例。 |
