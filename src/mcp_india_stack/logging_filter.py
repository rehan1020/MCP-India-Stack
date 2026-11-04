"""Aadhaar PII masking logging filter and text redaction utilities.

In compliance with the Digital Personal Data Protection Act, 2023 (DPDP Act)
and UIDAI guidelines, 12-digit Aadhaar sequences must be masked to only show
the last 4 digits across logs, exception messages, reprs, and tool outputs.
"""

from __future__ import annotations

import logging
import re

# Match 12-digit formatted numbers with spaces or hyphens: 1234 5678 9012 or 1234-5678-9012
_AADHAAR_FORMATTED_RE = re.compile(r"\b(\d{4})[-\s](\d{4})[-\s](\d{4})\b")

# Match continuous runs of 12 or more digits: 123456789012
_RUN_12_DIGITS_RE = re.compile(r"\b\d{8,}(\d{4})\b")

# Match any un-word-bounded sequence of 12 consecutive digits
_RAW_12_CONSECUTIVE_RE = re.compile(r"\d{8,}(\d{4})")


def mask_aadhaar_text(text: str) -> str:
    """Redact 12-digit Aadhaar sequences to last 4 digits (e.g. 'XXXX XXXX 7261').

    Args:
        text: Any string potentially containing Aadhaar numbers or 12-digit runs.

    Returns:
        Redacted string with all 12-digit numbers masked to last 4 digits.
    """
    if not isinstance(text, str):
        return str(text)

    # 1. Replace 12-digit grouped by spaces or hyphens
    def _rep_formatted(m: re.Match[str]) -> str:
        return f"XXXX XXXX {m.group(3)}"

    redacted = _AADHAAR_FORMATTED_RE.sub(_rep_formatted, text)

    # 2. Replace any continuous 12+ digit sequence
    def _rep_run(m: re.Match[str]) -> str:
        s = m.group(0)
        return "X" * (len(s) - 4) + m.group(1)

    redacted = _RUN_12_DIGITS_RE.sub(_rep_run, redacted)

    # 3. Defensive pass for any remaining 12-digit run without word boundary
    redacted = _RAW_12_CONSECUTIVE_RE.sub(_rep_run, redacted)

    return redacted


class AadhaarMaskingFilter(logging.Filter):
    """Logging filter that redacts 12-digit sequences and Aadhaar PII from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact log records before output."""
        try:
            if isinstance(record.msg, str):
                record.msg = mask_aadhaar_text(record.msg)

            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: mask_aadhaar_text(v) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        mask_aadhaar_text(a) if isinstance(a, str) else a for a in record.args
                    )

            if record.exc_info:
                import traceback

                tb_str = "".join(traceback.format_exception(*record.exc_info))
                record.exc_text = mask_aadhaar_text(tb_str)
                record.exc_info = None
            elif record.exc_text:
                record.exc_text = mask_aadhaar_text(record.exc_text)

        except Exception:
            pass
        return True


def install_aadhaar_masking_filter(logger: logging.Logger | None = None) -> AadhaarMaskingFilter:
    """Install the AadhaarMaskingFilter on a logger (or root logger if None).

    Attaches to both the logger and all existing handlers.
    """
    flt = AadhaarMaskingFilter()
    target = logger or logging.getLogger()

    if not any(isinstance(f, AadhaarMaskingFilter) for f in target.filters):
        target.addFilter(flt)

    for h in target.handlers:
        if not any(isinstance(f, AadhaarMaskingFilter) for f in h.filters):
            h.addFilter(flt)

    # Also attach to 'mcp_india_stack' logger hierarchy
    pkg_logger = logging.getLogger("mcp_india_stack")
    if not any(isinstance(f, AadhaarMaskingFilter) for f in pkg_logger.filters):
        pkg_logger.addFilter(flt)

    return flt


# Install automatically on import
install_aadhaar_masking_filter()
