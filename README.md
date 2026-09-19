# OpenDrive

驾驭 AI 完成中长程开发任务的工作流工具：**先对齐产品形态（用户说"确认产品形态"才冻结），再按台账小步交付，每个里程碑用产品语言回检漂移。**

为"人用 AI 写代码总是跑偏"这个问题而生：AI 理解的和你理解的不是同一个需求、OpenSpec 这类工具只校验文档格式不校验方向、任务勾选和代码完成度脱钩、多 Agent 共享工作树互相覆盖。OpenDrive 用三个机制堵住这些洞：

| 机制 | 堵哪个洞 |
|---|---|
| **确认口令 + baseline 冻结** | AI 把"继续/好的"当成确认，闷头开发 |
| **台账 ↔ 证据对账（check）** | 任务勾了没证据 / 代码写了没勾选，完成度无法审计 |
| **scope 漂移检测（drift）** | 实现悄悄超出当前任务范围，范围蔓延不可见 |

## 安装

```bash
bash scripts/install.sh
```

会软链到 `~/.codex/skills/opendrive` 和 `~/.claude/skills/opendrive`，Codex 用 `$opendrive`、Claude Code 用 `/opendrive` 调用。

## 三阶段工作流

```
ALIGN  ──确认口令──►  BUILD  ──里程碑──►  REVIEW  ──偏差──►  回到 ALIGN
(写 shape.md)      冻结    (台账+证据)      (产品语言汇报)
```

1. **ALIGN**：AI 用产品语言写 `opendrive/shape.md`（页面、操作、状态、交付与不交付、验收路径），等你说"确认产品形态"，然后 `baseline` 冻结。
2. **BUILD**：拆 `opendrive/tasks.md`，每个任务带验证方式；完成一个勾一个并写 `checks/` 证据；`check` 对账。
3. **REVIEW**：每个里程碑用产品语言汇报"现在能走通什么、和 shape.md 有什么偏差"，有偏差回到 ALIGN。

## 硬规则（写在 SKILL.md 第〇条）

确认口令（"继续"不算确认）、单一写入者、台账即真相、漂移即停、先查原生再动手（`shape.md` 必须有实质的「原生能力核查」节，`baseline` 才放行）、环境问题 15 分钟升级、跨仓/删除/改合同先报告、评审最多 2 轮且只有 P0 阻塞。

## 命令

```bash
python3 scripts/opendrive.py init      # 初始化 opendrive/
python3 scripts/opendrive.py status    # 阶段、勾选率、确认状态
python3 scripts/opendrive.py check     # 台账与证据对账
python3 scripts/opendrive.py drift     # 工作树改动 vs 当前 scope
python3 scripts/opendrive.py baseline --quote "用户原话"   # 冻结形态
python3 scripts/opendrive.py log "决策或偏差"              # 记一笔
```

脚本零依赖（Python 3.8+ 标准库），只读不写你的代码，git 写操作一律由人或 AI 显式执行。

## 迭代路线

未解决的问题和优化上下文见 [ROADMAP.md](ROADMAP.md)。

## 文件布局

```
OpenDrive/
├── SKILL.md                 # 工作流定义（两个 Agent 共用这一份）
├── scripts/
│   ├── opendrive.py         # 校验/记账脚本
│   └── install.sh           # 双 Agent 安装器
├── ROADMAP.md               # 未解决问题与迭代上下文
└── README.md
```
