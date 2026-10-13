# Software Setup

All labs in this course use free, open-source software that runs on your own laptop (Windows, macOS or Linux). You don't need an account, license or internet connection once everything is installed.

| Tool | What it does in this course | Like… |
|---|---|---|
| **DuckDB** | The database. The course data is a single file, `health_analytics.duckdb`. | Snowflake, SQL Server, Oracle |
| **DBeaver Community** | Point-and-click SQL editor: browse tables, write queries, view diagrams, export results | Snowsight, SSMS, Toad |
| **JupyterLab** | Python notebooks for analysis, charts and machine learning (scikit-learn, TensorFlow). SQL runs in notebooks too. | Snowflake Notebooks, Databricks |
| **Miniforge (conda)** | Installs Python and the packages JupyterLab needs | Anaconda |

Setup takes about 30–45 minutes. Please finish it **before the first lab**.

## Steps

1. [Make a course folder and get the data](01_get_the_data.md) (5 min)
2. [Install DBeaver and connect to the database](02_dbeaver.md) (10 min)
3. [Install Python and JupyterLab with Miniforge](03_python_jupyterlab.md) (15–20 min)
4. [Check your setup](04_check_setup.md) (5 min)
5. *(Optional)* [Install the DuckDB command-line tool](05_duckdb_cli_optional.md)

Stuck? See [troubleshooting.md](troubleshooting.md), then ask your instructor or classmates, including a screenshot.

## What's in this folder

```
software-setup/
  README.md                     this page
  01_get_the_data.md            course folder + database file
  02_dbeaver.md                 DBeaver install and connection
  03_python_jupyterlab.md       Miniforge, environment, JupyterLab
  04_check_setup.md             verify everything works
  05_duckdb_cli_optional.md     DuckDB command-line tool (optional)
  troubleshooting.md            common problems and fixes
  environment.yml               conda environment definition (recommended)
  requirements.txt              pip alternative
  check_setup.py                setup checker script
  notebooks/00_getting_started.ipynb   first notebook: SQL + Python with DuckDB
```

## How the pieces fit together

```
            health_analytics.duckdb  (one file, read-only for coursework)
              /                         \
   DBeaver (SQL editor)          JupyterLab notebook
   - explore tables              - %%sql cells (JupySQL)
   - write/test queries          - pandas, matplotlib
   - ER diagrams, exports        - scikit-learn, TensorFlow
```

Both tools open the database **read-only**, so you can keep DBeaver and JupyterLab open at the same time. To save your own tables, see [Saving your own work](troubleshooting.md#saving-your-own-tables).

## For instructors

- **Building the database:** run `python generate.py` in [`../synthetic-data`](../synthetic-data). It writes `output/health_analytics.duckdb` (student file, no answer key) and `output/health_analytics_instructor.duckdb` (adds the `answer_key` schema). Only distribute `health_analytics.duckdb`.
- **Distributing it:** the student file is about 140 MB (about 60 MB zipped). Upload it to your learning management system or attach it to a GitHub Release. Students can also build it themselves with `python generate.py` (about 10 minutes), which produces identical data with the default seed.
- **Accommodations / no-install option:** students who can't install software can run the notebooks on an institution-hosted JupyterHub, or in Google Colab after running `pip install jupysql duckdb-engine` and uploading the database file. Colab isn't open source, but it runs in any browser. DuckDB, pandas and scikit-learn are preinstalled there.
