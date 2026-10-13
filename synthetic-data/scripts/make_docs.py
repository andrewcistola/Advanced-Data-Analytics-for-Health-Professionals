#!/usr/bin/env python3
"""Build docs/data_dictionary.md from a generated instructor DuckDB file.

    python scripts/make_docs.py output/health_analytics_instructor.duckdb
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from synthhealth.dictionary import TABLES  # noqa: E402


def q(s):
    return s.replace("'", "''")


def main(db):
    con = duckdb.connect(db, read_only=True)
    cols = con.sql("select table_schema, table_name, column_name, data_type, ordinal_position from information_schema.columns "
                   "order by table_schema, table_name, ordinal_position").df()
    md = ["# Data dictionary", "",
          "Generated from the default build (25,000 members, seed 42). Row counts change with `--members`/`--seed`.", ""]
    for (schema, table), g in cols.groupby(["table_schema", "table_name"], sort=False):
        n = con.sql(f"select count(*) from {schema}.{table}").fetchone()[0]
        tdesc, cdesc = TABLES.get(table, ("Answer key (instructor only)." if schema != "main" else "", {}))
        if schema == "main":
            md += [f"## `{table}`", "", tdesc, "", f"Rows: {n:,}", "", "| Column | Type | Description |", "|---|---|---|"]
            md += [f"| `{r.column_name}` | {r.data_type} | {cdesc.get(r.column_name, '')} |" for r in g.itertuples()]
            md.append("")
    ak = cols[cols.table_schema == "answer_key"].groupby("table_name").column_name.apply(lambda s: ", ".join(f"`{c}`" for c in s))
    md += ["## Instructor-only `answer_key` schema", "",
           "These tables hold the generator's hidden truth so you can check student answers. They exist only in `health_analytics_instructor.duckdb` (and `parquet/answer_key/`), not in the student file `health_analytics.duckdb`.", ""]
    md += [f"- **{t}**: {c}" for t, c in ak.items()]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "data_dictionary.md").write_text("\n".join(md) + "\n")
    print("wrote docs/data_dictionary.md")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "output" / "health_analytics_instructor.duckdb"))
