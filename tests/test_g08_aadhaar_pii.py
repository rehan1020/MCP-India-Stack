"""Tests for G8: Aadhaar PII masking, logging filter, and DPDP/UIDAI compliance."""

from __future__ import annotations

import io
import logging
import re
from typing import Any

import pytest

from mcp_india_stack.logging_filter import (
    install_aadhaar_masking_filter,
)
from mcp_india_stack.tools.aadhaar import validate_aadhaar
from mcp_india_stack.tools.bulk_aadhaar import bulk_validate_aadhaar

# Strict regex matching any unmasked 12 consecutive digits
TWELVE_DIGIT_RE = re.compile(r"\b\d{12}\b|\d{12}")

SAMPLE_VALID_AADHAAR = "295945837260"  # Valid Verhoeff checksum (ends in 0)


def _assert_no_12_digits(obj: Any) -> None:
    """Recursively verify that no unmasked 12-digit sequence exists in obj."""
    if isinstance(obj, str):
        matches = TWELVE_DIGIT_RE.findall(obj)
        assert not matches, f"Found unmasked 12-digit sequence in string: {obj}"
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_12_digits(k)
            _assert_no_12_digits(v)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            _assert_no_12_digits(item)


class TestAadhaarMasking:
    def test_valid_aadhaar_masked(self) -> None:
        res = validate_aadhaar(SAMPLE_VALID_AADHAAR)
        assert res["valid"] is True
        assert res["masked"] == "XXXX XXXX 7260"
        _assert_no_12_digits(res)

    def test_invalid_checksum_masked(self) -> None:
        # Flip check digit to make checksum invalid
        invalid_num = SAMPLE_VALID_AADHAAR[:-1] + ("1" if SAMPLE_VALID_AADHAAR[-1] == "0" else "0")
        res = validate_aadhaar(invalid_num)
        assert res["valid"] is False
        _assert_no_12_digits(res)

    def test_malformed_inputs(self) -> None:
        test_inputs = [
            "12345678901",  # 11 digits
            "1234567890123",  # 13 digits
            "095945837261",  # Starts with 0
            "195945837261",  # Starts with 1
            "29594583726A",  # Contains letter
            "",
            None,
            "   ",
        ]
        for inp in test_inputs:
            res = validate_aadhaar(inp)  # type: ignore[arg-type]
            assert res["valid"] is False
            _assert_no_12_digits(res)

    def test_exception_handler_masks_pii(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exceptions mentioning raw Aadhaar must be masked before reaching outputs."""
        from mcp_india_stack.tools import aadhaar as aadhaar_module

        def faulty_verhoeff(num: str) -> bool:
            raise RuntimeError(f"Database error while querying {SAMPLE_VALID_AADHAAR}")

        monkeypatch.setattr(aadhaar_module, "_verhoeff_checksum", faulty_verhoeff)
        res = validate_aadhaar(SAMPLE_VALID_AADHAAR)
        assert res["valid"] is False
        assert len(res["errors"]) > 0
        assert "XXXX XXXX 7260" in res["errors"][0] or "XXXX" in res["errors"][0]
        _assert_no_12_digits(res)


class TestBulkAadhaarMasking:
    def test_bulk_aadhaar_all_variants(self) -> None:
        numbers = [
            SAMPLE_VALID_AADHAAR,
            "2959 4583 7261",
            "2959-4583-7261",
            "012345678901",
            "999988887777",
            "short",
            "1234567890123",
            "",
        ]
        res = bulk_validate_aadhaar(numbers)
        assert res["total"] == len(numbers)
        assert len(res["results"]) == len(numbers)
        _assert_no_12_digits(res)

    def test_bulk_aadhaar_exception_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from mcp_india_stack.tools import bulk_aadhaar as bulk_module

        def faulty_single(num: str) -> dict[str, Any]:
            raise ValueError(f"Crash on processing item {SAMPLE_VALID_AADHAAR}")

        monkeypatch.setattr(bulk_module, "_validate_single_aadhaar", faulty_single)
        res = bulk_validate_aadhaar([SAMPLE_VALID_AADHAAR])
        _assert_no_12_digits(res)


class TestLoggingFilter:
    def test_filter_redacts_log_records(self) -> None:
        logger = logging.getLogger("test_aadhaar_logger")
        logger.setLevel(logging.INFO)
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        install_aadhaar_masking_filter(logger)

        logger.info("Validating Aadhaar number %s in system", SAMPLE_VALID_AADHAAR)
        logger.warning("Failed Aadhaar: 2959 4583 7261 with error")
        logger.error("Raw hyphenated 2959-4583-7261 validation failure")

        log_output = stream.getvalue()
        _assert_no_12_digits(log_output)
        assert "XXXX XXXX 7260" in log_output or "XXXXXXXX7260" in log_output

    def test_filter_redacts_exception_info(self) -> None:
        logger = logging.getLogger("test_aadhaar_exc_logger")
        logger.setLevel(logging.INFO)
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        install_aadhaar_masking_filter(logger)

        try:
            raise RuntimeError(f"Processing failed for Aadhaar {SAMPLE_VALID_AADHAAR}")
        except Exception:
            logger.exception("Caught unhandled exception")

        log_output = stream.getvalue()
        _assert_no_12_digits(log_output)


class TestDPDPAandUIDAINotes:
    def test_tool_docstrings_contain_compliance_notes(self) -> None:
        from mcp_india_stack.registrations.kyc import (
            bulk_validate_aadhaar as reg_bulk_aadhaar,
        )
        from mcp_india_stack.registrations.kyc import (
            validate_aadhaar as reg_aadhaar,
        )

        for tool in (reg_aadhaar, reg_bulk_aadhaar, validate_aadhaar, bulk_validate_aadhaar):
            doc = tool.__doc__ or ""
            assert "UIDAI" in doc, f"UIDAI note missing in {tool.__name__}"
            assert "DPDP" in doc, f"DPDP note missing in {tool.__name__}"
