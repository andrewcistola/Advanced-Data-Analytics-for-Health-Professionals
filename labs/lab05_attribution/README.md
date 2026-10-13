# Lab 5: Patient Attribution

**Business question:** Understory Health Partners, the system's ACO, needs its 2025 attributed population. Which members belong to its practices, and how often does a health plan's assigned PCP match the PCP the member actually sees?

**Skills:** `INNER JOIN` across three tables, `LEFT JOIN`, and `ROW_NUMBER()` to pick one row per member.
**Domain:** value-based payment today. Shared-savings ACOs (like Medicare's MSSP) attribute each patient to the primary care provider who delivered the **plurality** (largest share) of their primary care visits.
**Tool:** DBeaver.
**Time:** about 75 minutes.

## Data

| Table | Use |
|---|---|
| `medical_claims` | `member_id`, `rendering_npi`, `service_from_date` |
| `medical_claim_lines` | `procedure_code` |
| `providers` | `provider_role = 'PCP'`, `practice_name`, `aco_name` |
| `coverage_member_months` | `assigned_pcp_npi` (HMO-type plans only) |

**Primary care visit codes:** office visits 99202–99205 and 99211–99215, preventive visits 99381–99397, annual wellness visits G0438 and G0439.

## Tasks

### 1. Primary care visits
Join `medical_claims` → `medical_claim_lines` → `providers` to list every 2025 visit with a primary care code where the rendering provider is a PCP. Keep `member_id`, the PCP's `npi`, `practice_name`, `aco_name` and the service date. Count one visit per claim.

### 2. Attribute members
For each member and PCP, count visits and find the most recent visit date. Use `ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY visits DESC, last_visit DESC)` to keep each member's top PCP.
- How many members are attributed in 2025?
- How many of them are attributed to an Understory Health Partners practice?

### 3. Assigned vs. attributed
HMO-type plans assign every member a PCP (`assigned_pcp_npi` in `coverage_member_months`). For members with an assigned PCP in December 2025:
- What percent of those *with* a 2025 attribution are attributed to their assigned PCP?
- Using a `LEFT JOIN`, what percent had **no** primary care visit at all in 2025?

### 4. AI step
Ask an AI tool to write the attribution query from the rule in Task 2. Does it break ties by most recent visit? Does it count claims or lines? Fix anything it gets wrong.

## Deliverable

Your SQL file plus a short note (3–5 sentences) to the ACO director: how many members are attributed, and what the assigned-vs-actual mismatch means for care management outreach.
