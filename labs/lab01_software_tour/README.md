# Lab 1: Software Tour

**Business question:** What's in this data warehouse, and how do the tables connect?

**Skills:** relational database concepts (tables, rows, primary and foreign keys) and finding your way around DBeaver and JupyterLab.
**Domains introduced:** revenue cycle, value-based payment, population health.
**Tool:** DBeaver (SQL) and JupyterLab.
**Time:** about 60 minutes.

## Scenario

You've joined the analytics team at **Understory Health**, a regional health system in North Central Florida. It runs Understory Regional Medical Center, Understory Community Hospital, an employed physician group and an ACO, Understory Health Partners. The team works from a claims data warehouse for the region's population (2021–2025). It holds what a health plan sees (eligibility, medical and pharmacy claims) and what the hospital sees (its payment ledger).

Before you can answer business questions, you need to know where things live.

## Data

The whole database: `health_analytics.duckdb`. You'll mainly use `beneficiaries`, `coverage_member_months`, `medical_claims`, `medical_claim_lines`, `pharmacy_claims` and `providers`.

Every column has a description. In DBeaver, open a table's **Properties** tab, or run:

```sql
SELECT table_name, column_name, comment
FROM duckdb_columns()
WHERE table_name = 'medical_claims';
```

## Tasks

### 1. Confirm your setup
Run `python check_setup.py` and the notebook `00_getting_started.ipynb` (see `software-setup/`). Take a screenshot of the checker output.

### 2. Find the keys
In DBeaver right-click **main → View Diagram**.
- Name the **primary key** of `beneficiaries`, `medical_claims` and `providers`. Prove each one is unique with a query that compares `COUNT(*)` with `COUNT(DISTINCT ...)`.
- Name **two foreign-key links**, for example the column in `medical_claim_lines` that points to `medical_claims`. Write a join that uses each one.

### 3. Trace one member's story
Pick any member who has both medical and pharmacy claims. Using only SQL, describe:
- who they are (age, sex, zip code and county)
- their coverage over time (which payers and plans, and when)
- their care: how many claims by setting (office, emergency, inpatient, …), their top diagnoses, and their prescriptions

*Hint:* `GROUP BY` with `MIN()` and `MAX()` turns 60 rows of monthly coverage into a few lines.

### 4. AI step
Ask an AI tool: *"In medical claims data, what is the difference between a claim header and a claim line?"* Then check the answer against `medical_claims` and `medical_claim_lines`: which columns live on each, and why? Note one thing the AI got right and one it got wrong or left vague.

## Deliverable

Submit one file (SQL script or notebook) with:
1. the setup screenshot
2. your key queries and the names of the keys
3. the member's story in a short paragraph, with the `member_id` and the queries you used
4. your AI check (2–3 sentences)
