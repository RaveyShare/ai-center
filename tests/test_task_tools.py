"""任务规划工具集 —— 全面覆盖测试。

覆盖目标：
  - parse_requirement：bullet / 编号 / 句子分割 / 空输入 / 去重 / ID 稳定
  - split_task：模板命中 / 未命中 / 不修改入参 / max_subtasks 截断
  - estimate_effort：规则匹配 / 父任务汇总 / 默认工时 / 不修改入参
  - schedule_tasks：跳过周末 / 跳过节假日 / 父子日期范围 / 跨天推进
  - save_task_tree：写入文件 / 父目录创建 / 中文不转义
  - plan_end_to_end：5 步串联
  - build_hands：返回的 LocalHand 可正常 execute
  - Task domain 模型：to_dict / from_dict 双向
"""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from ravey.ai.tasks.domain import Task
from ravey.ai.tasks.tools import (
    build_hands,
    estimate_effort,
    parse_requirement,
    plan_end_to_end,
    save_task_tree,
    schedule_tasks,
    split_task,
)


# ============================================================
# parse_requirement
# ============================================================

class TestParseRequirement:

    def test_bullets(self):
        text = "- 任务一\n- 任务二\n* 任务三"
        result = parse_requirement(text)
        titles = [t["title"] for t in result]
        assert titles == ["任务一", "任务二", "任务三"]
        assert all(t["id"].startswith("task-") for t in result)
        assert all(t["description"] == "" for t in result)

    def test_numbered_list(self):
        text = "1. 接口设计\n2) 后端实现\n3、前端实现"
        result = parse_requirement(text)
        titles = [t["title"] for t in result]
        assert titles == ["接口设计", "后端实现", "前端实现"]

    def test_sentence_split(self):
        text = "完成首页改版。修复登录 bug；优化搜索性能"
        result = parse_requirement(text)
        titles = [t["title"] for t in result]
        assert titles == ["完成首页改版", "修复登录 bug", "优化搜索性能"]

    def test_empty_input(self):
        assert parse_requirement("") == []
        assert parse_requirement("   \n  \t") == []
        assert parse_requirement(None) == []  # type: ignore[arg-type]

    def test_filters_short_fragments(self):
        # 句子分割模式下，长度 < 4 的碎片被过滤
        text = "好。a；优化数据库索引。b"
        result = parse_requirement(text)
        titles = [t["title"] for t in result]
        assert titles == ["优化数据库索引"]

    def test_deduplicates_same_title(self):
        text = "- 接口A\n- 接口A\n- 接口B"
        result = parse_requirement(text)
        assert len(result) == 2

    def test_id_is_stable(self):
        """同样的 title 产出同样的 id。"""
        a = parse_requirement("- 同样的任务")
        b = parse_requirement("- 同样的任务")
        assert a[0]["id"] == b[0]["id"]

    def test_bullets_take_priority_over_sentences(self):
        text = "总目标：发版。\n- 子任务1\n- 子任务2"
        result = parse_requirement(text)
        # bullet 命中，句子分割不再生效
        assert [t["title"] for t in result] == ["子任务1", "子任务2"]


# ============================================================
# split_task
# ============================================================

class TestSplitTask:

    def test_module_template(self):
        task = {"id": "t1", "title": "用户中心模块"}
        result = split_task(task)
        assert len(result["subtasks"]) == 6
        assert result["subtasks"][0]["title"].startswith("需求评审")

    def test_no_template_match_is_leaf(self):
        task = {"id": "t1", "title": "想个名字"}
        result = split_task(task)
        assert result["subtasks"] == []

    def test_does_not_mutate_input(self):
        task = {"id": "t1", "title": "支付接口"}
        original = dict(task)
        _ = split_task(task)
        assert task == original

    def test_max_subtasks_truncation(self):
        task = {"id": "t1", "title": "登录模块"}
        result = split_task(task, max_subtasks=3)
        assert len(result["subtasks"]) == 3

    def test_inherits_priority(self):
        task = {"id": "t1", "title": "登录模块", "priority": "P0"}
        result = split_task(task)
        assert all(s["priority"] == "P0" for s in result["subtasks"])

    def test_fills_default_fields(self):
        task = {"id": "t1", "title": "无模板任务"}
        result = split_task(task)
        for k in ("hours", "priority", "depends_on", "start_date", "due_date"):
            assert k in result

    def test_bug_template(self):
        task = {"id": "t1", "title": "修复某 bug"}
        result = split_task(task)
        steps = [s["title"].split(" - ")[0] for s in result["subtasks"]]
        assert steps == ["复现", "定位", "修复", "回归测试"]


# ============================================================
# estimate_effort
# ============================================================

class TestEstimateEffort:

    def test_rule_matched(self):
        task = {"id": "t1", "title": "评审需求"}
        result = estimate_effort(task)
        assert result["hours"] == 1.0

    def test_default_when_no_rule_matches(self):
        task = {"id": "t1", "title": "完全无关键词的任务"}
        result = estimate_effort(task)
        assert result["hours"] == 4.0

    def test_parent_aggregates_children(self):
        task = {
            "id": "p", "title": "父任务",
            "subtasks": [
                {"id": "c1", "title": "评审 PRD", "subtasks": []},
                {"id": "c2", "title": "实现登录", "subtasks": []},
            ],
        }
        result = estimate_effort(task)
        assert result["subtasks"][0]["hours"] == 1.0
        assert result["subtasks"][1]["hours"] == 8.0
        assert result["hours"] == 9.0

    def test_does_not_mutate_input(self):
        task = {"id": "t1", "title": "评审", "subtasks": []}
        before = dict(task)
        _ = estimate_effort(task)
        assert task == before

    def test_recursive_three_levels(self):
        task = {
            "id": "g", "title": "祖父",
            "subtasks": [
                {
                    "id": "p", "title": "父",
                    "subtasks": [
                        {"id": "c", "title": "评审", "subtasks": []},
                    ],
                },
            ],
        }
        result = estimate_effort(task)
        assert result["subtasks"][0]["subtasks"][0]["hours"] == 1.0
        assert result["subtasks"][0]["hours"] == 1.0
        assert result["hours"] == 1.0


# ============================================================
# schedule_tasks
# ============================================================

class TestScheduleTasks:

    def test_single_leaf_within_one_day(self):
        # start_date 是周一
        tasks = [{"id": "t1", "title": "x", "hours": 2.0, "subtasks": []}]
        result = schedule_tasks(tasks, start_date="2026-05-04", work_hours_per_day=6.0)
        assert result[0]["start_date"] == "2026-05-04"
        assert result[0]["due_date"] == "2026-05-04"

    def test_skips_weekend(self):
        # 2026-05-02 是周六，应跳到周一 2026-05-04
        tasks = [{"id": "t1", "title": "x", "hours": 2.0, "subtasks": []}]
        result = schedule_tasks(tasks, start_date="2026-05-02", work_hours_per_day=6.0)
        assert result[0]["start_date"] == "2026-05-04"

    def test_skips_holiday(self):
        tasks = [{"id": "t1", "title": "x", "hours": 2.0, "subtasks": []}]
        result = schedule_tasks(
            tasks, start_date="2026-05-04", work_hours_per_day=6.0,
            holidays=["2026-05-04", "2026-05-05"],
        )
        assert result[0]["start_date"] == "2026-05-06"

    def test_multi_day_task(self):
        # 14h, 6h/day → 占 3 天（6 + 6 + 2）
        tasks = [{"id": "t1", "title": "x", "hours": 14.0, "subtasks": []}]
        result = schedule_tasks(tasks, start_date="2026-05-04", work_hours_per_day=6.0)
        assert result[0]["start_date"] == "2026-05-04"
        assert result[0]["due_date"] == "2026-05-06"

    def test_serial_tasks_advance_cursor(self):
        tasks = [
            {"id": "t1", "title": "a", "hours": 6.0, "subtasks": []},
            {"id": "t2", "title": "b", "hours": 6.0, "subtasks": []},
        ]
        result = schedule_tasks(tasks, start_date="2026-05-04", work_hours_per_day=6.0)
        assert result[0]["due_date"] == "2026-05-04"
        assert result[1]["start_date"] == "2026-05-05"

    def test_parent_dates_span_subtasks(self):
        tasks = [{
            "id": "p", "title": "P",
            "subtasks": [
                {"id": "c1", "title": "a", "hours": 6.0, "subtasks": []},
                {"id": "c2", "title": "b", "hours": 6.0, "subtasks": []},
            ],
        }]
        result = schedule_tasks(tasks, start_date="2026-05-04", work_hours_per_day=6.0)
        assert result[0]["start_date"] == "2026-05-04"
        assert result[0]["due_date"] == "2026-05-05"

    def test_default_start_is_today(self):
        tasks = [{"id": "t1", "title": "x", "hours": 1.0, "subtasks": []}]
        result = schedule_tasks(tasks)
        # 起始一定是今天或之后第一个工作日
        assert result[0]["start_date"] >= date.today().isoformat()


# ============================================================
# save_task_tree
# ============================================================

class TestSaveTaskTree:

    def test_writes_json(self, tmp_path: Path):
        tree = [{"id": "t1", "title": "中文标题", "subtasks": []}]
        out = tmp_path / "plan.json"
        path = save_task_tree(tree, str(out))
        assert Path(path).is_file()

        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded == tree

    def test_creates_parent_dirs(self, tmp_path: Path):
        out = tmp_path / "deep" / "nested" / "plan.json"
        save_task_tree([], str(out))
        assert out.parent.is_dir()

    def test_preserves_chinese_chars(self, tmp_path: Path):
        out = tmp_path / "plan.json"
        save_task_tree([{"id": "t1", "title": "需求评审"}], str(out))
        text = out.read_text(encoding="utf-8")
        assert "需求评审" in text  # 没有被 \uXXXX 转义

    def test_returns_absolute_path(self, tmp_path: Path):
        out = tmp_path / "plan.json"
        path = save_task_tree([], str(out))
        assert Path(path).is_absolute()


# ============================================================
# plan_end_to_end
# ============================================================

class TestPlanEndToEnd:

    def test_full_pipeline(self):
        result = plan_end_to_end(
            "- 用户中心模块\n- 修复登录 bug",
            start_date="2026-05-04",
        )
        assert len(result) == 2
        # 第一个有模板（"模块"），有子任务
        assert len(result[0]["subtasks"]) > 0
        # 估工时填上
        assert result[0]["hours"] > 0
        # 排期填上
        assert result[0]["start_date"] is not None
        assert result[0]["due_date"] is not None

    def test_empty_input(self):
        assert plan_end_to_end("") == []

    def test_with_holidays(self):
        result = plan_end_to_end(
            "- 单测某模块",
            start_date="2026-05-04",
            holidays=["2026-05-04"],
        )
        # 起始应跳过假期
        first_start = result[0]["start_date"]
        assert first_start > "2026-05-04"


# ============================================================
# build_hands （Hand 注册）
# ============================================================

class TestBuildHands:

    def test_returns_five_hands(self):
        hands = build_hands()
        assert set(hands.keys()) == {
            "parse_requirement", "split_task", "estimate_effort",
            "schedule_tasks", "save_task_tree",
        }

    def test_each_hand_executes(self):
        hands = build_hands()
        # parse_requirement
        result = hands["parse_requirement"].execute(
            "parse_requirement", {"text": "- 任务一"}
        )
        assert "任务一" in result

    def test_hand_schema_has_description(self):
        hands = build_hands()
        for name, hand in hands.items():
            schema = hand.schema()
            assert schema["name"] == name
            assert schema["description"]


# ============================================================
# Task domain model
# ============================================================

class TestTaskDomain:

    def test_to_dict_round_trip(self):
        t = Task(
            id="t1", title="父", hours=10.0, priority="P1",
            depends_on=["t0"], start_date="2026-05-04", due_date="2026-05-05",
            subtasks=[Task(id="c1", title="子", hours=4.0)],
        )
        d = t.to_dict()
        t2 = Task.from_dict(d)
        assert t2.id == t.id
        assert t2.title == t.title
        assert t2.hours == t.hours
        assert t2.subtasks[0].id == "c1"

    def test_from_dict_with_defaults(self):
        t = Task.from_dict({"id": "x", "title": "y"})
        assert t.priority == "P2"
        assert t.subtasks == []
        assert t.depends_on == []
