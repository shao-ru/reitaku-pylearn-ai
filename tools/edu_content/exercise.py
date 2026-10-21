"""練習問題ファイル（exercises ipynb）の読み込みと検証

1問 = 「## 問題 <ID>」で始まる markdown セル（見出しセル）
      + コード問題の場合はその後に続く @starter / @solution / @tests のセル
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import yaml

from .common import ID_RE, Report, as_list, cell_source, first_h1, split_list

# 「## 問題 <ID>」。ID を省略した「## 問題」も見出しとして認識する（assign-ids で付与する）
QUESTION_HEAD_RE = re.compile(r"^##[ \t]*問題(?:[ \t]+(\S+))?[ \t]*$", re.MULTILINE)
ATTR_RE = re.compile(r"^[-*]\s*(形式|知識点|難易度|キーワード|タグ)\s*[:：]\s*(.*)$")
SECTION_RE = re.compile(r"^###\s*(.+?)\s*$", re.MULTILINE)
OPTION_RE = re.compile(r"^[-・]\s+([A-F])\.\s?(.*)$")
# 「### 正解」セクションの本文：「B」または複数正解「A, C」
ANSWER_RE = re.compile(r"^\s*([A-F](?:\s*[,、，]\s*[A-F])*)\s*$")
TYPES = {"choice": "choice", "code": "code"}  # ipynb の「形式」→ JSON の question_type
TEST_MODES = ("stdio", "function")


def _sections(text: str) -> tuple[str, dict[str, str]]:
    """見出しセルを「### 以前の部分」と {セクション名: 本文} に分ける。"""
    marks = list(SECTION_RE.finditer(text))
    if not marks:
        return text, {}
    head = text[: marks[0].start()]
    secs = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        secs[m.group(1)] = text[m.end():end].strip()
    return head, secs


def _parse_options(text: str) -> tuple[str, list[str], list[str]]:
    q_lines, options, letters, cur = [], [], [], None
    for line in text.split("\n"):
        m = OPTION_RE.match(line.strip())
        if m:
            if cur is not None:
                options.append(textwrap.dedent("\n".join(cur)).strip())
            letters.append(m.group(1))
            cur = [m.group(2).strip()] if m.group(2).strip() else []
        elif cur is not None:
            cur.append(line)
        else:
            q_lines.append(line)
    if cur is not None:
        options.append(textwrap.dedent("\n".join(cur)).strip())
    return "\n".join(q_lines).strip(), options, letters


def _parse_hints(text: str) -> list[str]:
    hints = []
    for line in text.split("\n"):
        m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.*)$", line)
        if m:
            hints.append(m.group(1).strip())
        elif hints and line.strip():
            hints[-1] += "\n" + line.strip()
    return hints


def _block_kind(cell: dict) -> str | None:
    src = cell_source(cell).lstrip()
    if cell.get("cell_type") == "code":
        if src.startswith("# @starter"):
            return "starter"
        if src.startswith("# @solution"):
            return "solution"
    if cell.get("cell_type") == "markdown" and re.search(r"```ya?ml\s*\n\s*#\s*@tests", src):
        return "tests"
    return None


def _strip_marker(src: str) -> str:
    lines = src.lstrip().split("\n")
    return "\n".join(lines[1:]).strip("\n") + "\n"


def _parse_tests(cell: dict, where: str, report: Report) -> dict | None:
    m = re.search(r"```ya?ml\s*\n(.*?)```", cell_source(cell), re.DOTALL)
    try:
        data = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError as e:
        report.error(where, f"@tests の YAML 構文エラー: {e}")
        return None
    if not isinstance(data, dict):
        report.error(where, "@tests は mode / cases を持つ辞書で書いてください")
        return None
    mode = data.get("mode", "stdio")
    if mode not in TEST_MODES:
        report.error(where, f"@tests の mode は {TEST_MODES} のいずれか: {mode!r}")
    cases = data.get("cases") or []
    if not cases:
        report.error(where, "@tests に cases が1つもありません")
    norm = []
    for i, c in enumerate(cases):
        w = f"{where} cases[{i}]"
        if not isinstance(c, dict) or "expected" not in c:
            report.error(w, "各ケースには expected が必要です")
            continue
        if mode == "function" and not c.get("call"):
            report.error(w, "function モードでは call（例: total(3)）が必要です")
        case = {"expected": c["expected"], "public": bool(c.get("public", False))}
        if mode == "stdio":
            case["input"] = "" if c.get("input") is None else str(c.get("input"))
            case["expected"] = str(c["expected"])
        else:
            case["call"] = c.get("call")
        norm.append(case)
    if norm and not any(c["public"] for c in norm):
        report.warn(where, "public: true のケースがありません（学生に見せる入出力例がない）")
    timeout = data.get("timeout", 2)
    return {"mode": mode, "timeout": timeout, "cases": norm}


def load_exercises(path: Path, nb: dict, meta_idx: int, meta: dict, report: Report) -> dict | None:
    where = str(path)
    cells = nb["cells"]
    fid = meta.get("id")
    if not fid or not ID_RE.match(str(fid)):
        report.error(where, f"id が不正です: {fid!r}")
        return None
    default_kp = meta.get("default_knowledge_point")
    unit = meta.get("unit")  # 単元の練習ファイル（総合演習など）
    if unit and default_kp:
        report.error(where, "unit と default_knowledge_point は同時に指定できません（単元の問題は問題ごとに知識点を書く）")
    default_diff = meta.get("default_difficulty")

    # 見出しセルの位置を集める
    heads = [i for i, c in enumerate(cells)
             if c.get("cell_type") == "markdown" and QUESTION_HEAD_RE.search(cell_source(c))]
    if not heads:
        report.warn(where, "問題（## 問題 <ID>）が1つもありません")

    exercises = []
    for n, hi in enumerate(heads):
        nxt = heads[n + 1] if n + 1 < len(heads) else len(cells)
        text = cell_source(cells[hi])
        qid = QUESTION_HEAD_RE.search(text).group(1)
        if qid is None:
            w = f"{where} {n + 1}問目"
            report.error(w, "問題 ID がありません（`uv run python -m tools.edu_content assign-ids` で付与できます）")
        else:
            w = f"{where} 問題 {qid}"
            if not ID_RE.match(qid):
                report.error(w, "問題 ID に使えない文字があります")

        head, secs = _sections(text[QUESTION_HEAD_RE.search(text).end():])
        attrs = {}
        for line in head.split("\n"):
            m = ATTR_RE.match(line.strip())
            if m:
                attrs[m.group(1)] = m.group(2).strip()

        qtype = attrs.get("形式", "choice")
        if qtype not in TYPES:
            report.error(w, f"形式は choice / code のいずれか: {qtype!r}")
            continue
        kps = split_list(attrs["知識点"]) if attrs.get("知識点") else as_list(default_kp)
        kps = [re.sub(r"[（(].*?[)）]", "", k).strip() for k in kps]  # 「loop_03（主）」の注記を除去
        if not kps:
            report.error(w, "知識点がありません（問題の属性「知識点」か default_knowledge_point で指定）")
        diff = attrs.get("難易度")
        if diff is not None:
            diff = int(diff) if diff.isdigit() else diff
        elif default_diff is not None:
            diff = default_diff
        keywords = split_list(attrs.get("キーワード", ""))
        tags = split_list(attrs.get("タグ", ""))

        stmt = secs.get("問題文")
        if stmt is None:
            report.error(w, "### 問題文 がありません")
            stmt = ""
        hints = _parse_hints(secs["ヒント"]) if "ヒント" in secs else []

        ex = {
            "id": qid,
            "question_type": TYPES[qtype],
            "knowledge_points": kps,
            "primary_knowledge_point": kps[0] if kps else None,
            "unit": str(unit) if unit else None,
            "difficulty": diff,
            "keywords": keywords,
            "tags": tags,
            "hints": hints,
            "source": where,
        }

        if qtype == "choice":
            question, options, letters = _parse_options(stmt)
            ex["question"] = question
            ex["options"] = options
            if len(options) < 2:
                report.error(w, "選択肢（- A. ...）が2つ以上必要です")
            expected_letters = [chr(ord("A") + i) for i in range(len(letters))]
            if letters != expected_letters:
                report.error(w, f"選択肢の記号は A から順に: {letters}")
            if "答えと解説" in secs:
                report.error(w, "旧形式の「### 答えと解説」です。「### 正解」と「### 解説」に分けてください")
            ans = secs.get("正解")
            m = ANSWER_RE.match(ans) if ans is not None else None
            if ans is None:
                report.error(w, "### 正解 がありません")
                ex["correct_answers"] = []
            elif not m:
                report.error(w, f"### 正解 には選択肢の記号だけを書いてください（例: B、A, C）: {ans[:30]!r}")
                ex["correct_answers"] = []
            else:
                answers = re.findall(r"[A-F]", m.group(1))
                ex["correct_answers"] = answers
                for a in answers:
                    if a not in letters:
                        report.error(w, f"正解 {a} が選択肢にありません")
                if len(set(answers)) != len(answers):
                    report.error(w, "正解の記号が重複しています")
            ex["explanation"] = secs.get("解説", "").strip() or None
            if not ex["explanation"]:
                report.warn(w, "### 解説 がないか空です")
        else:
            ex["question"] = stmt
            ex["explanation"] = secs.get("解説", "").strip() or None
            blocks: dict[str, dict] = {}
            for ci in range(hi + 1, nxt):
                kind = _block_kind(cells[ci])
                if kind is None:
                    src = cell_source(cells[ci]).strip()
                    if src and src != "---":
                        report.warn(w, f"問題に属さないセルを無視しました: {src[:30]!r}")
                    continue
                if kind in blocks:
                    report.error(w, f"@{kind} が2つあります")
                blocks[kind] = cells[ci]
            for kind in ("starter", "solution", "tests"):
                if kind not in blocks:
                    report.error(w, f"@{kind} のセルがありません")
            ex["starter_code"] = _strip_marker(cell_source(blocks["starter"])) if "starter" in blocks else None
            ex["solution_code"] = _strip_marker(cell_source(blocks["solution"])) if "solution" in blocks else None
            ex["tests"] = _parse_tests(blocks["tests"], w, report) if "tests" in blocks else None

        exercises.append(ex)

    return {
        "id": fid,
        "title": meta.get("title") or first_h1([c for i, c in enumerate(cells) if i != meta_idx]),
        "exercises": exercises,
        "source": where,
    }
