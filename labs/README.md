# Labs

Thirteen hands-on labs that use the synthetic health data warehouse (`health_analytics.duckdb`). Each one answers a real business question from healthcare administration. The labs build from SQL basics to machine learning and a final multi-model project.

| # | Lab | Business question | Technique | Tool |
|---|---|---|---|---|
| 1 | [Software Tour](lab01_software_tour/) | What's in the warehouse and how do the tables connect? | relational keys, joins | DBeaver, JupyterLab |
| 2 | [Querying Claims Data](lab02_querying_claims/) | How much did payers pay, and who pays slowest? | `SELECT`, `WHERE`, aggregates | DBeaver |
| 3 | [Claim Denials](lab03_claim_denials/) | Which denials cost most, and how much is recovered? | `CASE WHEN` | DBeaver |
| 4 | [Tracking Electronic Prior Authorization Use](lab04_prior_authorization/) | Is ePA growing, is it faster, and who's lagging? | `GROUP BY`, `HAVING` | DBeaver |
| 5 | [Patient Attribution](lab05_attribution/) | Who belongs to the ACO, and does plan assignment match reality? | joins, `ROW_NUMBER()` | DBeaver |
| 6 | [Calculating HEDIS Scores](lab06_hedis/) | How do the MA plans score on three quality measures? | subqueries, CTEs | DBeaver |
| 7 | [Provider Performance Comparison](lab07_provider_performance/) | Which practice differences are real and which are noise? | query optimization | DBeaver |
| 8 | [Closing Coding Gaps](lab08_coding_gaps/) | Which HCCs are most likely to go undocumented this year? | scikit-learn basics | JupyterLab |
| 9 | [Readmissions Reduction Program](lab09_readmissions/) | Did the Transitional Care Program work? | logistic regression | JupyterLab |
| 10 | [Diabetes Complications](lab10_diabetes_complications/) | What drives complications beyond A1c and adherence? | random forests | JupyterLab |
| 11 | [High-Risk Zip Codes](lab11_high_risk_zips/) | Where should mobile clinics go? | neural networks (TensorFlow) | JupyterLab |
| 12 | [Fraud Detection](lab12_fraud_detection/) | Which providers should investigators audit? | k-means | JupyterLab |
| 13 | [Finding a Potential Intervention](lab13_finding_an_intervention/) | Which program gives the best return? | multi-model pipeline, ROI | JupyterLab |

## What's in each lab folder

| File | For |
|---|---|
| `README.md` | Student handout: scenario, definitions, tasks, deliverable |
| `solution.md` | Complete SQL/Python solution, the expected pattern of results, common AI mistakes and a sample stakeholder answer |
| `expected_results.md` | Exact output of every solution block on the default database build |

Every lab follows the same pattern: 3–5 tasks, about 60–75 minutes, one task where students use a generative AI tool and check its work, and a short written answer to the business question.

## Slides

- [`slides/lab_instructions.pptx`](slides/lab_instructions.pptx): one deck with an overview and instruction slide for every lab.
- Each week's technical seminar deck in [`../technical-seminars`](../technical-seminars) ends with an overview of that week's lab.

## Setup

Students need the software in [`../software-setup`](../software-setup) and the database file `health_analytics.duckdb` (built by [`../synthetic-data`](../synthetic-data)). SQL labs assume a DBeaver connection to that file. Notebook labs assume it sits at `../data/health_analytics.duckdb` relative to the notebook.

## For instructors

- **Check the solutions** against any build of the data:
  ```bash
  python labs/tools/run_solutions.py synthetic-data/output/health_analytics_instructor.duckdb
  python labs/tools/run_solutions.py synthetic-data/output/health_analytics_instructor.duckdb lab09 --write   # refresh expected_results.md
  ```
  Use the instructor database. A few solution blocks check student answers against the `answer_key` schema.
- `expected_results.md` was generated from the default build (`python generate.py`, 25,000 members, seed 42). A different seed or member count changes the exact numbers but not the patterns.
- The planted patterns behind each lab are documented in [`../synthetic-data/docs/instructor_notes.md`](../synthetic-data/docs/instructor_notes.md).
