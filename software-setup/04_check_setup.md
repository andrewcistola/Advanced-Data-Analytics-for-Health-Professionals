# Step 4: Check your setup

## 4.1 Run the checker

With the environment active, from your `HealthAnalytics` folder:

```bash
conda activate health-analytics
python check_setup.py data/health_analytics.duckdb
```

A working setup looks like this:

```
Python 3.12.x on Windows AMD64
  OK      duckdb 1.x
  OK      pandas 2.x
  OK      numpy 2.x
  OK      matplotlib 3.x
  OK      sklearn 1.x
  OK      jupyterlab 4.x
  OK      sql 0.x
  OK      duckdb_engine 0.x
  OK      statsmodels 0.x
  OK      tensorflow 2.x
  OK      seaborn 0.x

  OK      database data/health_analytics.duckdb
          19 tables, 650,869 medical claims

All set!
```

## 4.2 Run the first notebook

In JupyterLab open `notebooks/00_getting_started.ipynb` and choose **Run → Run All Cells**. Every cell should finish without a red error box, and you should see a line chart of members by payer type.

## 4.3 Confirm DBeaver and JupyterLab can share the file

With the notebook still open (don't run the last `con.close()` cell), switch to DBeaver and run any query. If both work at the same time, both connections are read-only and you're done.

## Checklist before the first lab

- [ ] `health_analytics.duckdb` is in `HealthAnalytics/data/`
- [ ] DBeaver connects and the sample query returns rows
- [ ] `python check_setup.py` ends with **All set!**
- [ ] `00_getting_started.ipynb` runs top to bottom
