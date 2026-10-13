"""Data-quality checks on a generated build. Run: pytest -q  (set HEALTH_DB to point at another file)."""
import os
from pathlib import Path

import duckdb
import pytest

DB = os.environ.get("HEALTH_DB", str(Path(__file__).resolve().parents[1] / "output" / "health_analytics.duckdb"))


@pytest.fixture(scope="module")
def con():
    if not Path(DB).exists():
        pytest.skip(f"{DB} not found - run generate.py first")
    c = duckdb.connect(DB, read_only=True)
    yield c
    c.close()


def one(con, sql):
    return con.sql(sql).fetchone()[0]


def test_primary_keys_unique(con):
    for t, k in [("beneficiaries", "member_id"), ("medical_claims", "claim_id"), ("pharmacy_claims", "rx_claim_id"),
                 ("providers", "npi"), ("hospital_payments", "transaction_id"), ("prior_authorizations", "prior_auth_id")]:
        assert one(con, f"select count(*) - count(distinct {k}) from {t}") == 0, t
    assert one(con, "select count(*) - count(distinct (member_id, coverage_month)) from coverage_member_months") == 0


def test_foreign_keys(con):
    checks = [
        "select count(*) from medical_claims c anti join beneficiaries b using (member_id)",
        "select count(*) from pharmacy_claims c anti join beneficiaries b using (member_id)",
        "select count(*) from coverage_member_months c anti join beneficiaries b using (member_id)",
        "select count(*) from medical_claim_lines l anti join medical_claims c using (claim_id)",
        "select count(*) from medical_claims c anti join providers p on c.billing_npi = p.npi",
        "select count(*) from pharmacy_claims c anti join providers p on c.prescriber_npi = p.npi",
        "select count(*) from hospital_payments h anti join medical_claims c using (claim_id)",
        "select count(*) from beneficiaries b anti join zip_area z using (zip_code)",
        "select count(*) from pharmacy_claims r anti join ref_drug d using (ndc)",
    ]
    for s in checks:
        assert one(con, s) == 0, s


def test_insured_claims_have_coverage_or_are_rebills(con):
    # an original claim billed to a plan should match the member's coverage that month, except
    # deliberate wrong-payer billing (denied 27/109) and the fraud scenario of billing after death
    n = one(con, """
        select count(*) from medical_claims c
        left join coverage_member_months m on m.member_id = c.member_id
             and m.coverage_month = date_trunc('month', c.service_from_date) and m.plan_id = c.plan_id
        where c.payer_type <> 'Self-pay' and m.member_id is null
          and coalesce(c.denial_reason_code, '') not in ('27', '109')""")
    total = one(con, "select count(*) from medical_claims")
    assert n / total < 0.002


def test_no_services_after_death_except_fraud(con):
    n = one(con, """
        select count(*) from medical_claims c join beneficiaries b using (member_id)
        join providers p on p.npi = c.billing_npi
        where c.service_from_date > b.death_date and p.provider_name <> 'Keystone Bracing & Supply'""")
    assert n == 0


def test_payment_arithmetic(con):
    bad = one(con, """select count(*) from medical_claims where claim_status in ('Paid','Partially Paid')
                      and abs(total_allowed - total_paid - patient_responsibility - sequestration_amount) > 0.05""")
    assert bad == 0
    assert one(con, "select count(*) from medical_claims where total_allowed > total_charge + 0.01") == 0


def test_ledger_balances_non_negative(con):
    assert one(con, """select count(*) from (select account_id, sum(ar_effect) b from hospital_payments
                       group by 1 having b < -0.05)""") == 0


def test_dates_in_window(con):
    assert one(con, "select min(service_from_date) >= date '2021-01-01' and max(service_from_date) <= date '2025-12-31' from medical_claims")
    assert one(con, "select count(*) from medical_claims c join beneficiaries b using(member_id) where c.service_from_date < b.birth_date") == 0
