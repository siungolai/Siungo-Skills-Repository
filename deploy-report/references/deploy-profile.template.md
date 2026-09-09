# 部署档案模板（deploy-profile）

> 本文件是 **deploy-report** 技能的字段模板。用法：复制到目标项目根目录（命名 `deploy-profile.md` 或按项目私有命名约定），逐字段填写，并把档案文件加入 `.gitignore` / 排除出版本控制。**档案可能含凭据，任何情况下不得提交或分发**；发布任何文件前先跑 `publish-check.md` 自检。
>
> 凭据推荐"指针式"存放：档案内只写来源（环境变量名 / 私有文件路径），不写字面值。

## 字段模板（复制以下内容到项目档案，删除本段说明）

```markdown
# 部署档案：<项目名>

> 本文件为私有部署档案，含连接信息，禁止提交/分发（已 gitignore）。

## 一、项目标识
- name: <项目名，如 my-site>
- site_url: <公网访问地址，如 https://www.example.com>      # 验证用基础 URL，可公开
- server_host: <域名或主机别名>                              # 凭据指针：实际地址可只写别名/私有文件
- creds_source: <环境变量名 或 私有文件路径>                  # 凭据来源指针，禁止字面量凭据

## 二、执行通道（如何跑远端命令 / 如何上传）
- exec_channel: <描述，如 `node .ssh-tool/ssh-exec.js "<cmd>"` 或 ssh 别名>
- upload_channel: <描述，如 `<工具> --sftp-upload <本地> <远端>` 或 rsync/scp 用法>
- channel_note: <本机工具限制与替代通道，如本机 curl 对 HTTPS 受限 → 用 Node https 验证>

## 三、本地构建
- build_cmd: <构建命令，如 `npm run build` / `go build -o server .`>
- build_dir: <产物目录，如 dist/ 或二进制文件名>
- test_cmd: <本地测试命令；无则留空>
- build_mode: local | on_server        # 本地构建 or 服务器构建（CGO/动态链接类选 on_server）
- build_note: <缓存/环境变量等注意点>

## 四、服务器布局
- app_type: static | service           # 纯静态站 or 常驻服务（后端）
- deploy_root: <部署根目录，如 /var/www/<app>>
- app_dir: <现役目录/文件路径>
- data_dir: <数据目录（数据库/上传等，活动文件绝不覆盖），如 /var/www/<app>/data>
- service_name: <systemd 服务名；静态站可留空>
- service_user: <服务属主，如 www-data>
- reload_cmd: <如 `systemctl restart <svc>` / `nginx -t && nginx -s reload`>
- nginx_conf: <nginx 站点配置路径（如需检查）>
- strict_service: true | false         # systemd 强隔离（ProtectSystem=strict 等）→ 注意 ReadWritePaths/属主

## 五、备份与回滚
- backup_dir: <服务器备份目录，如 /root/<app>-deploy-bak>
- retention: 3                          # 备份保留份数（默认 3）
- backup_extra: <数据目录额外备份规则，如 tar 数据目录留 .bak>

## 六、验证计划
- default_tier: T2                      # T1 基础 / T2 冒烟（默认）/ T3 回归（需批准）
- smoke_paths:                          # 冒烟清单：每行 路径 | 期望状态 | 说明
  - / | 200 | 首页
  - /api/v1/health | 200 | 健康检查
- asset_checks: <产物 MIME/缓存头等检查点，如 image/webp 可访问>
- async_checks: <需轮询完成态的任务，如批量重建类；提交 2xx ≠ 完成>
- regression_doc: <T3 回归依据的验收清单文档路径；无则留空>

## 七、项目备注
- known_pitfalls: <本项目特有的坑（私有，可含路径细节，勿外泄）>
- last_deploy: <上次部署标识：commit sha 或产物时间戳；每次部署后更新>
```

## 虚构示例（骨架参考，字段含义见上）

```markdown
# 部署档案：my-site
- name: my-site
- site_url: https://www.example.com
- server_host: prod-server             # 实际主机在 creds_source 私有文件中
- creds_source: %DEPLOY_CREDS%         # 环境变量，或项目内 gitignore 文件
- exec_channel: node .ssh-tool/ssh-exec.js "<cmd>"
- upload_channel: node .ssh-tool/ssh-exec.js --sftp-upload <local> <remote>
- build_cmd: npm run build
- build_dir: dist/
- build_mode: local
- app_type: static
- deploy_root: /var/www/my-site
- app_dir: /var/www/my-site
- data_dir: （无）
- reload_cmd: nginx -t && nginx -s reload
- backup_dir: /root/my-site-deploy-bak
- retention: 3
- default_tier: T2
- smoke_paths:
  - / | 200 | 首页
  - /assets/app.js | 200 | 产物可访问
- last_deploy: 2026-09-09T12:00:00
```

## 使用守则

1. 档案实例 = 私有文件：加入 `.gitignore`（`deploy-profile.md` 或实际命名），用 `git status` 确认不会进入提交列表（`git check-ignore <file>` 应返回该文件）。
2. 凭据字段一律指针式（环境变量名/私有文件路径），不写字面密码/token/key。
3. 项目部署记录（何时部署了什么、回滚过没有）建议另存于私有部署记录文档或档案 `last_deploy` 字段，作为无 git 项目的线上基线。
4. 字段按项目裁剪：纯静态站可删除 service_name/service_user/strict_service；无数据目录可删除 data_dir/backup_extra。
