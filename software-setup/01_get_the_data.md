# Step 1: Make a course folder and get the data

## 1.1 Create the folder

Create a folder called **`HealthAnalytics`** in your home folder, with two folders inside it:

```
HealthAnalytics/
  data/        <- the database goes here
  notebooks/   <- your lab notebooks go here
```

- **Windows:** `C:\Users\<your name>\HealthAnalytics`
- **macOS:** `/Users/<your name>/HealthAnalytics`

Avoid putting the folder inside OneDrive, iCloud Drive, Dropbox or Google Drive. Sync tools lock files while uploading, which can cause errors when the database is open.

## 1.2 Download the database

1. Download **`health_analytics.duckdb.zip`** from the link your instructor provides.
2. Unzip it and move **`health_analytics.duckdb`** into `HealthAnalytics/data/`.

The file is about 150 MB (about 70 MB zipped). It contains every course table: beneficiaries, coverage, medical and pharmacy claims, hospital payments, prior authorizations, providers, area data and code lookups. All data are synthetic.

## 1.3 Download the setup files

From this GitHub repository click **Code → Download ZIP**, unzip it, and copy these items from `software-setup/` into your `HealthAnalytics` folder:

- `environment.yml`
- `check_setup.py`
- `notebooks/00_getting_started.ipynb` → `HealthAnalytics/notebooks/`

Your folder should now look like:

```
HealthAnalytics/
  check_setup.py
  environment.yml
  data/
    health_analytics.duckdb
  notebooks/
    00_getting_started.ipynb
```

Next: [Step 2 – DBeaver](02_dbeaver.md)
