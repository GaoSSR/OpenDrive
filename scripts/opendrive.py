#!/usr/bin/env python3
"""OpenDrive - 驾驭 AI 开发流程的轻量校验脚本。

只做检查和记账，不修改用户代码、不做任何 git 写操作（baseline 的 commit 由
AI 或用户自己执行，脚本只打印建议命令）。

子命令:
  init       初始化 opendrive/ 目录结构
  status     当前阶段、任务勾选率、形态确认状态
  check      台账与证据对账（勾了没证据 / 有证据没勾 / 证据过期）
  drift      工作树改动 vs 当前任务声明的范围
  baseline   记录用户的"确认产品形态"口令（写入 shape.md 头部）
  log        追加一条带时间戳的决策/偏差记录到 opendrive/log.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT_MARK = "opendrive"
SHAPE = "shape.md"
TASKS = "tasks.md"
LOG = "log.md"
CHECKS = "checks"
CONFIRM_RE = re.compile(r"<!--\s*confirmed:\s*(.+?)\s*-->", re.S)
TASK_RE = re.compile(r"^\s*-\s*\[([ xX~\-]?)\]\s*(\d+\.\d+)\s*(.+)$")
SCOPE_RE = re.compile(r"<!--\s*scope:\s*(.+?)\s*-->")


def find_root() -> Path:
    """从 cwd 向上找 opendrive/ 或 .git，定位项目根。"""
    cur = Path.cwd()
    for p in [cur, *cur.parents]:
        if (p / ROOT_MARK).is_dir():
            return p
        if (p / ".git").exists():
            return p
    return cur


def od_dir(root: Path) -> Path:
    return root / ROOT_MARK


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def confirmed(shape_text: str) -> re.Match | None:
    return CONFIRM_RE.search(shape_text)


def parse_tasks(text: str):
    """返回 [(编号, 勾选?, 描述, scope列表)]。"""
    out = []
    current_scope: list[str] = []
    for line in text.splitlines():
        m = SCOPE_RE.search(line)
        if m:
            current_scope = [s.strip() for s in m.group(1).split(",") if s.strip()]
            continue
        m = TASK_RE.match(line)
        if m:
            mark, num, desc = m.group(1), m.group(2), m.group(3).strip()
            out.append((num, mark.lower() == "x", desc, list(current_scope)))
    return out


def git(*args: str, check: bool = False) -> str:
    try:
        r = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=10
        )
        if check and r.returncode != 0:
            return ""
        return r.stdout
    except Exception:
        return ""


def cmd_init(root: Path) -> int:
    d = od_dir(root)
    (d / CHECKS).mkdir(parents=True, exist_ok=True)
    if not (d / SHAPE).exists():
        (d / SHAPE).write_text(
            "# 产品形态说明\n\n"
            "<!-- 阶段一产出：用产品语言描述最终形态。 -->\n"
            "<!-- 用户说\"确认产品形态\"后，运行 opendrive.py baseline 冻结本文件。 -->\n\n"
            "## 入口与首屏\n\n## 页面与操作\n\n## 状态与反馈\n\n"
            "## 本期交付\n\n## 本期不交付\n\n## 与参考产品的对齐边界\n\n"
            "## 原生能力核查\n\n<!-- 硬规则 5：列出为目标平台/参考实现查了哪些原生能力、\n"
            "     哪些可直接复用、哪些才需要自建。没写这一节 = 没查过。 -->\n\n"
            "## 验收路径\n",
            encoding="utf-8",
        )
    if not (d / TASKS).exists():
        (d / TASKS).write_text(
            "# 任务台账\n\n"
            "<!-- 每个里程碑用 scope 注释声明本轮允许改动的路径前缀 -->\n\n"
            "## G1 <里程碑名>\n<!-- scope: src/, docs/ -->\n\n"
            "- [ ] 1.1 <任务> → 验证：<验证方式>\n",
            encoding="utf-8",
        )
    if not (d / LOG).exists():
        (d / LOG).write_text("# 决策与偏差记录\n", encoding="utf-8")
    print(f"✓ 已初始化 {d}")
    print("  下一步：阶段一 ALIGN —— 填写 shape.md，等用户说\"确认产品形态\"")
    return 0


def cmd_status(root: Path) -> int:
    d = od_dir(root)
    shape = read(d / SHAPE)
    tasks = parse_tasks(read(d / TASKS))

    c = confirmed(shape)
    print("== OpenDrive 状态 ==")
    if c:
        print(f"形态: 已冻结（{c.group(1).strip()}）")
    else:
        print("形态: ⚠ 未确认 —— 阶段一未完成，禁止写产品代码")

    if tasks:
        done = sum(1 for _, x, _, _ in tasks if x)
        print(f"任务: {done}/{len(tasks)} 已勾选")
        pending = [(n, desc) for n, x, desc, _ in tasks if not x]
        for n, desc in pending[:5]:
            print(f"  · 待办 {n}: {desc[:60]}")
    else:
        print("任务: 台账为空 —— 先拆任务再开发")
    return 0


def cmd_check(root: Path) -> int:
    d = od_dir(root)
    tasks = parse_tasks(read(d / TASKS))
    if not tasks:
        print("台账为空，无法对账"); return 1

    problems = 0
    checks_dir = d / CHECKS
    for num, ticked, desc, _ in tasks:
        evidence = checks_dir / f"{num}.md"
        if ticked and not evidence.exists():
            print(f"✗ {num} 已勾选但缺验证证据: checks/{num}.md —— {desc[:50]}")
            problems += 1
        elif ticked and evidence.exists():
            # 证据不为空
            if len(read(evidence).strip()) < 10:
                print(f"✗ {num} 证据文件近乎为空 —— checks/{num}.md")
                problems += 1
        if not ticked and evidence.exists():
            print(f"△ {num} 有证据但未勾选 —— 要么勾上，要么说明为什么不算完")
            problems += 1

    done = sum(1 for _, x, _, _ in tasks if x)
    if problems == 0:
        print(f"✓ 台账与证据一致（{done}/{len(tasks)} 已勾选且均有证据）")
    else:
        print(f"\n共 {problems} 处不一致 —— 修复后再继续")
    return 1 if problems else 0


def _current_scope(tasks_text: str) -> list[str]:
    """取最后一个未完成里程碑声明的 scope。"""
    groups = re.split(r"^##\s+", tasks_text, flags=re.M)
    for g in reversed(groups):
        if "- [x]" not in g or "- [ ]" in g:
            m = SCOPE_RE.search(g)
            if m:
                return [s.strip() for s in m.group(1).split(",") if s.strip()]
            return []
    return []


def cmd_drift(root: Path) -> int:
    tasks_text = read(od_dir(root) / TASKS)
    scope = _current_scope(tasks_text)
    changed = git("-C", str(root), "diff", "--name-only", "HEAD").splitlines()
    changed += git("-C", str(root), "ls-files", "--others", "--exclude-standard").splitlines()
    changed = [c for c in dict.fromkeys(changed) if c and not c.startswith(ROOT_MARK + "/")]

    if not changed:
        print("✓ 工作树干净，无漂移")
        return 0
    if not scope:
        print("⚠ 当前里程碑未声明 scope（在 tasks.md 里加 <!-- scope: path/ -->），无法判断漂移；以下改动请人工核对：")
        for c in changed:
            print(f"  ? {c}")
        return 1

    out = [c for c in changed if not any(c.startswith(s) for s in scope)]
    if out:
        print("✗ 以下改动超出当前里程碑声明的范围（scope）：")
        for c in out:
            print(f"  ✗ {c}")
        print("\n  要么这些改动属于当前任务（更新 scope），要么是范围蔓延（回退或停下报告）。")
        return 1
    print(f"✓ {len(changed)} 个改动均在当前 scope 内")
    return 0


def cmd_baseline(root: Path, quote: str) -> int:
    d = od_dir(root)
    shape_p = d / SHAPE
    text = read(shape_p)
    if not text.strip():
        print("✗ shape.md 为空 —— 先写产品形态说明"); return 1
    if confirmed(text):
        print("⚠ 已存在确认记录；如需重新冻结，先手动删除 shape.md 头部的 confirmed 注释")
        return 1
    # 硬规则 5 落点：原生能力核查一节必须有实质内容
    m = re.search(r"##\s*原生能力核查\s*\n(.*?)(?=\n##\s|\Z)", text, re.S)
    body = (m.group(1) if m else "").strip()
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
    if not m or len(body) < 20:
        print("✗ shape.md 缺少有实质内容的「原生能力核查」一节 —— 先查目标平台/参考实现的原生能力再冻结")
        return 1
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M %z")
    header = f"<!-- confirmed: {ts} | 用户原话: {quote} -->\n"
    shape_p.write_text(header + text, encoding="utf-8")
    print(f"✓ 形态已冻结（{ts}）")
    print("  建议立刻执行：")
    print(f'    git add {ROOT_MARK}/ && git commit -m "docs(opendrive): 冻结已确认的产品形态"')
    return 0


def cmd_log(root: Path, msg: str) -> int:
    d = od_dir(root)
    d.mkdir(exist_ok=True)
    log_p = d / LOG
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%m-%d %H:%M")
    with log_p.open("a", encoding="utf-8") as f:
        f.write(f"\n- [{ts}] {msg}")
    print(f"✓ 已记录到 {log_p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="opendrive", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("check")
    sub.add_parser("drift")
    p = sub.add_parser("baseline")
    p.add_argument("--quote", required=True, help="用户确认时的原话")
    p = sub.add_parser("log")
    p.add_argument("message")
    args = ap.parse_args()

    root = find_root()
    if args.cmd != "init" and not od_dir(root).is_dir():
        print(f"✗ 未找到 {ROOT_MARK}/ 目录，先运行: opendrive.py init")
        return 1

    return {
        "init": lambda: cmd_init(root),
        "status": lambda: cmd_status(root),
        "check": lambda: cmd_check(root),
        "drift": lambda: cmd_drift(root),
        "baseline": lambda: cmd_baseline(root, args.quote),
        "log": lambda: cmd_log(root, args.message),
    }[args.cmd]()


if __name__ == "__main__":
    sys.exit(main())
