# Step 2: Install DBeaver and connect to the database

DBeaver Community Edition is a free, open-source SQL editor that works with almost every database used in healthcare (SQL Server, Oracle, PostgreSQL, Snowflake, DuckDB and more). What you learn here carries over to whatever database your employer uses.

## 2.1 Install DBeaver Community

1. Go to **https://dbeaver.io/download/**.
2. Download **DBeaver Community** for your system:
   - **Windows:** *Windows (installer)*. Run it and accept the defaults.
   - **macOS:** *macOS for Apple Silicon* (M1–M4 chips) or *macOS for Intel*. Open the `.dmg` and drag DBeaver to Applications. Not sure which chip you have? Apple menu → *About This Mac*.
   - **Linux:** the `.deb`/`.rpm` package or the Snap/Flatpak.
3. Open DBeaver. If it asks to create a sample database, choose **No**.

## 2.2 Create the DuckDB connection

1. Click **Database → New Database Connection** (or the plug icon with a **+** at the top left).
2. Type **DuckDB** in the search box, select it, and click **Next**.
3. Next to **Path**, click **Browse…** and select `HealthAnalytics/data/health_analytics.duckdb`.
4. **Make the connection read-only** so DBeaver and JupyterLab can both use the file at the same time:
   - Open the **Driver properties** tab.
   - Right-click in the property list and choose **Add new property**.
   - Name: `duckdb.read_only`, Value: `true`.
5. Click **Test Connection…**. The first time, DBeaver asks to **download the DuckDB driver**. Click **Download**, wait, then click **OK**. You should see **Connected**.
6. Click **Finish**.

> If you don't see the Driver properties tab until after testing, that's fine. Test first so the driver downloads, then add the property.

## 2.3 Rename the connection (optional but tidy)

Right-click the new connection in the **Database Navigator** (left panel) → **Rename** → `HealthAnalytics`.

## 2.4 Explore

- Expand **HealthAnalytics → health_analytics → main → Tables** to see every table. Double-click a table to see its **Properties** (columns and types) and **Data** tabs.
- **ER diagram:** right-click **main → View Diagram** to see the tables in one picture.
- **Open a SQL editor:** select the connection and press **Ctrl + ]** (Windows/Linux) or **Cmd + ]** (macOS), or use **SQL Editor → New SQL script**.

Paste this and run it with **Ctrl + Enter** (Cmd + Enter on macOS):

```sql
SELECT claim_setting,
       COUNT(*)              AS claims,
       ROUND(SUM(total_paid)) AS total_paid
FROM medical_claims
WHERE claim_status IN ('Paid', 'Partially Paid')
GROUP BY claim_setting
ORDER BY total_paid DESC;
```

You should get one row per care setting (Office, Inpatient, Emergency, …).

To see the description of every column in a table:

```sql
SELECT column_name, data_type, comment
FROM duckdb_columns()
WHERE table_name = 'medical_claims';
```

## 2.5 Handy DBeaver shortcuts

| Action | Windows / Linux | macOS |
|---|---|---|
| Run the statement under the cursor | Ctrl + Enter | Cmd + Enter |
| Run the whole script | Alt + X | Option + X |
| Format SQL | Ctrl + Shift + F | Cmd + Shift + F |
| Autocomplete table/column names | Ctrl + Space | Ctrl + Space |
| Comment/uncomment line | Ctrl + / | Cmd + / |

**Exporting results:** right-click a result grid → **Export data…** → CSV or Excel.

Next: [Step 3 – Python and JupyterLab](03_python_jupyterlab.md)
