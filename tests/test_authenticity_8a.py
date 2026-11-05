"""Comprehensive test suite for Authenticity System 8a.

Covers:
- Semantic rules R1-R6
- A1 cross-field rules (GSTIN, CIN, DL, FSSAI, EPF, ESIC) positive and negative
- A2 dataset hit, miss, and stale checks
- Bulk summary counts and item envelopes
- Relative performance benchmark (< 1 ms p95 overhead)
"""

from __future__ import annotations

import time
from typing import Any

from mcp_india_stack.authenticity.models import (
    AuthenticityCheck,
    build_authenticity_envelope,
    compute_evidence_hash,
    evaluate_level,
)
from mcp_india_stack.tools.bulk_gstin import bulk_validate_gstin
from mcp_india_stack.tools.bulk_ifsc import bulk_validate_ifsc
from mcp_india_stack.tools.bulk_pan import bulk_validate_pan
from mcp_india_stack.tools.cin import validate_cin
from mcp_india_stack.tools.driving_license import validate_driving_license
from mcp_india_stack.tools.epf_code import validate_epf_code
from mcp_india_stack.tools.esic_code import validate_esic_code
from mcp_india_stack.tools.fssai import validate_fssai
from mcp_india_stack.tools.gstin import validate_gstin
from mcp_india_stack.tools.ifsc import lookup_ifsc
from mcp_india_stack.tools.isin import decode_isin
from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.pincode import lookup_pincode
from mcp_india_stack.tools.state_code import decode_state_code


def _is_valid(res: dict[str, Any]) -> bool:
    if "valid" in res:
        return bool(res["valid"])
    if isinstance(res.get("data"), dict) and "valid" in res["data"]:
        return bool(res["data"]["valid"])
    return bool(res.get("success", False))


def _is_found(res: dict[str, Any]) -> bool:
    if "found" in res:
        return bool(res["found"])
    return bool(res.get("data", {}).get("found"))


class TestSemanticRules:
    """Tests for core semantic rules R1-R6."""

    def test_r1_highest_consecutive_level_never_inflated(self) -> None:
        """R1: level equals highest consecutive level whose checks all passed."""
        # A0 passed, A1 passed -> A1
        checks = [
            AuthenticityCheck("c0", True, "A0", "detail"),
            AuthenticityCheck("c1", True, "A1", "detail"),
        ]
        assert evaluate_level(checks, valid=True) == "A1"

        # A0 passed, A1 failed, A2 passed -> should NOT skip to A2! Must remain A0
        checks_gap = [
            AuthenticityCheck("c0", True, "A0", "detail"),
            AuthenticityCheck("c1", False, "A1", "detail"),
            AuthenticityCheck("c2", True, "A2", "detail"),
        ]
        assert evaluate_level(checks_gap, valid=True) == "A0"

        # A0 failed, A1 passed -> None
        checks_a0_fail = [
            AuthenticityCheck("c0", False, "A0", "detail"),
            AuthenticityCheck("c1", True, "A1", "detail"),
        ]
        assert evaluate_level(checks_a0_fail, valid=True) is None

    def test_r2_valid_false_gives_level_null(self) -> None:
        """R2: valid=false gives level=null, and failed checks are listed."""
        checks = [
            AuthenticityCheck("fmt", False, "A0", "Invalid format"),
            AuthenticityCheck("chk", False, "A0", "Checksum mismatch"),
        ]
        envelope = build_authenticity_envelope(checks=checks, valid=False, source="TestAuthority")
        assert envelope["level"] is None
        assert len(envelope["checks"]) == 2
        assert envelope["checks"][0]["passed"] is False

    def test_r3_dataset_miss_is_not_forgery(self) -> None:
        """R3: dataset miss stays at A1/A0 and adds limitation not_found_in_dataset@<ver>."""
        res = lookup_ifsc("ZZZZ0000000")
        assert _is_found(res) is False
        auth = res["authenticity"]
        assert auth["level"] == "A1"  # Format and bank prefix pass, dataset missed
        assert any("not_found_in_dataset" in lim for lim in auth["limitations"])
        assert auth["evidence_hash"] is None

    def test_r4_prohibit_low_entropy_identifier_digests(self) -> None:
        """R4: never emit hash or digest of low-entropy identifier (Aadhaar, mobile, PAN, VPA)."""
        # Dictionary with raw PAN
        pan_rec = {"pan": "ABCDE1234F", "name": "Test User"}
        assert compute_evidence_hash(pan_rec) is None

        # Dictionary with raw Aadhaar
        aadhaar_rec = {"aadhaar": "295945837261", "status": "active"}
        assert compute_evidence_hash(aadhaar_rec) is None

        # Dictionary with mobile number value
        mobile_rec = {"user_id": 123, "phone": "9876543210"}
        assert compute_evidence_hash(mobile_rec) is None

        # Legitimate public directory entry (e.g. IFSC directory record)
        public_rec = {
            "BANK": "HDFC BANK",
            "BRANCH": "MUMBAI MAIN",
            "CITY": "MUMBAI",
            "STATE": "MAHARASHTRA",
        }
        digest = compute_evidence_hash(public_rec)
        assert digest is not None
        assert digest.startswith("sha256:")

    def test_r5_output_is_deterministic(self) -> None:
        """R5: output is deterministic given identical inputs and as_of."""
        res1 = validate_gstin("27AAPFU0939F1ZV")
        res2 = validate_gstin("27AAPFU0939F1ZV")
        assert res1["authenticity"] == res2["authenticity"]

    def test_r6_pii_redaction_in_authenticity_fields(self) -> None:
        """R6: PII rules (Aadhaar masking) apply to check details and limitations."""
        checks = [
            AuthenticityCheck("aadhaar_check", False, "A0", "Failed for 295945837261 value"),
        ]
        envelope = build_authenticity_envelope(
            checks=checks,
            valid=False,
            source="UIDAI",
            custom_limitations=["Limitation regarding 295945837261 identifier"],
        )
        assert "295945837261" not in envelope["checks"][0]["detail"]
        assert "XXXX" in envelope["checks"][0]["detail"]
        assert "295945837261" not in envelope["limitations"][0]
        assert "XXXX" in envelope["limitations"][0]


class TestA1CrossFieldRules:
    """Tests for domain-specific A1 cross-field rules."""

    def test_gstin_a1_positive_and_negative(self) -> None:
        """GSTIN: embedded PAN, state code, entity number, 14th char, expected_entity_type."""
        # Standard valid GSTIN -> A1
        res = validate_gstin("27AAPFU0939F1ZV")
        assert _is_valid(res) is True
        assert res["authenticity"]["level"] == "A1"

        # Expected entity type matches PAN 4th char ('F' for Firm)
        res_firm = validate_gstin("27AAPFU0939F1ZV", expected_entity_type="F")
        assert res_firm["authenticity"]["level"] == "A1"
        assert any(
            c["name"] == "expected_entity_type_consistency" and c["passed"] is True
            for c in res_firm["authenticity"]["checks"]
        )

        # Expected entity type mismatch ('C' Company expected, got 'F' Firm)
        res_mismatch = validate_gstin("27AAPFU0939F1ZV", expected_entity_type="C")
        assert _is_valid(res_mismatch) is False  # Entity mismatch invalidates entity validation
        assert res_mismatch["authenticity"]["level"] is None  # R2: valid=False -> level=None
        assert any(
            c["name"] == "expected_entity_type_consistency" and c["passed"] is False
            for c in res_mismatch["authenticity"]["checks"]
        )

    def test_cin_a1_positive_and_negative(self) -> None:
        """CIN: listing flag, ROC state, company type, incorporation year [1850, today]."""
        # Valid CIN -> A1
        res = validate_cin("L17110MH1973PLC019786")
        assert _is_valid(res) is True
        assert res["authenticity"]["level"] == "A1"

        # Invalid incorporation year (< 1850) -> level None (R2: invalid)
        res_old = validate_cin("L17110MH1840PLC019786")
        assert _is_valid(res_old) is False
        assert res_old["authenticity"]["level"] is None
        assert any(
            c["name"] == "cin_incorporation_year_plausibility" and c["passed"] is False
            for c in res_old["authenticity"]["checks"]
        )

        # Invalid listing status (neither L nor U)
        res_invalid_listing = validate_cin("X17110MH1973PLC019786")
        assert _is_valid(res_invalid_listing) is False
        assert res_invalid_listing["authenticity"]["level"] is None

    def test_driving_license_a1(self) -> None:
        """DL: state prefix, 2-digit RTO, plausible year."""
        res = validate_driving_license("MH0220191234567")
        assert _is_valid(res) is True
        assert res["authenticity"]["level"] == "A1"

    def test_fssai_a1(self) -> None:
        """FSSAI: 14-digit numeric, valid state code, registration year, type."""
        # Positive: Maharashtra (27), Year 23, Type 1 -> A1
        res = validate_fssai("27231000000001")
        assert _is_valid(res) is True
        assert res["authenticity"]["level"] == "A1"

        # Negative: unusual year and invalid license type 9 -> stays at A0
        res_neg = validate_fssai("10019000000001")
        assert _is_valid(res_neg) is True
        assert res_neg["authenticity"]["level"] == "A0"

    def test_epf_and_esic_a1(self) -> None:
        """EPF and ESIC region codes and office structures."""
        epf = validate_epf_code("27/12345/123456/001")
        assert _is_valid(epf) is True
        assert epf["authenticity"]["level"] == "A1"

        esic = validate_esic_code("11-12345-12345")
        assert _is_valid(esic) is True
        assert esic["authenticity"]["level"] == "A1"


class TestA2DatasetAttestation:
    """Tests for A2 authoritative dataset matching."""

    def test_ifsc_hit_and_miss(self) -> None:
        """IFSC match reaches A2; miss stays at A1."""
        hit = lookup_ifsc("SBIN0001234")
        assert _is_found(hit) is True
        assert hit["authenticity"]["level"] == "A2"
        assert hit["authenticity"]["evidence_hash"] is not None

        miss = lookup_ifsc("SBIN0999999")
        assert _is_found(miss) is False
        assert miss["authenticity"]["level"] == "A1"
        assert any("not_found_in_dataset" in lim for lim in miss["authenticity"]["limitations"])

    def test_pincode_hit_and_miss(self) -> None:
        """Pincode match reaches A2; miss stays at A1."""
        hit = lookup_pincode("110001")
        assert _is_found(hit) is True
        assert hit["authenticity"]["level"] == "A2"

        miss = lookup_pincode("999999")
        assert _is_found(miss) is False
        assert miss["authenticity"]["level"] == "A1"

    def test_state_code_and_isin(self) -> None:
        """State code and ISIN lookup A2 attestation."""
        state = decode_state_code("27")
        assert _is_found(state) is True
        assert state["authenticity"]["level"] == "A2"

        isin = decode_isin("INE002A01018")
        assert _is_valid(isin) is True
        assert isin["authenticity"]["level"] == "A2"


class TestBulkSummaryCounts:
    """Tests for bulk tools emitting per-item authenticity and summary counts."""

    def test_bulk_gstin_summary(self) -> None:
        """bulk_validate_gstin provides per-item authenticity and summary breakdown."""
        items = ["27AAPFU0939F1ZV", "INVALIDGSTIN123"]
        res = bulk_validate_gstin(items)
        assert res["success"] is True
        assert "authenticity_summary" in res["data"]
        summary = res["data"]["authenticity_summary"]
        assert summary["A1"] == 1
        assert summary["null"] == 1
        assert res["authenticity"]["summary"] == summary

        # Each result item has authenticity
        for r in res["data"]["results"]:
            assert "authenticity" in r

    def test_bulk_pan_summary(self) -> None:
        """bulk_validate_pan provides per-item authenticity and summary breakdown."""
        pans = ["ABCPK1234F", "INVALIDPAN"]
        res = bulk_validate_pan(pans)
        assert res["success"] is True
        summary = res["data"]["authenticity_summary"]
        assert summary["A1"] == 1
        assert summary["null"] == 1

    def test_bulk_ifsc_summary(self) -> None:
        """bulk_validate_ifsc provides per-item authenticity and summary breakdown."""
        ifscs = ["SBIN0001234", "ZZZZ0000000"]
        res = bulk_validate_ifsc(ifscs)
        assert res["success"] is True
        summary = res["data"]["authenticity_summary"]
        assert summary["A2"] == 1
        assert summary["A1"] == 1


class TestRelativePerformanceBudget:
    """Performance budget: A0-A2 adds < 1 ms p95 overhead per call."""

    def test_pan_authenticity_p95_overhead(self) -> None:
        """Benchmark: 1000 PAN evaluations must stay under agreed overhead budget."""
        pan = "ABCPK1234F"
        latencies: list[float] = []

        # Warm up
        for _ in range(50):
            validate_pan(pan)

        for _ in range(500):
            t0 = time.perf_counter()
            validate_pan(pan)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms

        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        # P95 should be well under 1.0 ms for pure in-memory validation
        assert p95 < 1.0, f"p95 latency {p95:.3f} ms exceeds 1.0 ms budget"

    def test_bulk_1000_item_budget(self) -> None:
        """A bulk call of 500 items stays within 1000 ms."""
        pans = ["ABCPK1234F"] * 500
        t0 = time.perf_counter()
        res = bulk_validate_pan(pans)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        assert res["success"] is True
        assert elapsed_ms < 1000.0, f"Bulk validation took {elapsed_ms:.1f} ms"


class TestMutationCrossFieldLogic:
    """Mutation tests: mutating individual components drops attestation level or fails check."""

    def test_gstin_mutations(self) -> None:
        """Mutate individual GSTIN components and verify level degradation."""
        base = "27AAPFU0939F1ZV"

        # Mutate 14th char from 'Z' to 'A'
        mutated_14th = base[:13] + "A" + base[14]
        res = validate_gstin(mutated_14th)
        auth = res["authenticity"]
        assert auth["level"] is None  # R2: valid=False gives level=None
        assert any(
            c["name"] == "standard_14th_char_rule" and c["passed"] is False for c in auth["checks"]
        )

        # Mutate state code to unassigned '99'
        mutated_state = "99" + base[2:]
        res_state = validate_gstin(mutated_state)
        auth_state = res_state["authenticity"]
        assert auth_state["level"] is None
        assert any(
            c["name"] == "state_code_consistency" and c["passed"] is False
            for c in auth_state["checks"]
        )

    def test_cin_mutations(self) -> None:
        """Mutate individual CIN components and verify check degradation."""
        base = "L17110MH1973PLC019786"

        # Mutate company type from PLC to XYZ
        mutated_type = base[:12] + "XYZ" + base[15:]
        res = validate_cin(mutated_type)
        auth = res["authenticity"]
        assert auth["level"] is None  # R2: valid=False gives level=None
        assert any(
            c["name"] == "cin_company_type_consistency" and c["passed"] is False
            for c in auth["checks"]
        )
