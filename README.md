# Advanced Data Analytics for Health Professionals

This repo holds code and content for an advanced, graduate-level course in health data analytics. The course is aimed at current or future medical providers, health administrators, or public health professionals. Learning outcomes are met using seminars and hands-on labs. 

## About the course

The course picks up where an introductory analytics course leaves off (spreadsheets, statistical testing, visualization). It adds relational databases, SQL and machine learning, and applies them to areas of healthcare administration where analytics already drives organizational performance.

By the end, students should be able to:

- access and query data in relational databases with industry-standard SQL tools
- use machine learning to find insights for a healthcare analytics project
- explain how analytics improves performance in three domains: **revenue cycle**, **value-based payment** and **population health**
- design and run an analytics project, including intermediate steps and stakeholder deliverables
- explain current best practices for the effective and ethical use of AI in healthcare analytics
- evaluate AI-generated outputs with common quality assurance approaches

### How each week fits together

Each week combines four seminars that build toward a hands-on lab:

| Seminar | What it covers |
|---|---|
| **Analytics management** | Components of an analytics project, stakeholder alignment, writing requirements, quality assurance, designing deliverables, communicating complex findings, managing timelines and setbacks |
| **AI in analytics** | How generative AI and machine learning work, the current tool landscape, using AI to write code, when to use it and when not to, and how to evaluate its output |
| **Domain context** | A healthcare administration topic, such as claims and revenue cycle, quality measurement, risk adjustment, transitions of care, area-level resources, or fraud, waste and abuse |
| **Technical skills** | The skill the lab needs, from basic SQL through joins, subqueries and optimization, to scikit-learn and neural networks |

The **lab** is where the seminar topics all meet. Students apply that week's technical skill to a business question from the domain seminar, using one realistic dataset all term. Every lab includes a step where students use a generative AI tool and check its work. Each lab ends with a short written answer for a stakeholder, not just code.

### Course arc

| Phase | Labs | Focus |
|---|---|---|
| **Foundations: Databases and the revenue cycle** | 1–4 | Relational databases, querying claims, denials, electronic prior authorization |
| **Value-based payment and quality using SQL** | 5–7 | Patient attribution, HEDIS-style quality measures, provider performance and the data problems that make value-based payment hard |
| **Machine learning for population health** | 8–12 | Risk adjustment coding gaps (intro to ML), program evaluation (logistic regression), root causes of complications (random forests), high-risk geographies (neural networks), fraud detection (clustering) |
| **Putting it together** | 13 | A multi-model workflow that turns predictions into an intervention decision with an estimated return |

## The data

All labs use one **fully synthetic** data warehouse. It looks like what a health plan and a regional hospital system would hold for a population over five years (2021–2025):

- **Members and coverage:** demographics, plus monthly eligibility across commercial, ACA Marketplace, Medicaid and Medicare plans, including people moving between coverage types
- **Claims:** medical claim headers and lines (diagnoses, procedures, DRGs, charges, allowed and paid amounts, denials, resubmissions) and pharmacy claims (paid and rejected)
- **Operations:** prior authorization requests, care management program enrollments, and a hospital patient-accounting ledger (payments, adjustments, write-offs)
- **Context:** a provider directory and area-level social and resource measures by zip code

The data has the messiness and structure that make healthcare analytics hard: churn between payers, denials and rework, small denominators, selection bias in programs, and hidden patterns for students to discover. No real person, provider or plan is represented.

## Contents

| Folder | What it is |
|---|---|
| [`labs/`](labs/) | Thirteen labs, from SQL basics to machine learning, each with a student handout, a full SQL/Python solution and expected results. A slide deck with every lab's instructions is in [`labs/slides/`](labs/slides/). |
| [`management-seminars/`](management-seminars/) | One short slide deck per week's management seminar: basics, best practices and common pitfalls for running analytics projects, with speaker notes. Same plain format as the technical seminars. |
| [`domain-seminars/`](domain-seminars/) | One short slide deck per week's domain seminar: basics, policy, reform goals, how analytics is deployed and how it drives decisions, with speaker notes and sources. Same plain format as the technical seminars. |
| [`technical-seminars/`](technical-seminars/) | One short slide deck per week's technical seminar, with speaker notes and an overview of the matching lab. Plain formatting, ready for an organization's template. |
| [`exam/`](exam/) | Written exam: one required and four elective essay questions on planning an analytics project, plus instructions, an oral follow-up and a rubric aligned with the learning outcomes. |
| [`software-setup/`](software-setup/) | Student setup guide for the software (all free and open source): DuckDB, DBeaver Community, and JupyterLab via Miniforge. Includes the conda environment, a setup checker, and a getting-started notebook. |
| [`synthetic-data/`](synthetic-data/) | Generator for the synthetic data warehouse described above. Outputs a DuckDB database and Parquet files, with a data dictionary and instructor notes. |

## Getting started

- **Students:** follow [`software-setup/`](software-setup/), then start with [Lab 1](labs/lab01_software_tour/).
- **Instructors:** build the data with [`synthetic-data/`](synthetic-data/) (`python generate.py`), then check the labs with `python labs/tools/run_solutions.py <database>`.

## About the instructor

**Andrew S. Cistola, PhD, MPH** is a data scientist, health policy researcher and adjunct faculty member who teaches graduate courses in health data analytics and health information technology.

He leads analytics teams supporting federal health programs at a national consulting firm. His work centers on payment integrity for Medicare programs. Before that, he worked on ACA Marketplace risk adjustment at a health plan, on national benchmarks of healthcare administrative transactions at an industry nonprofit, and as a data analyst in state public health.

His research interests include value-based payment, risk adjustment and health equity, diabetes outcomes, program evaluation, and the use of AI in health services research. He has presented at national health services research, health data and health economics conferences. He holds a PhD in health services research and an MPH in population health management, both from the University of Florida.

He often tells students that data problems are, at root, human problems. That is why this course pairs technical skills with stakeholder work, communication and judgment.

[Connect on LinkedIn](https://www.linkedin.com/in/andrew-cistola/)

## License

MIT. See [LICENSE](LICENSE).
