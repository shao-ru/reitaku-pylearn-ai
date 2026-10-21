"""知識グラフの一覧ドキュメント（Markdown）を YAML から生成する（graph-doc）"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

LAYER_ORDER = ("文法", "構造", "アルゴリズム", "応用")
REL_LABEL = {"prerequisite": "先修", "related_error": "混同エラー", "related": "関連", "contains": "包含"}


def _md(s) -> str:
    return "" if s is None else str(s).replace("|", "\\|").replace("\n", " ")


def render(data: dict, bundle: dict, content_counts: dict) -> str:
    graphs = data["graphs"]
    kp_by_id = {kp["id"]: kp for g in graphs for kp in g["knowledge_points"]}
    rels = bundle["relations"]
    units = bundle["units"]

    out = [f"# 知識グラフ一覧（自動生成）",
           "",
           f"`uv run python -m tools.edu_content graph-doc content/` で `content/` の YAML から生成した一覧（{date.today().isoformat()}）。"
           "**このファイルは直接編集しない。** 設計方針は `docs/knowledge_graph.md` を参照。",
           ""]

    # ---- 概要
    by_layer = Counter(kp["layer"] for kp in kp_by_id.values())
    by_rel = Counter(r["relation_type"] for r in rels)
    out += ["## 概要", "",
            "| 項目 | 数 |", "| --- | --- |",
            f"| トピック | {len(graphs)} |",
            f"| 知識点 | {len(kp_by_id)}（" + "・".join(f"{l} {by_layer[l]}" for l in LAYER_ORDER if by_layer[l]) + "） |",
            f"| 関係 | {len(rels)}（" + "・".join(f"{REL_LABEL[t]} {n}" for t, n in by_rel.items()) + "） |",
            f"| 単元 | {len(units)}（うちトピック単元 {sum(u['auto'] for u in units)}） |", ""]

    # ---- トピック間の依存（mermaid）
    edges = Counter()
    for r in rels:
        if r["relation_type"] != "prerequisite":
            continue
        a, b = kp_by_id.get(r["from_id"]), kp_by_id.get(r["to_id"])
        if a and b and a["topic"] != b["topic"]:
            edges[(a["topic"], b["topic"])] += 1
    out += ["## トピック間の先修関係", "",
            "矢印は「左のトピックの知識点が、右のトピックの知識点の前提になっている」ことを表す（数字は関係の数）。", "",
            "```mermaid", "flowchart LR"]
    for g in graphs:
        layers = sorted({kp["layer"] for kp in g["knowledge_points"]}, key=LAYER_ORDER.index)
        out.append(f'    {g["topic"]}["{g["topic"]}<br/>{g["title"]}<br/>（{"・".join(layers)}）"]')
    for (a, b), n in sorted(edges.items()):
        out.append(f"    {a} -->|{n}| {b}")
    out += ["```", ""]

    # ---- トピックごとの知識点
    incoming = defaultdict(list)
    for r in rels:
        if r["relation_type"] == "prerequisite":
            incoming[r["to_id"]].append(r["from_id"])
    out += ["## 知識点", "",
            "「講義」「問題」は現在の教材の数（問題は主知識点として数えたもの）。", ""]
    for g in sorted(graphs, key=lambda g: g["topic"]):
        out += [f"### {g['topic']}：{g['title']}", "",
                "| ID | 知識点 | 層 | 難易度 | 前提 | 講義 | 問題 |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for kp in sorted(g["knowledge_points"], key=lambda k: k["order"]):
            c = content_counts.get(kp["id"], {})
            out.append(f"| {kp['id']} | {_md(kp['title'])} | {kp['layer']} | {kp['difficulty']} | "
                       f"{', '.join(incoming.get(kp['id'], [])) or '—'} | {c.get('lessons', 0) or '—'} | {c.get('exercises', 0) or '—'} |")
        out.append("")

    # ---- 単元
    out += ["## 単元", "",
            "「単元の講義・問題」は単元そのものに付けた教材（総合演習など）の数。範囲内の知識点の教材は含まない。", "",
            "| ID | 単元 | 範囲 | 知識点数 | 単元の講義 | 単元の問題 |", "| --- | --- | --- | --- | --- | --- |"]
    for u in sorted(units, key=lambda u: (u["auto"], u["id"])):
        scope = []
        if u["topics"]:
            scope.append("トピック " + ", ".join(u["topics"]))
        if u["knowledge_points"]:
            scope.append(", ".join(u["knowledge_points"]))
        c = content_counts.get(("unit", u["id"]), {})
        kind = "（自動）" if u["auto"] else ""
        out.append(f"| {u['id']} | {_md(u['title'])}{kind} | {_md(' ＋ '.join(scope))} | {len(u['members'])} | "
                   f"{c.get('lessons', 0) or '—'} | {c.get('exercises', 0) or '—'} |")
    out.append("")

    # ---- 先修以外の関係
    out += ["## 混同エラー・関連", "",
            "| 種類 | 知識点 | 知識点 | 説明 |", "| --- | --- | --- | --- |"]
    for r in rels:
        if r["relation_type"] in ("related_error", "related"):
            out.append(f"| {REL_LABEL[r['relation_type']]} | {r['from_id']} | {r['to_id']} | {_md(r.get('note'))} |")
    out.append("")
    return "\n".join(out)


def content_counts(bundle: dict) -> dict:
    counts: dict = defaultdict(lambda: {"lessons": 0, "exercises": 0})
    for le in bundle["lessons"]:
        for k in le["knowledge_points"]:
            counts[k]["lessons"] += 1
        if le.get("unit"):
            counts[("unit", le["unit"])]["lessons"] += 1
    for ex in bundle["exercises"]:
        if ex.get("unit"):
            counts[("unit", ex["unit"])]["exercises"] += 1
        else:
            counts[ex["primary_knowledge_point"]]["exercises"] += 1
    return counts
