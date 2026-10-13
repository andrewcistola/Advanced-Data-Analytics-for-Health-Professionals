#!/usr/bin/env python3
"""Run every code block in the lab solution files against a database.

    python labs/tools/run_solutions.py path/to/health_analytics.duckdb            # all labs
    python labs/tools/run_solutions.py path/to/health_analytics.duckdb lab03 lab09
    python labs/tools/run_solutions.py path/to/health_analytics.duckdb --write   # also save expected_results.md

```sql blocks run in DuckDB; ```python blocks run in one namespace per lab that already
has `con` (a read-only DuckDB connection) and `DB_PATH`. Results print to the console so
instructors can compare them with the "Expected results" in each solution.
"""
import re
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
LABS = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"```(sql|python)\n(.*?)```", re.S)


def run_lab(sol: Path, db: str, write: bool = False) -> bool:
    import contextlib
    import io
    buf = io.StringIO()
    tee = Tee(sys.stdout, buf)
    with contextlib.redirect_stdout(tee):
        ok = _run(sol, db)
    if write:
        body = buf.getvalue()
        body = re.sub(r"  \[block (\d+) (sql|python) ok, [0-9.]+s\]", r"--- end of block \1 ---", body)
        (sol.parent / "expected_results.md").write_text(
            f"# Expected results: {sol.parent.name}\n\nOutput of every code block in `solution.md`, run against the default "
            f"database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.\n\n"
            f"```text\n{body.strip()}\n```\n")
    return ok


class Tee(io.TextIOBase if False else object):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def _run(sol: Path, db: str) -> bool:
    print(f"\n{'=' * 100}\n{sol.parent.name}\n{'=' * 100}")
    con = duckdb.connect(db, read_only=True)
    ns = {"con": con, "DB_PATH": db, "__name__": "__main__"}
    ok = True
    for n, (lang, code) in enumerate(BLOCK.findall(sol.read_text()), 1):
        if "# skip-run" in code or "-- skip-run" in code:
            continue
        t0 = time.time()
        try:
            if lang == "sql":
                for stmt in [s for s in code.split(";") if s.strip() and not all(
                        l.strip().startswith("--") or not l.strip() for l in s.splitlines())]:
                    rel = con.sql(stmt)
                    if rel is not None:
                        print(rel.df().head(15).to_string())
            else:
                exec(compile(code, f"{sol.parent.name}#block{n}", "exec"), ns)
            print(f"  [block {n} {lang} ok, {time.time() - t0:.1f}s]")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  [block {n} {lang} FAILED] {type(e).__name__}: {e}")
    con.close()
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    db, only = args[0], args[1:]
    sols = sorted(LABS.glob("lab*/solution.md"))
    if only:
        sols = [s for s in sols if any(s.parent.name.startswith(o) for o in only)]
    results = {s.parent.name: run_lab(s, db, write) for s in sols}
    print("\nSummary:", ", ".join(f"{k}: {'ok' if v else 'FAILED'}" for k, v in results.items()))
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
