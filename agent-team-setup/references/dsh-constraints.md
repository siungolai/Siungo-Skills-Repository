# DSH 团队与任务板的宿主事实（dsh-constraints）

> 本文件是**宿主行为的事实源**：以下每条都是从 DSH 宿主实现（`app.asar`）里读出的事实，不是约定也不是偏好。技能正文与预设只引用结论；当宿主升级导致行为变化时，改这里并 bump 版本。
> 事实取自 bundle 行号（括号内为归档行号），便于升级后逐条复核。

## §1 Team 的形态

- **没有团队配置文件**，也不存在"组建团队"这个事件：任何普通运行时根节点**隐式**就是一支 Team 的 Lead，TeamId 等于该会话的 SessionId；持久状态从第一条成员、消息或任务记录开始（808461）。
- 可配的只有两个上限：`maxMembers` 与 `maxTasks`，默认 16 / 256（810457-810458、810477-810478），声明在提供 team 能力的 bundle 的 `cordis.patch.yml` 里（808118-808134）。
- **实例事实**：profile 里的 `cordis.patch.yml` 可能把上限压得比默认值低（常见做法是 `maxMembers: 8`）。**动手前先读当前 profile 的这个文件**，以实际值为准——按默认 16 算席位，会在生成第 9 个成员时被 `Team member limit 8 reached` 顶回来。
- 角色枚举只有 `lead` 与 `teammate` 两种（810142）——**没有** frontend / backend / reviewer 这类内置角色，角色差异 100% 靠 `prompt`。

## §2 成员生成接口

- 模型可见参数**只有** `name` / `description` / `prompt` / `context`（`fresh` 或 `fork`）（825874-825891）；**没有** `provider`、`model`、`reasoning_effort` 之类的覆盖参数——服务层 provider 由宿主注入（809345）。想给某个席位不同的模型或推理档位，此版本做不到。
- 名字规则：lower-kebab-case、≤64 字符、不能叫 `lead`、**在同一 Team 内永久不复用**（809492、809351）。成员被解散/移除后名字仍被占用，重开要用新名。
- 生成成员是 **Lead 专属动作**（809334），成员无法生成成员。

## §3 任务板

### 3.1 快照与并发

- 任务板是 CAS（compare-and-swap）快照式：每次变更都要带上 `expectedRevision`，过期报 `TEAM_TASK_STALE_REVISION`（808471）。变更成功统一是 `revision: current.revision + 1`（810409）。
- 前缀错误：任务不存在 `TEAM_TASK_NOT_FOUND`（810314）、快照过期（810315）、任务已删除 `TEAM_TASK_DELETED`（810316）。
- 越权：变更需要**调用者是 Lead 或该任务 owner**，否则 `TEAM_TASK_UNAUTHORIZED`（810320，错误文案 `task mutation requires its owner or Team Lead`）。
- 任务视图对外会**剥离 ownerId**（810450、1021162）——别指望从列表里直接读到 owner 字段，认领关系以你自己的记录与成员回报为准。

### 3.2 八个 action 的前置条件与副作用

| action | 前置条件 | 副作用 / 报错 |
|---|---|---|
| `create` | 无 Lead 门槛；**不接受 `blocked_by`** | 新建为 `pending`、无 owner（812813）。依赖边必须建完后用 `set_dependencies` 补 |
| `claim` | 他人未持有（否则 `TEAM_TASK_ALREADY_CLAIMED` 810325）、当前为 `pending` **且 ready**（否则 `TEAM_TASK_BLOCKED` 810326） | → `in_progress`，ownerId = 调用者（810324） |
| `release` | **仅 `in_progress`** | → `pending`，清 owner（810333） |
| `edit` | 只改 `subject` / `description` / `writeScopes`；三项全缺报 `TEAM_INVALID_ARGUMENT`（810343） | 只做字段替换（810341） |
| `set_dependencies` | 缺 `blocked_by` 报错；只做图校验 | 成环 `TEAM_TASK_CYCLE`（810234）、自环（810425）。**这是补依赖边的唯一途径**（810351） |
| `complete` | **仅 `in_progress`** | → `completed`，保留 owner（810359） |
| `reopen` | **仅 `completed`** | → `pending` **且清 owner**（810367、812920）——打回后原主必须重新 claim |
| `reassign` | **Lead-only**（`only the Team Lead can reassign tasks` / `TEAM_LEAD_REQUIRED` 810376）；仅 `pending` 或 `in_progress` | 省略 owner → unassign 回 `pending`（812929）；给 owner → `in_progress` + ownerId（812935） |
| `delete` | 被其他任务依赖时 `TEAM_TASK_HAS_DEPENDENTS`（810397）；不要求已完成 | → `deleted` 留 tombstone，不占 `maxTasks`（808471、810400） |

### 3.3 readiness

- **ready = 所有 `blockedBy` 已 completed**（809845）。
- readiness **只拦 `claim`，不会唤醒任何成员**（808471、809861）。依赖一满足，必须由 Lead 主动叫醒下游席位。
- `writeScopes` 是 workspace 相对前缀，**只对重叠发出告警、既不阻塞 claim 也不授权写入**（808471、809861）。写范围靠契约纪律，不靠机制。

## §4 等待与状态

- `wait_agent` 的返回只有 `{ timedOut: boolean }`（`TeamWaitResult` 1021166；工具 schema 825793）——**没有任何变更内容**，等到了什么必须再回读名册/任务板/邮箱。参数只有 `timeout_ms`（默认 30000 825969；窗口 10 秒 – 1 小时，越界报 `TEAM_INVALID_TIMEOUT` 808836）。
- 语义是等「**调用开始之后**」roster / 任务板 / 邮箱 / 在线状态的**边沿**（808475），并且**绝不唤醒成员**（808839、811223）。
- **没有活跃对等体时立即返回** `{ timedOut: false }` 并附 `NO_ACTIVE_PEER_MESSAGE`（825971-825975、825657）；活跃判定集合是 `ACTIVE_WAIT_STATUSES = { "running", "provisioning" }`（825656）。
- 因此 `inactive` 只表示"当前没有 turn 在执行"，**不代表任务完成或失败**（825655）。成员跑完一轮转 inactive、任务仍停在 in_progress，是最常见的停滞形态——必须配停滞处理（见 SKILL.md 的 §6.3）。
- 中断单个成员是 Lead 专属动作（809293）。

## §5 消息与可见性

- 邮箱可见性判据：`membership.role === "lead" || message.targetId === agent.id`（809589）。**Lead 看得到全部消息，每个 teammate 只看得到明确发给自己的消息。**
- teammate 要向 Lead 回报，只能显式 `send_message({ target: "lead" })`；广播式的"心照不宣"在这个模型里不存在。
- 权限不是靠工具清单区分的：九个团队工具的 schema 对 Lead 与 teammate 完全相同，权限在执行期判定（825438）。**Lead-only 只有三处**：生成成员（809334）、中断成员（809293）、改派任务（810376）。任务板的 create / list / get / update 四类工具 teammate 都能调，`create` 也没有 Lead 门槛——所以"谁建任务"是契约纪律，不是机制限制。

## §6 组队模式的副作用

- 启用 team 能力后，**普通子代理被禁用**：`Ordinary subagent delegation and overlapping global child controls are disabled; Workflow can still create fresh children.`（807875、807912）。
- 后果：上游 `code-review`（依赖并行子代理）与 `research`（后台代理）**在组队期间不可用**。所以组队模式下的审查必须由团队内的只读席位执行；未组队时仍按 `code-review` 走——这是 SKILL.md §1 分叉的原因。

## §7 技能加载与调用

- 用户可在输入框用 `/名字` token 调用 user-invocable 技能（1031858、1031900、1031934：只扫用户消息、按空白分隔）；`/` 菜单来自技能列表接口。
- 技能发现**只扫顶层** `<name>/SKILL.md` 或 `<name>.md`，嵌套的 `**/SKILL.md` 是 deliberate 的不发现（974789）。所以预设只能作为本技能目录内的 `references/` 材料，不能做成并列的独立技能。
- frontmatter 里宿主真正解析的是 `name` / `description`（必需）以及 `whenToUse` / `metadata` / `disable-model-invocation` / `user-invocable`；`userInvocable` 默认 true（975933-975934）。`version`、`last_updated`、`agent_created`、`author` 是**本仓库自己的规范**，宿主不读——它们服务于本仓库的版本纪律，不服务于宿主。
