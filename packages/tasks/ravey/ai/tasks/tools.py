"""任务规划工具集 —— 收集 / 拆分 / 估算 / 排期 / 持久化。

设计原则：
  1. 纯函数 + 无外部依赖，本地可跑、不需要 LLM
  2. 启发式兜底，规则也能产出合理结果
  3. 类型严格，参数和返回值全部结构化
  4. 幂等，同样输入产出同样结果
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


# ============================================================
# 启发式规则
# ============================================================

# 关键词 → 默认拆分模板
_SPLIT_TEMPLATES: dict[str, list[str]] = {
    "模块": ["需求评审", "接口设计", "后端实现", "前端实现", "联调测试", "灰度发布"],
    "接口": ["DDL/Schema 设计", "服务层实现", "Controller 实现", "单元测试", "联调"],
    "页面": ["设计稿确认", "前端骨架", "组件实现", "联调对接", "视觉走查"],
    "bug": ["复现", "定位", "修复", "回归测试"],
    "迁移": ["评估影响面", "备份", "执行迁移", "验证", "回滚预案"],
    "优化": ["基线测量", "定位瓶颈", "实施优化", "效果验证"],
}

# 关键词 → 估工时（小时）
_EFFORT_RULES: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"评审|review", re.I), 1.0),
    (re.compile(r"设计稿|设计", re.I), 4.0),
    (re.compile(r"接口.*设计|schema|ddl", re.I), 3.0),
    (re.compile(r"实现|开发|编码", re.I), 8.0),
    (re.compile(r"单测|单元测试", re.I), 2.0),
    (re.compile(r"联调", re.I), 4.0),
    (re.compile(r"测试|qa|回归", re.I), 4.0),
    (re.compile(r"发布|上线|灰度", re.I), 2.0),
    (re.compile(r"修复|fix", re.I), 4.0),
    (re.compile(r"复现|定位", re.I), 2.0),
    (re.compile(r"备份|迁移", re.I), 3.0),
]

_DEFAULT_EFFORT_HOURS = 4.0


# ============================================================
# ① 收集：从自然语言提取原始任务
# ============================================================

_BULLET_RE = re.compile(r"^\s*[-*•]\s+(.+)$", re.MULTILINE)
_NUMBERED_RE = re.compile(r"^\s*\d+[.)、]\s*(.+)$", re.MULTILINE)
_SENTENCE_SPLIT = re.compile(r"[。；;\n]+")


def parse_requirement(text: str) -> list[dict]:
    """从自然语言需求中提取原始任务列表。

    策略（按优先级）：
      1. 识别 markdown bullet / 编号列表
      2. 都没有则按中英文句子分割符切分
      3. 过滤掉长度 < 4 的碎片
      4. 给每个任务生成稳定 ID

    Args:
        text: 用户输入的需求文本

    Returns:
        原始任务列表：[{id, title, description}]
    """
    if not text or not text.strip():
        return []

    bullets = [m.group(1).strip() for m in _BULLET_RE.finditer(text)]
    if not bullets:
        bullets = [m.group(1).strip() for m in _NUMBERED_RE.finditer(text)]

    if not bullets:
        bullets = [s.strip() for s in _SENTENCE_SPLIT.split(text) if len(s.strip()) >= 4]

    results: list[dict] = []
    seen: set[str] = set()
    for title in bullets:
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        tid = "task-" + str(abs(hash(title)))[:8]
        results.append({"id": tid, "title": title, "description": ""})

    return results


# ============================================================
# ② 拆分：按模板把一个任务展开成子任务
# ============================================================

def split_task(task: dict, max_subtasks: int = 6) -> dict:
    """按领域模板把一个任务拆成子任务列表。

    Args:
        task: 要拆分的任务 dict（至少包含 id, title）
        max_subtasks: 最多产生多少个子任务

    Returns:
        带 subtasks 字段的新 dict（不修改入参）。无匹配模板时 subtasks=[]。
    """
    title = task.get("title", "")
    matched_template: list[str] | None = None

    for keyword, template in _SPLIT_TEMPLATES.items():
        if keyword in title:
            matched_template = template
            break

    subtasks: list[dict] = []
    if matched_template:
        for step in matched_template[:max_subtasks]:
            sub_title = f"{step} - {title}"
            subtasks.append({
                "id": "task-" + uuid.uuid4().hex[:8],
                "title": sub_title,
                "description": f"{title} 的 {step} 阶段",
                "hours": 0.0,
                "priority": task.get("priority", "P2"),
                "depends_on": [],
                "start_date": None,
                "due_date": None,
                "subtasks": [],
            })

    result = dict(task)
    result.setdefault("hours", 0.0)
    result.setdefault("priority", "P2")
    result.setdefault("depends_on", [])
    result.setdefault("start_date", None)
    result.setdefault("due_date", None)
    result["subtasks"] = subtasks
    return result


# ============================================================
# ③ 估算：为叶子任务估工时
# ============================================================

def estimate_effort(task: dict) -> dict:
    """递归为任务树估工时。

    叶子节点按规则匹配；父节点 hours = 子任务之和。
    """
    result = dict(task)
    result["subtasks"] = [estimate_effort(s) for s in task.get("subtasks", [])]

    if result["subtasks"]:
        result["hours"] = round(sum(s["hours"] for s in result["subtasks"]), 1)
    else:
        title = result.get("title", "")
        hours = _DEFAULT_EFFORT_HOURS
        for pattern, h in _EFFORT_RULES:
            if pattern.search(title):
                hours = h
                break
        result["hours"] = hours

    return result


# ============================================================
# ④ 排期：沿工作日历分配 start_date / due_date
# ============================================================

def _parse_date(s: str | None) -> date:
    if not s:
        return date.today()
    return datetime.fromisoformat(s).date()


def _next_workday(d: date, holidays: set[date]) -> date:
    """返回 d 起第一个非周末、非假期的日期（含当天）。"""
    while d.weekday() >= 5 or d in holidays:
        d += timedelta(days=1)
    return d


def _advance_by_hours(
    current: date,
    hours_remaining: float,
    work_hours_per_day: float,
    holidays: set[date],
) -> tuple[date, float]:
    """从 current 起推进 hours_remaining 工时，返回 (截止日, 当天已用工时)。"""
    current = _next_workday(current, holidays)
    day_used = 0.0
    while hours_remaining > 0:
        capacity = work_hours_per_day - day_used
        if hours_remaining <= capacity:
            day_used += hours_remaining
            hours_remaining = 0
            return current, day_used
        hours_remaining -= capacity
        current = _next_workday(current + timedelta(days=1), holidays)
        day_used = 0.0
    return current, day_used


def schedule_tasks(
    task_tree: list[dict],
    start_date: str | None = None,
    work_hours_per_day: float = 6.0,
    holidays: list[str] | None = None,
) -> list[dict]:
    """按工作日历为任务树分配起止日期。

    规则：
      - 叶子任务按 hours / work_hours_per_day 推进
      - 父任务的 start_date = 首个子任务的 start_date
      - 父任务的 due_date = 末个子任务的 due_date
      - 跳过周末和 holidays
      - 同级任务串行排期

    Args:
        task_tree: 已估算工时的任务列表
        start_date: 起始日期（ISO 格式，默认今天）
        work_hours_per_day: 每日有效工时
        holidays: 节假日 ISO 字符串列表

    Returns:
        带 start_date / due_date 填充的新任务列表
    """
    holiday_set: set[date] = set()
    for h in holidays or []:
        holiday_set.add(_parse_date(h))

    cursor = _parse_date(start_date)
    day_used_carry = 0.0

    def _walk(node: dict) -> tuple[dict, date, date]:
        nonlocal cursor, day_used_carry
        result = dict(node)

        if node.get("subtasks"):
            new_subs = []
            first_start: date | None = None
            last_end: date | None = None
            for sub in node["subtasks"]:
                new_sub, s, e = _walk(sub)
                new_subs.append(new_sub)
                if first_start is None:
                    first_start = s
                last_end = e
            result["subtasks"] = new_subs
            result["start_date"] = first_start.isoformat() if first_start else None
            result["due_date"] = last_end.isoformat() if last_end else None
            return result, first_start or cursor, last_end or cursor

        # 叶子任务
        hours = float(node.get("hours", _DEFAULT_EFFORT_HOURS))
        start = _next_workday(cursor, holiday_set)
        remaining_today = work_hours_per_day - day_used_carry
        if remaining_today <= 0:
            start = _next_workday(start + timedelta(days=1), holiday_set)
            day_used_carry = 0.0
            remaining_today = work_hours_per_day

        if hours <= remaining_today:
            due = start
            day_used_carry += hours
            if day_used_carry >= work_hours_per_day:
                cursor = _next_workday(start + timedelta(days=1), holiday_set)
                day_used_carry = 0.0
            else:
                cursor = start
        else:
            hours -= remaining_today
            due, day_used_carry = _advance_by_hours(
                _next_workday(start + timedelta(days=1), holiday_set),
                hours,
                work_hours_per_day,
                holiday_set,
            )
            if day_used_carry >= work_hours_per_day:
                cursor = _next_workday(due + timedelta(days=1), holiday_set)
                day_used_carry = 0.0
            else:
                cursor = due

        result["start_date"] = start.isoformat()
        result["due_date"] = due.isoformat()
        result["subtasks"] = []
        return result, start, due

    scheduled = []
    for t in task_tree:
        new_t, _, _ = _walk(t)
        scheduled.append(new_t)
    return scheduled


# ============================================================
# ⑤ 持久化
# ============================================================

def save_task_tree(task_tree: list[dict], output_path: str) -> str:
    """把任务树写到 JSON 文件。

    Args:
        task_tree: 任务树
        output_path: 输出路径

    Returns:
        写入的绝对路径
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(task_tree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path.resolve())


# ============================================================
# 便捷入口：一键端到端规划（无 LLM，纯本地）
# ============================================================

def plan_end_to_end(
    requirement: str,
    start_date: str | None = None,
    work_hours_per_day: float = 6.0,
    holidays: list[str] | None = None,
) -> list[dict]:
    """端到端本地规划，串起 5 个工具。

    主要用途：
      - 单元 / 集成测试
      - 离线数据回放
      - 给 Agent 做 few-shot 示范时生成参考答案
    """
    raw = parse_requirement(requirement)
    split = [split_task(t) for t in raw]
    estimated = [estimate_effort(t) for t in split]
    scheduled = schedule_tasks(
        estimated,
        start_date=start_date,
        work_hours_per_day=work_hours_per_day,
        holidays=holidays or [],
    )
    return scheduled


# ============================================================
# Hand 注册：把上面的纯函数包装成给 Brain 用的工具
# ============================================================

def build_hands() -> dict[str, Any]:
    """返回 {tool_name: LocalHand} 字典，供 Brain 注入。"""
    from ravey.ai.agent_framework.hands import LocalHand

    return {
        "parse_requirement": LocalHand(parse_requirement, tags=["planner"]),
        "split_task": LocalHand(split_task, tags=["planner"]),
        "estimate_effort": LocalHand(estimate_effort, tags=["planner"]),
        "schedule_tasks": LocalHand(schedule_tasks, tags=["planner"]),
        "save_task_tree": LocalHand(save_task_tree, tags=["planner"]),
    }
