"""Pytest configuration and shared fixtures for MCP India Stack tests."""

from __future__ import annotations

import json
import os
import re
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ============================================================================
# PHASE 6 — Regression Fixtures (fake but structurally valid)
# ============================================================================

# GSTIN fixtures
VALID_GSTIN = "27AAPFU0939F1ZV"  # Valid checksum (Maharashtra)
INVALID_GSTIN_CHECKSUM = "27AAPFU0939F1ZX"  # Bad checksum
INVALID_GSTIN_FORMAT = "INVALID"  # Wrong length
GSTIN_WITH_SPECIAL_CHARS = "  27  AAPFU  0939F  1ZV  "  # Messy input

# PAN fixtures
VALID_PAN = "AAPFU0939F"  # Valid format
INVALID_PAN_FORMAT = "INVALID12"  # Wrong length
VALID_PAN_INDIVIDUAL = "AAAPL1234C"  # Individual (P)
VALID_PAN_COMPANY = "AABCU1234DE"  # Company (C)
VALID_PAN_HUF = "AADDH1234KL"  # HUF (H)
VALID_PAN_FIRM = "AAEFF1234MN"  # Firm (F)
PAN_WITH_SPECIAL_CHARS = "  aapfu  0939f  "  # Messy input, lowercase

# IFSC fixtures
VALID_IFSC = "SBIN0001234"  # Valid format
DEPRECATED_IFSC = "LVCB0000001"  # Lakshmi Vilas Bank (merged)
INVALID_IFSC_FORMAT = "INVALID0123"
IFSC_WITH_SPECIAL_CHARS = "  sbin  0001234  "

# UPI VPA fixtures
VALID_UPI = "testuser@okicici"
VALID_UPI_PAYTM = "testuser@paytm"
INVALID_UPI_NO_AT = "testuserokicici"
UPI_WITH_SPECIAL_CHARS = "  TestUser  @  okicici  "

# Pincode fixtures
VALID_PINCODE = "400001"  # Mumbai
INVALID_PINCODE_SHORT = "40001"  # 5 digits
INVALID_PINCODE_LONG = "4000011"  # 7 digits
PINCODE_WITH_SPECIAL_CHARS = "  400  001  "

# CIN fixtures
VALID_CIN = "U67190TN2014PTC096249"  # Listed company
INVALID_CIN_FORMAT = "INVALID123456789"
CIN_WITH_SPECIAL_CHARS = "  u67190tn2014ptc096249  "

# HSN/SAC fixtures
VALID_HSN_4 = "1001"  # Cereals
VALID_HSN_6 = "100190"  # Wheat
VALID_HSN_8 = "10019000"  # Wheat (specific)
VALID_SAC = "998311"  # Legal services
INVALID_HSN = "999999"

# FSSAI fixtures
VALID_FSSAI = "11223344556677"  # 14-digit
INVALID_FSSAI_SHORT = "112233445566"  # 12-digit

# Aadhaar fixture (fake but valid checksum algorithm)
VALID_AADHAAR = "123456789012"  # 12 digits

# EPF/ESIC fixtures
VALID_EPF = "MH/12345/67890/123"
INVALID_EPF_FORMAT = "INVALID123"
VALID_ESIC = "12-12345-67890"
INVALID_ESIC_FORMAT = "INVALID"

# DigiLocker URI fixtures
VALID_DIGILOCKER_URI = "dlg://uidai/aadhaar"
VALID_DIGILOCKER_PAN = "dlg://incometax/pan"
INVALID_DIGILOCKER_URI = "http://example.com/doc"

# Financial amounts for calculators
SAMPLE_INCOME = 1500000.0
SAMPLE_BASIC_SALARY = 50000.0
SAMPLE_HRA = 180000.0
SAMPLE_RENT = 240000.0

# Date fixtures
EQUITY_STCG_HOLDING = 300  # days (short-term)
EQUITY_LTCG_HOLDING = 400  # days (long-term)


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_success():
    """Mock httpx that returns successful response."""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"found": True, "BANK": "Test Bank"}
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_httpx_not_found():
    """Mock httpx that returns 404."""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_httpx_timeout():
    """Mock httpx that times out."""
    import httpx

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException(
            "timeout"
        )
        yield mock_client


@pytest.fixture
def mock_db_connection():
    """Mock database connection that returns read-only results."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.close.return_value = None
    return mock_conn


@pytest.fixture
def mock_telemetry_file(tmp_path):
    """Create a temporary telemetry file for testing."""
    telemetry_file = tmp_path / "telemetry.jsonl"
    yield str(telemetry_file)
    if telemetry_file.exists():
        telemetry_file.unlink()


# ============================================================================
# Helper Functions
# ============================================================================


def assert_valid_response(response: dict[str, Any]) -> None:
    """Assert a response has all required fields."""
    assert "success" in response, "Response missing 'success' field"
    assert "data" in response, "Response missing 'data' field"
    assert "errors" in response, "Response missing 'errors' field"
    assert "warnings" in response, "Response missing 'warnings' field"
    assert "source" in response, "Response missing 'source' field"
    assert "tool_version" in response, "Response missing 'tool_version' field"


def assert_confidence_scoring(response: dict[str, Any]) -> None:
    """Assert confidence scoring fields are present and valid."""
    if "confidence" in response:
        assert isinstance(response["confidence"], (int, float)), "confidence must be numeric"
        assert 0.0 <= response["confidence"] <= 1.0, "confidence must be between 0.0 and 1.0"

    if "validated_by" in response:
        assert isinstance(response["validated_by"], list), "validated_by must be a list"
        for item in response["validated_by"]:
            assert isinstance(item, str), "validated_by items must be strings"


def assert_normalization(response: dict[str, Any], expected: str) -> None:
    """Assert normalized_input field is correct."""
    assert "normalized_input" in response, "Response missing normalized_input"
    assert response["normalized_input"] == expected, (
        f"Expected '{expected}', got '{response['normalized_input']}'"
    )


# ============================================================================
# Environment Flag Fixtures
# ============================================================================


@pytest.fixture
def dry_run_enabled(monkeypatch):
    """Enable dry-run mode."""
    monkeypatch.setenv("MCP_INDIA_STACK_DRY_RUN", "1")


@pytest.fixture
def live_lookup_enabled(monkeypatch):
    """Enable live lookup."""
    monkeypatch.setenv("MCP_INDIA_STACK_LIVE_LOOKUP", "1")


@pytest.fixture
def db_url_set(monkeypatch):
    """Set DB URL."""
    monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://fake-db:5432/api")


@pytest.fixture
def telemetry_enabled(monkeypatch, mock_telemetry_file):
    """Enable telemetry."""
    monkeypatch.setenv("MCP_INDIA_STACK_LOG", "1")
    monkeypatch.setenv("MCP_INDIA_STACK_LOG_PATH", mock_telemetry_file)
    yield mock_telemetry_file


@pytest.fixture
def bulk_workers_default(monkeypatch):
    """Set default bulk workers."""
    monkeypatch.setenv("MCP_INDIA_STACK_BULK_WORKERS", "10")
