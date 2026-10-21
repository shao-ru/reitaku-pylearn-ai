"""コード問題のテスト実行（教員が書いた模範解答・初期コードの検証用）

注意: これはサンドボックスではない。信頼できる教材の検証専用であり、
学生の提出コードの採点には M4 の採点サンドボックスを使うこと。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_FUNCTION_HARNESS = r'''
import json, sys
src = open(sys.argv[1], encoding="utf-8").read()
cases = json.load(sys.stdin)
ns = {"__name__": "__submission__"}
try:
    exec(compile(src, "submission.py", "exec"), ns)
except BaseException as e:
    print(json.dumps([{"ok": False, "error": f"{type(e).__name__}: {e}"} for _ in cases]))
    sys.exit(0)
out = []
for c in cases:
    try:
        got = eval(c["call"], ns)
        out.append({"ok": got == c["expected"], "got": repr(got)})
    except BaseException as e:
        out.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
print(json.dumps(out, ensure_ascii=False))
'''


def normalize_output(text: str) -> str:
    """行末の空白と末尾の空行を無視して比較する。"""
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# Windows（cp932）でも日本語の入出力を正しく扱えるよう UTF-8 に固定する
_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def run_tests(code: str, tests: dict) -> list[dict]:
    """各ケースについて {"ok": bool, "got"/"error": ...} を返す。"""
    timeout = tests.get("timeout", 2)
    with tempfile.TemporaryDirectory() as tmp:
        prog = Path(tmp) / "submission.py"
        prog.write_text(code, encoding="utf-8")
        if tests["mode"] == "stdio":
            results = []
            for c in tests["cases"]:
                try:
                    p = subprocess.run([sys.executable, "-I", str(prog)], input=c["input"],
                                       capture_output=True, text=True, encoding="utf-8",
                                       timeout=timeout, cwd=tmp, env=_ENV)
                except subprocess.TimeoutExpired:
                    results.append({"ok": False, "error": f"timeout ({timeout}s)"})
                    continue
                if p.returncode != 0:
                    err = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else f"exit {p.returncode}"
                    results.append({"ok": False, "error": err})
                    continue
                ok = normalize_output(p.stdout) == normalize_output(c["expected"])
                results.append({"ok": ok, "got": p.stdout})
            return results
        harness = Path(tmp) / "harness.py"
        harness.write_text(_FUNCTION_HARNESS, encoding="utf-8")
        payload = json.dumps([{"call": c["call"], "expected": c["expected"]} for c in tests["cases"]])
        try:
            p = subprocess.run([sys.executable, "-I", str(harness), str(prog)], input=payload,
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=timeout * max(1, len(tests["cases"])), cwd=tmp, env=_ENV)
        except subprocess.TimeoutExpired:
            return [{"ok": False, "error": "timeout"} for _ in tests["cases"]]
        try:
            return json.loads(p.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return [{"ok": False, "error": p.stderr.strip() or "no output"} for _ in tests["cases"]]
