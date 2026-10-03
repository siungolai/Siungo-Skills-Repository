# 预设：web（网页开发团队）

> 本文件是 v1 唯一预设的落地物：把 [`../team-model.md`](../team-model.md) 的席位/写范围/任务链模型落成可直接照抄的席位表、prompt 骨架与契约版式。
> 通用规则不在这里重复；宿主机制与错误码见 [`dsh-constraints.md`](dsh-constraints.md)。

## §1 判定分支：网页项目事实上场时怎么裁

1. **默认五席**：`lead`（用户）+ `web-planner` + `web-frontend` + `web-backend` + `web-reviewer`（只读）。
2. **裁开发席**：纯前端项目（静态站、组件库、仅对接既有 API）裁 `web-backend`；纯后端项目（无 UI 交付）裁 `web-frontend`。裁掉一侧后任务链只留一条实现分支。
3. **裁 `web-planner`**：用户已给现成 spec、或需求一句话能穷尽时裁掉，直接进构建——省掉一轮访谈往返。
4. **可选槽最多开一个**：有数据库/schema 变更开 `web-data`；交付物必须含用户文档开 `web-docs`。**开两个会撞上成员上限**（默认五席 + 2 = 7，含 Lead 正好触顶，上限读法见 [`dsh-constraints.md`](dsh-constraints.md) 的 §1）；确需第三个交付面时，把 `web-docs` 的活派给 `web-planner` 或由 Lead 自己写。
5. **不组队**：改动只有一个文件、单点 bug、纯文案调整，或不是开发任务 → 说明理由后按常规流程直接做。

## §2 席位表

| 席位 | 职责 | 写范围（逐个目录点名） | 只读 |
|---|---|---|---|
| `lead`（用户本人） | 契约、共享文件、裁决、验收 | 共享文件：依赖清单与 lock、构建与 lint 配置、`README`、入口文件 | 否 |
| `web-planner` | 需求访谈的执笔人：按 Lead 主持的访谈产出 spec | 项目文档目录（`docs/spec/`、`docs/adr/`、`CONTEXT.md`） | 否（不写代码） |
| `web-frontend` | 前端交付面：页面、组件、样式、前端状态 | 前端源码目录（如 `src/client/`、`src/components/`、`app/`） | 否 |
| `web-backend` | 后端交付面：接口、业务逻辑、服务端校验 | 后端源码目录（如 `src/server/`、`api/`、`server/`） | 否 |
| `web-reviewer` | 独立验证：复跑命令、逐条判定验收标准 | 无（不写任何文件，结论只进报告） | **是** |
| `web-data`（可选） | 数据层：迁移、种子、schema | 迁移与 schema 目录（如 `migrations/`、`prisma/`、`db/`） | 否 |
| `web-docs`（可选） | 面向用户的文档 | 用户文档目录（如 `docs/guide/`） | 否 |

**逐目录点名**：写范围必须是探测到的真实目录，不是"前端相关文件"。若项目里前后端同处一个目录（如 `src/` 下混放），先按文件类型或子目录画出可切的分界（`src/pages/` vs `src/api/`），画不出来就说明这个项目不适合双开发席并行——裁到"一开发席 + 审查席"。

**共享文件归属（固定归 Lead）**：依赖清单与 lock（`package.json` / `pnpm-lock.yaml` / `package-lock.json` / `requirements.txt` / `go.mod`）、构建与静态检查配置（`tsconfig.json`、`vite.config.*`、`next.config.*`、`.eslintrc*`）、`README.md`、入口文件（`index.html`、`main.ts`、`app.py`）。两个席位都要动同一个文件时，先问这个文件该不该拆，不能拆就收归 Lead 串行改。

## §3 席位 prompt 骨架

每个席位的 `prompt` 必须缝进五件事：**席位名与职责**、**写范围（逐个目录点名）**、**该认领的任务 ID**、**验证命令**、**回报方式**。以下是骨架，`<…>` 落地时必须替换。

**`web-planner`**

```
你是「<项目名>」本次功能的 web-planner。职责：把 Lead 与用户访谈敲定的需求落成需求文档，不写代码、不切任务、不上任务板。
写范围：仅 <文档目录>（spec 落 <docs/spec/feature.md>；词汇表落 <CONTEXT.md>；决策记录落 <docs/adr/>）。
需求澄清的追问由 Lead 面向用户进行——你无法与用户直接对话，需要澄清时把问题列给 lead。
任务：认领任务 <spec 任务 ID>。
完成判据：需求文档八段齐全（见 references/team-model.md 的 §4），验收标准逐条可判真假，任务草图只写进文档。
回报：完成后用显式消息发给 lead，内容为文档路径 + 八段自检结果 + 待澄清问题（没有写「无」）。
```

**`web-frontend`（`web-backend` 同构，替换交付面与目录）**

```
你是「<项目名>」本次功能的 web-frontend。职责：交付前端侧改动。
写范围：仅 <前端源码目录 1>、<前端源码目录 2>。**不碰**共享文件（依赖清单、构建与 lint 配置、README、入口文件）——需要改它们时停下，把需求发给 lead。
验证命令：<探测到的 lint / test / build 命令>。完成后必须实际跑过并附输出摘要。
任务：认领任务 <impl-front 任务 ID>（依赖 spec 任务）；完成后用显式消息发给 lead，内容为改动文件清单 + 验证命令与实测结果 + 未解决项。
越界处置：发现必须改别人地盘才能完成时，停下并回报 lead，不先斩后奏。
```

**`web-reviewer`（只读）**

```
你是「<项目名>」本次功能的 web-reviewer，只读席位。职责：独立判定交付是否满足验收标准。
禁止：不写任何文件、不改代码、不删任务、不代任何席位修 bug。
判据来源：需求文档 <spec 路径> 的验收标准，逐条判定「过 / 不过 / 无法判定」，每条附证据（命令、输出摘要、文件与行号）。
独立复跑：<探测到的验证命令>，用自己的调用复跑一遍，不采信他人贴的结果。
任务：认领任务 <verify 任务 ID>（依赖 impl-front 与 impl-back）。
结论：任意一条「不过」→ 用 reopen 打回对应的实现任务（并列出未过条目），报告仍显式发给 lead；全过 → complete 并把报告发给 lead。
超出契约范围的意见只写进报告的遗留项，不作为打回理由。
```

**回报方式**：席位之间**看不到彼此的消息**（邮箱私有），所以每份报告的收件人必须显式写 `lead`；不写就等于没有回报通道。

## §4 契约版式（展示模板）

八项按此顺序排列，没有的项写「无」：

```
## 团队契约：<功能名>

1. 需求摘要
   目标：<一句话>
   判据来源：<现存 spec 路径> 或「由 web-planner 产出」

2. 席位表
   | 席位 | 角色 | 职责 | 写范围 | 只读 |
   （内容取自 §2，逐目录点名）

3. 共享文件归属（Lead 独占）
   <依赖清单 / 构建与 lint 配置 / README / 入口文件>

4. 任务图
   spec       ← web-planner   无依赖            判据：<…>
   impl-front ← web-frontend  依赖 spec         判据：<…>
   impl-back  ← web-backend   依赖 spec         判据：<…>
   verify     ← web-reviewer  依赖 impl-front, impl-back   判据：逐条判定验收标准

5. 验证计划
   <命令>（来自 <读盘来源>）—— 由 web-reviewer 独立复跑

6. 边界与停止条件
   本次只做一个 ticket；verify 完成即解散团队；组队期间普通子代理被禁用，
   上游 code-review 与 research 在此模式下不可用。

7. 开放问题
   <需要用户拍板的点> / 无

8. 回应路径
   ① 确认组建（按契约执行，范围外不做任何操作）
   ② 需要调整（改席位 / 改写范围 / 改任务链 / 其他）
   ③ 取消本次组队
```

## §5 验证命令探测顺序

**命令必须来自读盘，不许猜**。按此顺序找，取第一个成立的来源；三类命令（测试 / 静态检查 / 构建）各自独立探测，项目里没有的类别写「无」：

1. `package.json` 的 `scripts`（`test` / `lint` / `typecheck` / `build`）→ 用项目声明的包管理器执行（有 `pnpm-lock.yaml` 用 `pnpm`、有 `yarn.lock` 用 `yarn`、只有 `package-lock.json` 用 `npm`）；
2. `Makefile` / `justfile` / `Taskfile.yml` 的目标；
3. `pyproject.toml`（`pytest`、`ruff`、`mypy` 的配置节）与 `tox.ini`、`setup.cfg`；
4. `go.mod`（`go test ./...`、`go vet ./...`）、`Cargo.toml`（`cargo test`、`cargo clippy`）；
5. CI 配置：`.github/workflows/*.yml`、`.gitlab-ci.yml`、`.circleci/config.yml`——**这里最接近真实门禁**，CI 里跑的命令就是团队该跑的命令；
6. 项目自述文档（`README.md`、`AGENTS.md`、`CONTRIBUTING.md`）里写明的命令。

三条纪律：

- 命令与实际脚本名逐字一致，不"顺手规范化"（脚本叫 `check` 就不要写成 `lint`）。
- 探测到的命令要在契约 §5 里注明来源（哪个文件、哪一节），便于用户发现探测错误。
- 没有任何验证命令的项目，验证计划写「人工核对验收标准」并由 `web-reviewer` 逐条执行——**不得省略验证环节**。
