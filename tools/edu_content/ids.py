"""問題 ID の自動付与（assign-ids）

ID のない「## 問題」見出しに「<主知識点>-<6桁の16進>」形式の ID を付け、ipynb に書き戻す。
既存の ID は変更しない。乱数を使うので、複数人が別々に問題を追加しても衝突しにくい。
"""
from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from .common import as_list, cell_source, find_meta_cell, load_notebook, split_list
from .exercise import ATTR_RE, QUESTION_HEAD_RE


def _primary_kp(text: str, default_kp) -> str | None:
    for line in text.split("\n"):
        m = ATTR_RE.match(line.strip())
        if m and m.group(1) == "知識点":
            kps = split_list(m.group(2))
            if kps:
                return re.sub(r"[（(].*?[)）]", "", kps[0]).strip()
    kps = as_list(default_kp)
    return str(kps[0]) if kps else None


def _existing_ids(paths: list[Path]) -> set[str]:
    ids = set()
    for path in paths:
        for cell in load_notebook(path).get("cells", []):
            for m in QUESTION_HEAD_RE.finditer(cell_source(cell)):
                if m.group(1):
                    ids.add(m.group(1))
    return ids


def _new_id(prefix: str, used: set[str]) -> str:
    while True:
        qid = f"{prefix}-{secrets.token_hex(3)}"
        if qid not in used:
            used.add(qid)
            return qid


def assign_ids(paths: list[Path], dry_run: bool = False) -> list[tuple[Path, str]]:
    """ID のない問題に ID を付ける。付けた (ファイル, ID) の一覧を返す。"""
    targets = []
    for path in paths:
        nb = load_notebook(path)
        _, meta = find_meta_cell(nb.get("cells", []))
        if meta and meta.get("type") == "exercises":
            targets.append((path, nb, meta))
    used = _existing_ids([p for p, _, _ in targets])

    assigned = []
    for path, nb, meta in targets:
        changed = False
        for cell in nb["cells"]:
            if cell.get("cell_type") != "markdown":
                continue
            src = cell_source(cell)
            m = QUESTION_HEAD_RE.search(src)
            if not m or m.group(1):
                continue
            prefix = _primary_kp(src, meta.get("default_knowledge_point")) or "q"
            qid = _new_id(prefix, used)
            src = src[:m.start()] + f"## 問題 {qid}" + src[m.end():]
            lines = src.split("\n")
            cell["source"] = [ln + "\n" for ln in lines[:-1]] + [lines[-1]]
            assigned.append((path, qid))
            changed = True
        if changed and not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(nb, f, ensure_ascii=False, indent=1)
                f.write("\n")
    return assigned
