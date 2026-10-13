# Step 3: Install Python and JupyterLab with Miniforge

We use **Miniforge**, a free, open-source installer for Python and the `conda` package manager. It sets up an isolated environment named `health-analytics` with every package the course needs, without touching any other Python on your computer.

> Already use Anaconda or Miniconda? You can skip 3.1 and run the commands in 3.2 from the Anaconda Prompt or Terminal.

## 3.1 Install Miniforge

### Windows

1. Go to **https://github.com/conda-forge/miniforge/releases/latest**.
2. Download **`Miniforge3-Windows-x86_64.exe`** and run it.
3. Choose **Just Me**, keep the default location, and accept the other defaults.
4. From the Start menu open **Miniforge Prompt**. Use this prompt for every command below.

### macOS and Linux

Open **Terminal** and run:

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

Press Enter to scroll through the license, type `yes` to accept, keep the default location, and answer `yes` when asked to initialize conda. **Close and reopen Terminal** afterwards.

### Check it worked

```bash
conda --version
```

You should see something like `conda 24.x` or newer.

## 3.2 Create the course environment

Move into your course folder and create the environment from `environment.yml`.

**Windows (Miniforge Prompt):**

```bat
cd %USERPROFILE%\HealthAnalytics
conda env create -f environment.yml
```

**macOS / Linux (Terminal):**

```bash
cd ~/HealthAnalytics
conda env create -f environment.yml
```

This downloads Python 3.12, JupyterLab, DuckDB, pandas, scikit-learn, TensorFlow and a few other packages. It takes 5–15 minutes depending on your connection. TensorFlow is the largest piece.

## 3.3 Start JupyterLab

Do this every time you work on a lab:

```bash
conda activate health-analytics
cd ~/HealthAnalytics            # Windows: cd %USERPROFILE%\HealthAnalytics
jupyter lab
```

JupyterLab opens in your web browser. Keep the prompt/terminal window open while you work. Closing it stops JupyterLab.

In the left file browser open **notebooks → 00_getting_started.ipynb** and run each cell with **Shift + Enter**.

## 3.4 How SQL works in a notebook

The course environment includes **JupySQL**, which adds a `%%sql` cell type:

```python
import duckdb
con = duckdb.connect("../data/health_analytics.duckdb", read_only=True)
%load_ext sql
%sql con
```

```sql
%%sql
SELECT payer_type, COUNT(DISTINCT member_id) AS members
FROM coverage_member_months
WHERE coverage_year = 2025
GROUP BY payer_type
```

Save a query result to Python with `<<`, then use pandas:

```sql
%%sql result <<
SELECT * FROM beneficiaries LIMIT 100
```

```python
df = result.DataFrame()
df.head()
```

Or run SQL directly from Python: `df = con.sql("SELECT ...").df()`.

## 3.5 Stopping JupyterLab

Save your notebook, then in JupyterLab choose **File → Shut Down**, or press **Ctrl + C** twice in the prompt/terminal.

Next: [Step 4 – Check your setup](04_check_setup.md)
