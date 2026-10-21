"""教材コンテンツの検証・ID 付与・JSON 出力ツール

使い方（リポジトリのルートで実行。初回は uv sync）:
  uv run python -m tools.edu_content validate   content/
  uv run python -m tools.edu_content assign-ids content/            [--dry-run]
  uv run python -m tools.edu_content export     content/ -o build/json/
  uv run python -m tools.edu_content courseware content/ -o build/courseware/
  uv run python -m tools.edu_content graph-doc  content/ -o docs/knowledge_graph_overview.md

  --no-run   コード問題のテスト実行を省略する（validate / export）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .common import Report, find_meta_cell, load_notebook
from .content import _skip, check_all, load_all, write_json
from .ids import assign_ids
from .graphdoc import content_counts, render
from .lesson import write_courseware


def _summary(bundle: dict) -> str:
    ex = bundle["exercises"]
    n_choice = sum(e["question_type"] == "choice" for e in ex)
    n_code = sum(e["question_type"] == "code" for e in ex)
    return (f"知識点 {len(bundle['knowledge_points'])} / 関係 {len(bundle['relations'])} / "
            f"単元 {len(bundle['units'])} / 講義 {len(bundle['lessons'])} / 問題 {len(ex)}（選択 {n_choice}・コード {n_code}） / "
            f"題単 {len(bundle['sets'])}")


def _notebooks(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*.ipynb")) if not _skip(p, root)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="edu_content", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "assign-ids", "export", "courseware", "graph-doc"):
        sp = sub.add_parser(name)
        sp.add_argument("root", type=Path)
        if name in ("export", "courseware", "graph-doc"):
            sp.add_argument("-o", "--out", type=Path, required=True)
        if name in ("validate", "export"):
            sp.add_argument("--no-run", action="store_true")
        if name == "assign-ids":
            sp.add_argument("--dry-run", action="store_true", help="書き込まずに付与予定の ID だけ表示する")
    args = p.parse_args(argv)

    if args.cmd == "assign-ids":
        assigned = assign_ids(_notebooks(args.root), dry_run=args.dry_run)
        for path, qid in assigned:
            print(f"  {qid}  ← {path}")
        verb = "付与予定" if args.dry_run else "付与しました"
        print(f"ID を {len(assigned)} 件{verb}")
        return 0

    if args.cmd == "courseware":
        n = 0
        for path in _notebooks(args.root):
            _, meta = find_meta_cell(load_notebook(path).get("cells", []))
            if meta and meta.get("type") == "lesson":
                out = args.out / path.relative_to(args.root)
                write_courseware(path, out)
                print(f"  {out}")
                n += 1
        print(f"講義ノート {n} 件を出力しました")
        return 0

    report = Report()
    data = load_all(args.root, report)
    bundle = check_all(data, report, run_code=not getattr(args, "no_run", False) and args.cmd != "graph-doc")
    if args.cmd == "graph-doc":
        if report.errors:
            for issue in report.errors:
                print(issue)
            print("エラーがあるため出力しませんでした")
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render(data, bundle, content_counts(bundle)), encoding="utf-8")
        print(f"出力: {args.out}")
        return 0
    for issue in report.issues:
        print(issue)
    print(_summary(bundle))
    print(f"エラー {len(report.errors)} 件 / 警告 {len(report.warnings)} 件")
    if args.cmd == "validate":
        return 1 if report.errors else 0

    if report.errors:
        print("エラーがあるため出力しませんでした")
        return 1
    written = write_json(data, args.root, args.out)
    print(f"JSON {len(written)} 件を出力しました: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
