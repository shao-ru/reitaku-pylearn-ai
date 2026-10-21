"""共通ユーティリティ: ipynb の読み込み、メタデータセルの解析、エラー収集"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

LAYERS = ("文法", "構造", "アルゴリズム", "応用")
RELATION_TYPES = ("prerequisite", "contains", "related_error", "related")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")
YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL)


@dataclass
class Issue:
    level: str  # "error" | "warning"
    where: str
    message: str

    def __str__(self) -> str:
        mark = "ERROR" if self.level == "error" else "WARN "
        return f"[{mark}] {self.where}: {self.message}"


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, where: str, message: str) -> None:
        self.issues.append(Issue("error", where, message))

    def warn(self, where: str, message: str) -> None:
        self.issues.append(Issue("warning", where, message))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]


def cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def load_notebook(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_yaml_block(text: str) -> dict | list | None:
    """テキスト中の最初の ```yaml ブロックを読み込む。なければ None。"""
    m = YAML_BLOCK_RE.search(text)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def find_meta_cell(cells: list[dict]) -> tuple[int, dict] | tuple[None, None]:
    """先頭のメタデータセル（```yaml で始まり type を含む markdown セル）を探す。"""
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell_source(cell).strip()
        if not src:
            continue
        if src.startswith("```yaml") or src.startswith("```yml"):
            data = parse_yaml_block(src)
            if isinstance(data, dict) and "type" in data:
                return i, data
        # 最初の非空 markdown セルがメタでなければ打ち切る
        return None, None
    return None, None


def first_h1(cells: list[dict]) -> str:
    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        m = re.search(r"^#\s+(.+)$", cell_source(cell), re.MULTILINE)
        if m:
            return m.group(1).strip()
    return ""


def as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def split_list(text: str) -> list[str]:
    """`a` `b` 形式、または a, b / a、b 形式の並びをリストにする。"""
    text = text.strip()
    ticks = re.findall(r"`([^`]+)`", text)
    if ticks:
        return [t.strip() for t in ticks if t.strip()]
    return [t.strip() for t in re.split(r"[,、，]", text) if t.strip()]
