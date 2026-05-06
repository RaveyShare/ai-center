"""任务领域模型。

任务树结构：单任务和带 subtasks 的父任务用同一个结构。
所有工具函数都基于 dict 操作，这里的 dataclass 仅用于类型说明和便利。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """任务树节点。"""

    id: str
    title: str
    description: str = ""
    hours: float = 0.0
    priority: str = "P2"             # P0 / P1 / P2 / P3
    depends_on: list[str] = field(default_factory=list)
    start_date: str | None = None
    due_date: str | None = None
    subtasks: list["Task"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "hours": self.hours,
            "priority": self.priority,
            "depends_on": list(self.depends_on),
            "start_date": self.start_date,
            "due_date": self.due_date,
            "subtasks": [s.to_dict() for s in self.subtasks],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        return cls(
            id=d["id"],
            title=d["title"],
            description=d.get("description", ""),
            hours=float(d.get("hours", 0.0)),
            priority=d.get("priority", "P2"),
            depends_on=list(d.get("depends_on", [])),
            start_date=d.get("start_date"),
            due_date=d.get("due_date"),
            subtasks=[cls.from_dict(s) for s in d.get("subtasks", [])],
        )
