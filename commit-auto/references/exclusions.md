# 排除清单与红线判定

`SKILL.md` §3（范围切分）与 §5（硬红线）引用的核对清单。

## 一、永不纳入提交范围

| 模式 | 说明 |
|---|---|
| `._*`、`.DS_Store`、`__MACOSX/` | macOS AppleDouble 与 Finder 元数据 |
| `node_modules/`、`lib/`、`dist/`、`build/`、`.next/`、`target/`、`.venv/` | 依赖目录与构建产物 |
| `.scratch/`、`handoff-*.md`、`*.bak` | 会话临时目录与交接文档（多数仓库已在 `.gitignore` 中） |
| `*.log`、`*.tmp`、`*~`、`*.swp` | 日志与编辑器临时文件 |
| 单文件体积 >10MB 的二进制 | 误入库会永久污染历史，见红线 |

命中即从提交范围剔除，并计入「未纳入清单」。

## 二、凭据形态（红线：命中即中止）

**文件名**：`.env`、`.env.*`、`*.key`、`*.pem`、`*.p12`、`id_rsa*`、`id_ed25519*`、`credentials*`、`secrets*`，以及含 `token`／`secret`／`password` 的文件名。

**内容特征**（对将要纳入的文本文件抽样检查）：

- `-----BEGIN … PRIVATE KEY-----`
- `ghp_`、`github_pat_`、`sk-`、`AKIA`、`xoxb-` 等凭据前缀
- `(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['"]?[^\s'"]{8,}`

命中时的动作：中止提交，报告文件名与命中位置，然后交还用户处置——移出范围、改用环境变量、或另开一笔明确授权。

## 三、破坏性 git 操作（红线）

`git init`；删除文件（`rm`、`git rm`、`git clean`，含清理 `.git/` 内部垃圾）；`--no-verify`；force push；amend 或 rebase 已推送的提交；`reset --hard`；`checkout -- .`；以及任何会覆盖或丢弃工作内容的操作。

需要其中任一动作时：报告「属于硬红线范围」，等待用户另行显式指示。
