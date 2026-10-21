"""知識グラフ定義（graph.yaml）と単元定義（units.yaml）の読み込みと検証

用語
  トピック : 知識点の置き場所（フォルダと graph.yaml）。知識点はちょうど1つのトピックに属する
  知識点   : 習熟度を記録する最小単位
  単元     : 知識点の集まり。総合演習・トピックをまたぐ練習・テスト範囲に使う。
             各トピックには、トピック全体を範囲とする単元（ID = トピック名）が自動で作られる
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .common import ID_RE, LAYERS, RELATION_TYPES, Report, as_list

# 向きを持たない関係（循環チェックの対象外）
UNDIRECTED = ("related",)


def _load_units(raw, where: str, report: Report, topic: str | None) -> list[dict]:
    units = []
    for i, u in enumerate(raw or []):
        w = f"{where} units[{i}]"
        if not isinstance(u, dict):
            report.error(w, "辞書形式で書いてください")
            continue
        uid = u.get("id")
        if not uid or not ID_RE.match(str(uid)):
            report.error(w, f"id が不正です: {uid!r}")
            continue
        if not u.get("title"):
            report.error(f"{w} ({uid})", "title がありません")
        kps = [str(k) for k in as_list(u.get("knowledge_points"))]
        topics = [str(t) for t in as_list(u.get("topics"))]
        if not kps and not topics:
            report.error(f"{w} ({uid})", "knowledge_points か topics のどちらかが必要です")
        units.append({"id": uid, "title": u.get("title"), "description": u.get("description"),
                      "topics": topics, "knowledge_points": kps, "defined_in": topic, "auto": False,
                      "_where": f"{w} ({uid})"})
    return units


def load_graph(path: Path, report: Report) -> dict | None:
    where = str(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        report.error(where, f"YAML の構文エラー: {e}")
        return None
    if not isinstance(data, dict) or data.get("type") != "graph":
        report.error(where, "先頭に `type: graph` が必要です")
        return None

    topic = data.get("topic")
    if not topic or not ID_RE.match(str(topic)):
        report.error(where, f"`topic` が不正です: {topic!r}")

    kps = []
    for i, kp in enumerate(data.get("knowledge_points") or []):
        w = f"{where} knowledge_points[{i}]"
        if not isinstance(kp, dict):
            report.error(w, "辞書形式で書いてください")
            continue
        kid = kp.get("id")
        if not kid or not ID_RE.match(str(kid)):
            report.error(w, f"id が不正です: {kid!r}")
            continue
        if not kp.get("title"):
            report.error(f"{w} ({kid})", "title がありません")
        if kp.get("layer") not in LAYERS:
            report.error(f"{w} ({kid})", f"layer は {LAYERS} のいずれか: {kp.get('layer')!r}")
        d = kp.get("difficulty")
        if not isinstance(d, int) or not 1 <= d <= 9:
            report.error(f"{w} ({kid})", f"difficulty は 1〜9 の整数: {d!r}")
        kps.append({
            "id": kid,
            "topic": topic,
            "title": kp.get("title"),
            "description": kp.get("description"),
            "layer": kp.get("layer"),
            "difficulty": d,
            "keywords": [str(k) for k in (kp.get("keywords") or [])],
            "order": kp.get("order", i + 1),
        })

    rels = []
    for i, r in enumerate(data.get("relations") or []):
        w = f"{where} relations[{i}]"
        if not isinstance(r, dict):
            report.error(w, "辞書形式で書いてください")
            continue
        if r.get("type") not in RELATION_TYPES:
            report.error(w, f"type は {RELATION_TYPES} のいずれか: {r.get('type')!r}")
        weight = r.get("weight", 1.0)
        if not isinstance(weight, (int, float)) or not 0 <= weight <= 1:
            report.error(w, f"weight は 0.0〜1.0: {weight!r}")
        rels.append({
            "from_id": r.get("from"),
            "to_id": r.get("to"),
            "relation_type": r.get("type"),
            "weight": float(weight) if isinstance(weight, (int, float)) else 1.0,
            "note": r.get("note"),
            "_where": w,
        })

    return {"topic": topic, "title": data.get("title"), "knowledge_points": kps, "relations": rels,
            "units": _load_units(data.get("units"), where, report, topic), "source": where}


def load_units_file(path: Path, data: dict, report: Report) -> dict:
    """type: units のファイル（トピックをまたぐ単元）"""
    where = str(path)
    return {"units": _load_units(data.get("units"), where, report, None), "source": where}


def check_graphs(graphs: list[dict], unit_files: list[dict], report: Report) -> dict:
    """全グラフ・単元をまとめて検証する。

    Returns: {"kp_ids": set, "kp_by_id": dict, "units": {unit_id: unit（members 付き）}}
    """
    ids: dict[str, str] = {}
    topics: dict[str, dict] = {}
    for g in graphs:
        if g["topic"] in topics:
            report.error(g["source"], f"トピック {g['topic']} が重複しています（{topics[g['topic']]['source']}）")
        topics[g["topic"]] = g
        for kp in g["knowledge_points"]:
            if kp["id"] in ids:
                report.error(g["source"], f"知識点 ID が重複: {kp['id']}（{ids[kp['id']]} でも定義）")
            ids[kp["id"]] = g["source"]
    kp_by_id = {kp["id"]: kp for g in graphs for kp in g["knowledge_points"]}

    # --- 関係 ---
    prereq: dict[str, list[str]] = {}
    seen_rel = set()
    for g in graphs:
        for r in g["relations"]:
            for end in ("from_id", "to_id"):
                if r[end] not in ids:
                    report.error(r["_where"], f"存在しない知識点: {r[end]!r}")
            if r["from_id"] == r["to_id"]:
                report.error(r["_where"], "自分自身への関係です")
            key = (r["relation_type"], *(sorted([r["from_id"], r["to_id"]])
                   if r["relation_type"] in UNDIRECTED else [r["from_id"], r["to_id"]]))
            if key in seen_rel:
                report.warn(r["_where"], f"同じ関係が2回定義されています: {r['from_id']} - {r['to_id']}")
            seen_rel.add(key)
            if r["relation_type"] == "prerequisite":
                prereq.setdefault(r["from_id"], []).append(r["to_id"])

    state: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        for nxt in prereq.get(node, []):
            if state.get(nxt) == 1:
                cyc = path[path.index(nxt):] + [nxt] if nxt in path else [node, nxt]
                report.error("graph", f"先修関係が循環しています: {' → '.join(cyc)}")
            elif state.get(nxt) is None:
                visit(nxt, path + [nxt])
        state[node] = 2

    for n in list(prereq):
        if state.get(n) is None:
            visit(n, [n])

    linked = {r[e] for g in graphs for r in g["relations"] for e in ("from_id", "to_id")}
    for g in graphs:
        for kp in g["knowledge_points"]:
            if kp["id"] not in linked:
                report.warn(g["source"], f"関係が一つもない知識点: {kp['id']}")

    # --- 単元 ---
    units: dict[str, dict] = {}
    for t, g in topics.items():  # トピック単元（自動）
        units[t] = {"id": t, "title": g["title"], "description": None, "topics": [t], "knowledge_points": [],
                    "defined_in": t, "auto": True, "_where": g["source"]}
    for u in [u for g in graphs for u in g["units"]] + [u for f in unit_files for u in f["units"]]:
        if u["id"] in units:
            report.error(u["_where"], f"単元 ID がトピック名または他の単元と重複しています: {u['id']}")
            continue
        if u["id"] in ids:
            report.error(u["_where"], f"単元 ID が知識点 ID と重複しています: {u['id']}")
            continue
        units[u["id"]] = u
    for u in units.values():
        members = []
        for t in u["topics"]:
            if t not in topics:
                report.error(u["_where"], f"存在しないトピック: {t}")
                continue
            members += [kp["id"] for kp in topics[t]["knowledge_points"]]
        for k in u["knowledge_points"]:
            if k not in ids:
                report.error(u["_where"], f"存在しない知識点: {k}")
            elif k not in members:
                members.append(k)
        u["members"] = members

    return {"kp_ids": set(ids), "kp_by_id": kp_by_id, "units": units}
