# Troubleshooting

## "Could not set lock on file" / "Conflicting lock is held"

DuckDB lets **one program write** to a database file, **or many programs read** it. This error means one connection opened the file in read-write mode.

- **DBeaver:** edit the connection (right-click → *Edit Connection*) → **Driver properties** → make sure `duckdb.read_only` = `true`. Then disconnect and reconnect.
- **Python/Jupyter:** always connect with `duckdb.connect(path, read_only=True)`.
- Still stuck? Close DBeaver, restart the Jupyter kernel (**Kernel → Restart Kernel**), and try again.

## Saving your own tables

The course database is read-only for coursework. To keep intermediate results:

- **Temporary tables** work on a read-only connection and last until you disconnect:
  ```sql
  CREATE TEMP TABLE my_diabetics AS
  SELECT DISTINCT member_id FROM medical_claims WHERE dx_1 LIKE 'E11%';
  ```
- **A personal workspace file** keeps tables between sessions. In a notebook:
  ```python
  work = duckdb.connect("../data/my_work.duckdb")            # your own file, read-write
  work.sql("ATTACH '../data/health_analytics.duckdb' AS course (READ_ONLY)")
  work.sql("CREATE OR REPLACE TABLE my_diabetics AS SELECT DISTINCT member_id FROM course.medical_claims WHERE dx_1 LIKE 'E11%'")
  ```
  In DBeaver, make a second DuckDB connection to `my_work.duckdb` (not read-only) and run the same `ATTACH` statement.
- **Export to a file:** `COPY (SELECT ...) TO 'result.csv' (HEADER);` or right-click a DBeaver result → *Export data*.

## DBeaver can't download the DuckDB driver

Usually a campus or VPN firewall. Try another network, or download the driver manually:

1. Download the latest `duckdb_jdbc-<version>.jar` from **https://repo1.maven.org/maven2/org/duckdb/duckdb_jdbc/**.
2. In DBeaver: **Database → Driver Manager → DuckDB → Edit → Libraries → Add File** and choose the JAR.
3. Click **Find Class**. It should show `org.duckdb.DuckDBDriver`. Click **OK**.

## `conda` is not recognized (Windows)

You're in a regular Command Prompt or PowerShell. Open **Miniforge Prompt** from the Start menu instead.

## `conda: command not found` (macOS/Linux)

Close and reopen Terminal. If it still fails, run `~/miniforge3/bin/conda init` and reopen Terminal again.

## `conda env create` fails or is very slow

- Make sure you're in the folder that contains `environment.yml` (`dir` on Windows, `ls` on macOS should list it).
- If it fails on **TensorFlow**, delete the `tensorflow` line from `environment.yml`, create the environment, and add TensorFlow later, when you reach the neural network labs, with `conda activate health-analytics` then `pip install tensorflow`.
- If the environment already exists from an earlier attempt: `conda env remove -n health-analytics`, then create it again.

## The notebook says `Found database: False`

The notebook expects the database at `../data/health_analytics.duckdb`, relative to the notebooks folder. Either move the file there or change `DB_PATH` in the first code cell to the full path, using forward slashes on Windows:

```python
DB_PATH = Path("C:/Users/yourname/HealthAnalytics/data/health_analytics.duckdb")
```

## `ModuleNotFoundError` in JupyterLab

JupyterLab was probably started from outside the `health-analytics` environment. Close it, then run `conda activate health-analytics` followed by `jupyter lab`. In the notebook's top-right corner the kernel should read **Python 3 (ipykernel)**.

## Apple Silicon Macs and TensorFlow

Recent TensorFlow releases (2.16+) install directly with pip on M-series Macs. If TensorFlow imports but runs slowly, that's expected. Course models are small and run fine on the CPU.

## Still stuck?

Ask your instructor or classmates, and include:

1. your operating system,
2. the exact command you ran,
3. a screenshot of the full error message,
4. the output of `python check_setup.py`.
