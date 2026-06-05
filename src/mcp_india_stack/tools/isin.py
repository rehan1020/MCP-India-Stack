"""ISIN (International Securities Identification Number) decoder."""

from __future__ import annotations

from typing import Any

SECURITY_TYPES = {
    "E": "Equity Share",
    "B": "Bond/Debenture",
    "F": "Mutual Fund unit",
    "G": "Government security",
}

DISCLAIMER = "Company name requires a securities master database not bundled here."


def _isin_luhn_valid(isin_clean: str) -> bool:
    """ISIN checksum validation per ISO 6166.

    Steps:
    1. Convert each character: digit stays as-is, letter → two-digit string (A=10, Z=35)
    2. Concatenate all into a flat digit string
    3. Apply standard Luhn algorithm to the full digit string
    """
    # Step 1 & 2: expand to flat digit string
    digit_str = ""
    for ch in isin_clean:
        if ch.isdigit():
            digit_str += ch
        else:
            digit_str += str(ord(ch) - 55)  # A=10, B=11, ..., Z=35

    # Step 3: Luhn algorithm on the full digit string
    digits = [int(d) for d in digit_str]
    # Double every second digit from the right (excluding check digit)
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0


def decode_isin(isin: str) -> dict[str, Any]:
    """Decode ISIN for Indian securities.

    Args:
        isin: 12-character ISIN

    Returns:
        Dict with decoded fields and Luhn validation.
    """
    isin_clean = isin.strip().upper().replace(" ", "")

    if len(isin_clean) != 12:
        return {"valid": False, "error": "ISIN must be 12 characters", "disclaimer": DISCLAIMER}

    country_code = isin_clean[:2]
    nsin = isin_clean[2:]

    luhn_valid = _isin_luhn_valid(isin_clean)

    security_type = "Unknown"
    if country_code == "IN" and nsin[0] in SECURITY_TYPES:
        security_type = SECURITY_TYPES[nsin[0]]

    country = "India" if country_code == "IN" else f"Country code: {country_code}"

    return {
        "valid": luhn_valid,
        "isin": isin_clean,
        "country_code": country_code,
        "country": country,
        "nsin": nsin,
        "checksum_valid": luhn_valid,
        "security_type": security_type,
        "note": "Company name requires securities master database.",
        "disclaimer": DISCLAIMER,
    }
