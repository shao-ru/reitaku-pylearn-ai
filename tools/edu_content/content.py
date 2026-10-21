"""コンテンツ全体の読み込み・相互参照チェック・JSON 出力"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .common import ID_RE, Report, as_list, find_meta_cell, load_notebook
from .exercise import TYPES, load_exercises
from .graph import check_graphs, load_graph, load_units_file
from .lesson import load_lesson
from .runner import run_tests

SET_MODES = ("static", "adaptive")


def _skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).parts
    return any(p.startswith(".") or p == "templates" or p.endswith("checkpoints") for p in rel[:-1])


def _load_set(path: Path, data: dict, report: Report) -> dict | None:
    where = str(path)
    sid = data.get("id")
    if not sid or not ID_RE.match(str(sid)):
        report.error(where, f"id が不正です: {sid!r}")
        return None
    mode = data.get("mode")
    if mode not in SET_MODES:
        report.error(where, f"mode は {SET_MODES} のいずれか: {mode!r}")
    return {
        "id": sid,
        "title": data.get("title"),
        "description": data.get("description"),
        "mode": mode,
        "items": [str(i) for i in as_list(data.get("items"))],
        "shuffle": bool(data.get("shuffle", False)),
        "selection": data.get("selection") or {},
        "source": where,
    }


def load_all(root: Path, report: Report) -> dict:
    graphs, unit_files, lessons, ex_files, sets = [], [], [], [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _skip(path, root):
            continue
        if path.suffix in (".yaml", ".yml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                report.error(str(path), f"YAML の構文エラー: {e}")
                continue
            kind = data.get("type") if isinstance(data, dict) else None
            if kind == "graph":
                g = load_graph(path, report)
                if g:
                    graphs.append(g)
            elif kind == "units":
                unit_files.append(load_units_file(path, data, report))
            elif kind == "set":
                s = _load_set(path, data, report)
                if s:
                    sets.append(s)
            else:
                report.warn(str(path), "type が graph / units / set ではないため無視しました")
        elif path.suffix == ".ipynb":
            nb = load_notebook(path)
            idx, meta = find_meta_cell(nb.get("cells", []))
            if meta is None:
                report.error(str(path), "先頭にメタデータセル（```yaml ... type: lesson / exercises）がありません")
                continue
            if meta["type"] == "lesson":
                le = load_lesson(path, nb, idx, meta, report)
                if le:
                    lessons.append(le)
            elif meta["type"] == "exercises":
                ef = load_exercises(path, nb, idx, meta, report)
                if ef:
                    ex_files.append(ef)
            else:
                report.error(str(path), f"type は lesson / exercises のいずれか: {meta['type']!r}")
    return {"graphs": graphs, "unit_files": unit_files, "lessons": lessons,
            "exercise_files": ex_files, "sets": sets}


def check_all(data: dict, report: Report, run_code: bool = True) -> dict:
    gr = check_graphs(data["graphs"], data["unit_files"], report)
    kp_ids, kp_by_id, units = gr["kp_ids"], gr["kp_by_id"], gr["units"]

    seen: dict[str, str] = {}
    for le in data["lessons"]:
        if le["id"] in seen:
            report.error(le["source"], f"ID が重複: {le['id']}（{seen[le['id']]}）")
        seen[le["id"]] = le["source"]
        for k in le["knowledge_points"]:
            if k not in kp_ids:
                report.error(le["source"], f"存在しない知識点: {k}")
        if le["unit"] and le["unit"] not in units:
            report.error(le["source"], f"存在しない単元: {le['unit']}")

    exercises = []
    ex_seen: dict[str, str] = {}
    for ef in data["exercise_files"]:
        if ef["id"] in seen:
            report.error(ef["source"], f"ID が重複: {ef['id']}（{seen[ef['id']]}）")
        seen[ef["id"]] = ef["source"]
        for ex in ef["exercises"]:
            w = f"{ex['source']} 問題 {ex['id']}"
            if ex["id"] is None:
                continue  # ID なしは解析時にエラー済み
            if ex["id"] in ex_seen:
                report.error(w, f"問題 ID が重複（{ex_seen[ex['id']]}）")
            ex_seen[ex["id"]] = ex["source"]
            for k in ex["knowledge_points"]:
                if k not in kp_ids:
                    report.error(w, f"存在しない知識点: {k}")
            if ex["unit"]:
                if ex["unit"] not in units:
                    report.error(w, f"存在しない単元: {ex['unit']}")
                else:
                    # 主知識点は単元の範囲内にあるべき（2番目以降は前提となる他の知識点でもよい）
                    p = ex["primary_knowledge_point"]
                    if p in kp_ids and p not in units[ex["unit"]]["members"]:
                        report.warn(w, f"主知識点 {p} が単元 {ex['unit']} の範囲外です")
            if ex["difficulty"] is None and ex["primary_knowledge_point"] in kp_by_id:
                ex["difficulty"] = kp_by_id[ex["primary_knowledge_point"]]["difficulty"]
            if not isinstance(ex["difficulty"], int) or not 1 <= ex["difficulty"] <= 9:
                report.error(w, f"難易度は 1〜9 の整数: {ex['difficulty']!r}")
            if ex["question_type"] == "code" and run_code and ex.get("tests") and ex.get("solution_code"):
                res = run_tests(ex["solution_code"], ex["tests"])
                for i, r in enumerate(res):
                    if not r["ok"]:
                        report.error(w, f"模範解答がテスト {i + 1} に失敗: {r.get('error') or repr(r.get('got'))}")
                if ex.get("starter_code"):
                    res = run_tests(ex["starter_code"], ex["tests"])
                    if all(r["ok"] for r in res):
                        report.error(w, "初期コードのままで全テストに通ってしまいます")
            exercises.append(ex)

    for s in data["sets"]:
        if s["id"] in seen:
            report.error(s["source"], f"ID が重複: {s['id']}（{seen[s['id']]}）")
        seen[s["id"]] = s["source"]
        if s["mode"] == "static":
            if not s["items"]:
                report.error(s["source"], "static の題単には items が必要です")
            for i in s["items"]:
                if i not in ex_seen:
                    report.error(s["source"], f"存在しない問題: {i}")
        elif s["mode"] == "adaptive":
            sel = s["selection"]
            kps = [str(k) for k in as_list(sel.get("knowledge_points"))]
            topics = [str(t) for t in as_list(sel.get("topics"))]
            sel_units = [str(u) for u in as_list(sel.get("units"))]
            if not kps and not topics and not sel_units:
                report.error(s["source"], "selection に knowledge_points・topics・units のいずれかが必要です")
            for k in kps:
                if k not in kp_ids:
                    report.error(s["source"], f"存在しない知識点: {k}")
            for u in sel_units:
                if u not in units:
                    report.error(s["source"], f"存在しない単元: {u}")
                else:
                    kps = kps + [k for k in units[u]["members"] if k not in kps]
            types = [TYPES.get(t, t) for t in as_list(sel.get("question_types"))] or list(TYPES.values())
            lo, hi = (as_list(sel.get("difficulty")) + [1, 9])[:2] if sel.get("difficulty") else (1, 9)
            # 候補：主知識点が範囲内、またはその単元の問題（総合演習など）
            pool = [e for e in exercises
                    if (e["primary_knowledge_point"] in kps
                        or kp_by_id.get(e["primary_knowledge_point"], {}).get("topic") in topics
                        or (e["unit"] is not None and e["unit"] in sel_units))
                    and e["question_type"] in types and lo <= (e["difficulty"] or 0) <= hi]
            count = sel.get("count")
            if not isinstance(count, int) or count < 1:
                report.error(s["source"], "selection.count は 1 以上の整数")
            elif len(pool) < count:
                report.warn(s["source"], f"条件に合う問題が {len(pool)} 問しかありません（count={count}）")
            s["pool_size"] = len(pool)

    return {
        "knowledge_points": [kp for g in data["graphs"] for kp in g["knowledge_points"]],
        "relations": [{k: v for k, v in r.items() if k != "_where"} for g in data["graphs"] for r in g["relations"]],
        "units": [_clean_unit(u) for u in units.values()],
        "lessons": data["lessons"],
        "exercises": exercises,
        "sets": data["sets"],
    }


# ---------------------------------------------------------------------------
# JSON 出力（元ファイル1つにつき JSON ファイル1つ）
# ---------------------------------------------------------------------------

def _clean_unit(u: dict) -> dict:
    return {k: v for k, v in u.items() if not k.startswith("_")}


def content_hash(ex: dict) -> str:
    """問題の内容から計算するハッシュ。取り込み時に内容の変更（＝版番号の更新）を検出するのに使う。"""
    body = {k: v for k, v in ex.items() if k not in ("id", "source", "content_hash")}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _rel(source: str, root: Path) -> Path:
    return Path(source).resolve().relative_to(root.resolve())


def write_json(data: dict, root: Path, out_dir: Path) -> list[Path]:
    """各元ファイルと同じ相対パスに .json を出力する。"""
    written = []

    def dump(obj: dict, source: str, kind: str) -> None:
        rel_src = _rel(source, root)
        path = out_dir / rel_src.with_suffix(".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        # source は元ファイルの相対パス（root からの位置）
        obj = {"type": kind, **{k: v for k, v in obj.items() if k not in ("source", "_where")},
               "source": rel_src.as_posix()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written.append(path)

    for g in data["graphs"]:
        g = dict(g, relations=[{k: v for k, v in r.items() if k != "_where"} for r in g["relations"]],
                 units=[_clean_unit(u) for u in g["units"]])
        dump(g, g["source"], "graph")
    for f in data["unit_files"]:
        dump({"units": [_clean_unit(u) for u in f["units"]]}, f["source"], "units")
    for le in data["lessons"]:
        dump(le, le["source"], "lesson")
    for ef in data["exercise_files"]:
        exs = []
        for ex in ef["exercises"]:
            ex = {k: v for k, v in ex.items() if k != "source"}
            ex["content_hash"] = content_hash(ex)
            exs.append(ex)
        dump(dict(ef, exercises=exs), ef["source"], "exercises")
    for s in data["sets"]:
        dump(s, s["source"], "set")
    return written
