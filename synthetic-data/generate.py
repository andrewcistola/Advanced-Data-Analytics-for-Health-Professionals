#!/usr/bin/env python3
"""Generate the synthetic health data warehouse.

Usage:
    python generate.py                       # 25,000 members -> output/
    python generate.py --members 2000        # quick small build
    python generate.py --csv                 # also write gzipped CSVs
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from synthhealth.build import build, write, log  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--members", type=int, default=25000, help="number of beneficiaries (default 25,000)")
    ap.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    ap.add_argument("--out", type=Path, default=Path("output"), help="output directory")
    ap.add_argument("--csv", action="store_true", help="also export gzipped CSV files")
    a = ap.parse_args()
    tables, answer = build(a.members, a.seed)
    db = write(tables, answer, a.out, csv=a.csv)
    log(f"done -> {db}")


if __name__ == "__main__":
    main()
