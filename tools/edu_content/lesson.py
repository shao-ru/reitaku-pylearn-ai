"""講義ノート（lesson ipynb）の読み込み・検証・教材出力"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from .common import ID_RE, Report, as_list, cell_source, find_meta_cell, first_h1, load_notebook


def load_lesson(path: Path, nb: dict, meta_idx: int, meta: dict, report: Report) -> dict | None:
    where = str(path)
    cells = nb["cells"]
    lid = meta.get("id")
    if not lid or not ID_RE.match(str(lid)):
        report.error(where, f"id が不正です: {lid!r}")
        return None
    # 講義は知識点に付ける（knowledge_points）か、単元に付ける（unit：総合演習のまとめなど）
    kps = [str(k) for k in as_list(meta.get("knowledge_points"))]
    unit = meta.get("unit")
    if not kps and not unit:
        report.error(where, "knowledge_points（知識点）か unit（単元）のどちらかを指定してください")
    if kps and unit:
        report.error(where, "knowledge_points と unit は同時に指定できません")

    body = [c for i, c in enumerate(cells) if i != meta_idx]
    title = meta.get("title") or first_h1(body)
    if not title:
        report.error(where, "タイトル（title または最初の # 見出し）がありません")

    # 講義ノートに採点用の情報が混ざっていないか
    for c in body:
        src = cell_source(c)
        if (re.search(r"^###\s*正解\s*$", src, re.MULTILINE) or re.search(r"\*\*正解[：:]", src)
                or src.lstrip().startswith("# @solution")):
            report.error(where, "講義ノートに正解・模範解答が含まれています（練習ファイルに移してください）")
            break

    parts = []
    for c in body:
        src = cell_source(c).strip()
        if not src:
            continue
        if c.get("cell_type") == "code":
            parts.append(f"```python\n{src}\n```")
        else:
            parts.append(src)

    return {
        "id": lid,
        "title": title,
        "knowledge_points": kps,
        "unit": str(unit) if unit else None,
        "content": "\n\n".join(parts),
        "source": where,
    }


def write_courseware(path: Path, out_path: Path) -> None:
    """メタデータセルを除いた ipynb を出力する（LearnLab の教材としてアップロードする用）。"""
    nb = load_notebook(path)
    idx, _ = find_meta_cell(nb["cells"])
    out = copy.deepcopy(nb)
    if idx is not None:
        del out["cells"][idx]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
