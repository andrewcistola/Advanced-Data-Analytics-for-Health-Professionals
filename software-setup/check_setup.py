#!/usr/bin/env python3
"""Health data analytics lab setup check.

Run from a terminal (with the health-analytics environment active):

    python check_setup.py                      # looks for health_analytics.duckdb in common places
    python check_setup.py path/to/health_analytics.duckdb

Prints OK / MISSING for each tool and runs one test query against the course database.
"""
import importlib
import platform
import sys
from pathlib import Path

REQUIRED = ["duckdb", "pandas", "numpy", "matplotlib", "sklearn", "jupyterlab", "sql", "duckdb_engine", "statsmodels"]
OPTIONAL = ["tensorflow", "seaborn"]


def check(mod):
    try:
        m = importlib.import_module(mod)
        return getattr(m, "__version__", "installed")
    except Exception:
        return None


def find_db(arg):
    cands = [Path(arg)] if arg else []
    here = Path.cwd()
    cands += [here / "health_analytics.duckdb", here / "data" / "health_analytics.duckdb", here.parent / "data" / "health_analytics.duckdb",
              Path.home() / "HealthAnalytics" / "data" / "health_analytics.duckdb", Path.home() / "HealthAnalytics" / "health_analytics.duckdb",
              Path.home() / "Downloads" / "health_analytics.duckdb"]
    return next((p for p in cands if p.exists()), None)


def main():
    ok = True
    print(f"Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    if sys.version_info < (3, 10):
        print("  !! Python 3.10 or newer is required")
        ok = False
    for mod in REQUIRED:
        v = check(mod)
        print(f"  {'OK     ' if v else 'MISSING'} {mod} {v or ''}")
        ok &= bool(v)
    for mod in OPTIONAL:
        v = check(mod)
        print(f"  {'OK     ' if v else 'later  '} {mod} {v or '(optional until the neural network labs)' if mod == 'tensorflow' else v or ''}")
    db = find_db(sys.argv[1] if len(sys.argv) > 1 else None)
    if db is None:
        print("\n  !! Could not find health_analytics.duckdb. Pass its path: python check_setup.py C:/path/to/health_analytics.duckdb")
        ok = False
    else:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        n_tables = con.sql("select count(*) from duckdb_tables()").fetchone()[0]
        n_claims = con.sql("select count(*) from medical_claims").fetchone()[0]
        con.close()
        print(f"\n  OK      database {db}\n          {n_tables} tables, {n_claims:,} medical claims")
    print("\nAll set!" if ok else "\nSomething is missing. See troubleshooting.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
