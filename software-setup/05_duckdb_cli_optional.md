# Step 5 (optional): DuckDB command-line tool

You don't need this for the labs, since DBeaver and JupyterLab cover everything. The command-line tool is handy for quick queries and for converting files (CSV ↔ Parquet ↔ Excel).

## Install

- **Windows:** in PowerShell, `winget install DuckDB.cli`
- **macOS:** with Homebrew, `brew install duckdb`
- **Any system:** download from **https://duckdb.org/install** and put the `duckdb` executable somewhere on your PATH.

## Use

Open the course database read-only:

```bash
duckdb -readonly ~/HealthAnalytics/data/health_analytics.duckdb
```

Then type SQL, ending each statement with a semicolon:

```sql
.tables
SELECT payer_type, COUNT(*) FROM coverage_member_months GROUP BY 1;
.quit
```

Useful dot-commands:

| Command | What it does |
|---|---|
| `.tables` | list tables |
| `.mode markdown` | print results as a Markdown table |
| `.timer on` | show query run time (useful for query optimization exercises) |
| `.quit` | exit |

DuckDB can also query files directly without loading them, e.g. `SELECT * FROM 'my_extract.csv';` or `COPY (SELECT ...) TO 'result.parquet';`.
