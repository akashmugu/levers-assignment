"""Integration tests for POST /bills and GET /bills.

These tests run against a real PostgreSQL database to verify query behavior,
database constraints, and API contracts end-to-end.
"""


# ---------------------------------------------------------------------------
# Seed data helpers
# ---------------------------------------------------------------------------

BILL_A = {
    "total": 3,
    "sub_bills": [
        {"amount": 1, "reference": "REF-1"},
        {"amount": 2, "reference": "ref-2"},
    ],
}

BILL_B = {
    "total": 1,
    "sub_bills": [
        {"amount": 1, "reference": "INV-1"},
    ],
}


def _seed(client):
    """Create the two example bills from the assignment."""
    client.post("/bills", json=BILL_A)
    client.post("/bills", json=BILL_B)


# ---------------------------------------------------------------------------
# POST /bills — happy path
# ---------------------------------------------------------------------------


class TestCreateBill:
    def test_create_bill(self, client):
        resp = client.post("/bills", json=BILL_A)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 3
        assert len(body["sub_bills"]) == 2
        assert body["id"] is not None

    def test_create_bill_with_null_reference(self, client):
        payload = {
            "total": 5,
            "sub_bills": [{"amount": 5, "reference": None}],
        }
        resp = client.post("/bills", json=payload)
        assert resp.status_code == 201
        assert resp.json()["sub_bills"][0]["reference"] is None

    def test_create_multiple_null_references(self, client):
        """Multiple sub_bills with null reference should be allowed."""
        payload = {
            "total": 3,
            "sub_bills": [
                {"amount": 1, "reference": None},
                {"amount": 2},
            ],
        }
        resp = client.post("/bills", json=payload)
        assert resp.status_code == 201
        assert len(resp.json()["sub_bills"]) == 2


# ---------------------------------------------------------------------------
# POST /bills — validation errors
# ---------------------------------------------------------------------------


class TestCreateBillValidation:
    def test_empty_sub_bills_rejected(self, client):
        resp = client.post("/bills", json={"total": 0, "sub_bills": []})
        assert resp.status_code == 422

    def test_total_mismatch_rejected(self, client):
        payload = {
            "total": 999,
            "sub_bills": [{"amount": 1, "reference": "X-1"}],
        }
        resp = client.post("/bills", json=payload)
        assert resp.status_code == 422

    def test_missing_total_rejected(self, client):
        resp = client.post("/bills", json={"sub_bills": [{"amount": 1}]})
        assert resp.status_code == 422

    def test_missing_sub_bills_rejected(self, client):
        resp = client.post("/bills", json={"total": 1})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /bills — duplicate reference (case-insensitive)
# ---------------------------------------------------------------------------


class TestDuplicateReference:
    def test_exact_duplicate_rejected(self, client):
        client.post("/bills", json=BILL_A)
        dup = {"total": 1, "sub_bills": [{"amount": 1, "reference": "REF-1"}]}
        resp = client.post("/bills", json=dup)
        assert resp.status_code == 409

    def test_case_insensitive_duplicate_rejected(self, client):
        client.post("/bills", json=BILL_A)
        dup = {"total": 1, "sub_bills": [{"amount": 1, "reference": "ref-1"}]}
        resp = client.post("/bills", json=dup)
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /bills — no filters
# ---------------------------------------------------------------------------


class TestGetBillsNoFilter:
    def test_empty_db_returns_empty_list(self, client):
        resp = client.get("/bills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_bills_with_all_sub_bills(self, client):
        _seed(client)
        resp = client.get("/bills")
        bills = resp.json()
        assert len(bills) == 2
        assert len(bills[0]["sub_bills"]) == 2
        assert len(bills[1]["sub_bills"]) == 1


# ---------------------------------------------------------------------------
# GET /bills?reference= — assignment examples
# ---------------------------------------------------------------------------


class TestReferenceFilter:
    def test_exact_reference(self, client):
        """/bills?reference=ref-1 → one bill, one matching sub_bill."""
        _seed(client)
        resp = client.get("/bills", params={"reference": "ref-1"})
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["total"] == 3
        # Only the matching sub_bill is returned
        assert len(bills[0]["sub_bills"]) == 1
        assert bills[0]["sub_bills"][0]["reference"] == "REF-1"

    def test_substring_multiple_matches(self, client):
        """/bills?reference=ref → matches REF-1 and ref-2 in the same bill."""
        _seed(client)
        resp = client.get("/bills", params={"reference": "ref"})
        bills = resp.json()
        assert len(bills) == 1
        refs = {sb["reference"] for sb in bills[0]["sub_bills"]}
        assert refs == {"REF-1", "ref-2"}

    def test_case_insensitive_match(self, client):
        """/bills?reference=in → matches INV-1 (case-insensitive)."""
        _seed(client)
        resp = client.get("/bills", params={"reference": "in"})
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["sub_bills"][0]["reference"] == "INV-1"

    def test_no_match_returns_empty(self, client):
        _seed(client)
        resp = client.get("/bills", params={"reference": "zzz"})
        assert resp.json() == []

    def test_null_references_not_matched(self, client):
        """Sub_bills with null reference should never match a reference filter."""
        client.post(
            "/bills",
            json={"total": 1, "sub_bills": [{"amount": 1, "reference": None}]},
        )
        resp = client.get("/bills", params={"reference": "none"})
        assert resp.json() == []

    def test_partial_sub_bills_returned(self, client):
        """Only matching sub_bills appear, not all sub_bills of the bill."""
        client.post(
            "/bills",
            json={
                "total": 6,
                "sub_bills": [
                    {"amount": 1, "reference": "MATCH-me"},
                    {"amount": 2, "reference": "skip-this"},
                    {"amount": 3, "reference": "MATCH-too"},
                ],
            },
        )
        resp = client.get("/bills", params={"reference": "match"})
        bills = resp.json()
        assert len(bills) == 1
        refs = {sb["reference"] for sb in bills[0]["sub_bills"]}
        assert refs == {"MATCH-me", "MATCH-too"}


# ---------------------------------------------------------------------------
# GET /bills?total_from= / total_to=
# ---------------------------------------------------------------------------


class TestTotalFilter:
    def test_total_from(self, client):
        _seed(client)
        resp = client.get("/bills", params={"total_from": 3})
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["total"] == 3

    def test_total_to(self, client):
        _seed(client)
        resp = client.get("/bills", params={"total_to": 1})
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["total"] == 1

    def test_total_range(self, client):
        _seed(client)
        resp = client.get("/bills", params={"total_from": 1, "total_to": 3})
        bills = resp.json()
        assert len(bills) == 2

    def test_total_range_no_match(self, client):
        _seed(client)
        resp = client.get("/bills", params={"total_from": 10, "total_to": 20})
        assert resp.json() == []

    def test_total_from_inclusive(self, client):
        """total_from=1 should include a bill with total=1."""
        _seed(client)
        resp = client.get("/bills", params={"total_from": 1})
        totals = {b["total"] for b in resp.json()}
        assert 1 in totals

    def test_total_to_inclusive(self, client):
        """total_to=3 should include a bill with total=3."""
        _seed(client)
        resp = client.get("/bills", params={"total_to": 3})
        totals = {b["total"] for b in resp.json()}
        assert 3 in totals


# ---------------------------------------------------------------------------
# GET /bills — combined filters
# ---------------------------------------------------------------------------


class TestCombinedFilters:
    def test_reference_and_total_from(self, client):
        _seed(client)
        resp = client.get(
            "/bills", params={"reference": "ref", "total_from": 3}
        )
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["total"] == 3

    def test_reference_and_total_excludes(self, client):
        """reference matches but total doesn't → empty."""
        _seed(client)
        resp = client.get(
            "/bills", params={"reference": "ref", "total_from": 10}
        )
        assert resp.json() == []

    def test_all_three_filters(self, client):
        _seed(client)
        resp = client.get(
            "/bills",
            params={"reference": "ref", "total_from": 1, "total_to": 5},
        )
        bills = resp.json()
        assert len(bills) == 1
        assert bills[0]["total"] == 3
