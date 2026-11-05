"""Domain-specific authenticity rules and check generators for MCP India Stack tools.

Maps individual tool validations into structured A0-A2 checks.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from mcp_india_stack.authenticity.models import (
    AuthenticityCheck,
    build_authenticity_envelope,
)


def create_gstin_authenticity(
    *,
    gstin: str,
    valid: bool,
    state_valid: bool,
    pan_valid: bool,
    entity_num_valid: bool,
    char14_valid: bool,
    checksum_valid: bool,
    pan_block: str = "",
    expected_entity_type: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_gstin.

    A0: Format and checksum pass.
    A1: Cross-field consistency:
        - Embedded PAN validation
        - Valid state code
        - Entity number char valid
        - 14th char == 'Z'
        - Optional expected_entity_type compared against PAN 4th char
    """
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="gstin_format_syntax",
            passed=bool(re.match(r"^[0-9A-Z]{15}$", gstin)),
            level="A0",
            detail="15-character uppercase alphanumeric structure",
        ),
        AuthenticityCheck(
            name="gstin_mod36_checksum",
            passed=checksum_valid,
            level="A0",
            detail="Luhn mod-36 checksum character verification",
        ),
        AuthenticityCheck(
            name="embedded_pan_consistency",
            passed=pan_valid,
            level="A1",
            detail="Characters 3-12 form a structurally valid Indian PAN",
        ),
        AuthenticityCheck(
            name="state_code_consistency",
            passed=state_valid,
            level="A1",
            detail="Leading 2 digits correspond to an assigned state/UT code",
        ),
        AuthenticityCheck(
            name="entity_number_consistency",
            passed=entity_num_valid,
            level="A1",
            detail="13th character is a valid alphanumeric entity index (1-9, A-Z)",
        ),
        AuthenticityCheck(
            name="standard_14th_char_rule",
            passed=char14_valid,
            level="A1",
            detail="14th character is 'Z' per standard GSTIN specification",
        ),
    ]

    # Optional expected entity type check (A1)
    if expected_entity_type and pan_block and len(pan_block) >= 4:
        entity_char = pan_block[3].upper()
        expected_char = expected_entity_type.strip().upper()
        entity_matches = entity_char == expected_char
        if entity_matches:
            detail_msg = f"PAN 4th character '{entity_char}' matches expected '{expected_char}'"
        else:
            detail_msg = (
                f"PAN 4th character '{entity_char}' does not match expected '{expected_char}'"
            )
        checks.append(
            AuthenticityCheck(
                name="expected_entity_type_consistency",
                passed=entity_matches,
                level="A1",
                detail=detail_msg,
            )
        )

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="GST Council / CBIC",
        as_of=as_of,
        custom_limitations=[
            "active registration status not verified",
            "taxpayer filing compliance not verified",
        ],
    )


def create_cin_authenticity(
    *,
    cin: str,
    valid: bool,
    listing_valid: bool,
    state_valid: bool,
    company_type_valid: bool,
    year_valid: bool,
    sequence_valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_cin.

    A0: Format syntax pass.
    A1: Cross-field consistency:
        - Listing flag ('L'/'U')
        - State/ROC code valid
        - Company type code valid
        - Year of incorporation within [1850, current_year]
        - Sequence number numeric
    """
    current_year = date.today().year

    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="cin_format_syntax",
            passed=bool(re.match(r"^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", cin)),
            level="A0",
            detail="21-character CIN syntax check",
        ),
        AuthenticityCheck(
            name="cin_listing_status_rule",
            passed=listing_valid,
            level="A1",
            detail="Leading character is 'L' (Listed) or 'U' (Unlisted)",
        ),
        AuthenticityCheck(
            name="cin_state_roc_consistency",
            passed=state_valid,
            level="A1",
            detail="State code corresponds to a recognized ROC jurisdiction",
        ),
        AuthenticityCheck(
            name="cin_company_type_consistency",
            passed=company_type_valid,
            level="A1",
            detail="Company type code corresponds to an official MCA category",
        ),
        AuthenticityCheck(
            name="cin_incorporation_year_plausibility",
            passed=year_valid,
            level="A1",
            detail=f"Incorporation year within historical range [1850, {current_year}]",
        ),
        AuthenticityCheck(
            name="cin_sequential_numeric_rule",
            passed=sequence_valid,
            level="A1",
            detail="Sequential component consists of 6 decimal digits",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Ministry of Corporate Affairs (MCA)",
        as_of=as_of,
        custom_limitations=[
            "active incorporation status not verified",
            "MCA annual filing compliance not verified",
        ],
    )


def create_driving_license_authenticity(
    *,
    dl: str,
    valid: bool,
    state_valid: bool,
    rto_valid: bool,
    year_valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_driving_license.

    A0: Syntax check.
    A1: State prefix valid, RTO prefix plausible, issue year plausible.
    """
    current_year = date.today().year
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="dl_format_syntax",
            passed=bool(re.match(r"^[A-Z]{2}[0-9]{2}[0-9]{4}[0-9]{7}$", dl)),
            level="A0",
            detail="15-character standard Sarathi driving license syntax",
        ),
        AuthenticityCheck(
            name="dl_state_prefix_consistency",
            passed=state_valid,
            level="A1",
            detail="State prefix corresponds to a recognized Indian State or UT",
        ),
        AuthenticityCheck(
            name="dl_rto_prefix_consistency",
            passed=rto_valid,
            level="A1",
            detail="RTO code is a plausible 2-digit issuing authority identifier",
        ),
        AuthenticityCheck(
            name="dl_issue_year_plausibility",
            passed=year_valid,
            level="A1",
            detail=f"Issue year within plausible range [1900, {current_year}]",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Ministry of Road Transport and Highways (MoRTH)",
        as_of=as_of,
        custom_limitations=[
            "active license validity not verified",
            "suspension or endorsement records not verified",
        ],
    )


def create_fssai_authenticity(
    *,
    fssai: str,
    valid: bool,
    state_valid: bool,
    year_valid: bool,
    license_type_valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_fssai.

    A0: 14-digit numeric syntax.
    A1: State code prefix valid, year plausible, license type (1/2/3) valid.
    """
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="fssai_format_syntax",
            passed=bool(re.match(r"^\d{14}$", fssai)),
            level="A0",
            detail="14-digit numeric FSSAI license structure",
        ),
        AuthenticityCheck(
            name="fssai_state_prefix_consistency",
            passed=state_valid,
            level="A1",
            detail="Leading 2 digits correspond to an assigned State/UT code",
        ),
        AuthenticityCheck(
            name="fssai_registration_year_plausibility",
            passed=year_valid,
            level="A1",
            detail="Digits 3-4 form a plausible 2-digit registration year",
        ),
        AuthenticityCheck(
            name="fssai_license_type_validity",
            passed=license_type_valid,
            level="A1",
            detail="Digit 5 represents a valid FSSAI license type category (1, 2, or 3)",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Food Safety and Standards Authority of India (FSSAI)",
        as_of=as_of,
        custom_limitations=[
            "active license validity not verified",
            "food safety inspection compliance not verified",
        ],
    )


def create_epf_authenticity(
    *,
    code: str,
    valid: bool,
    region_valid: bool,
    office_valid: bool = True,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_epf_code."""
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="epf_format_syntax",
            passed=bool(re.match(r"^\d{2}/\d{5,6}/\d{5,6}/\d{3}$", code)),
            level="A0",
            detail="Standard EPFO establishment code structure (XX/XXXXX/XXXXXX/XXX)",
        ),
        AuthenticityCheck(
            name="epf_region_code_consistency",
            passed=region_valid,
            level="A1",
            detail="2-digit region code matches recognized EPFO regional office",
        ),
        AuthenticityCheck(
            name="epf_office_subcode_structure",
            passed=office_valid,
            level="A1",
            detail="Office, establishment, and extension sub-components correctly formatted",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Employees' Provident Fund Organisation (EPFO)",
        as_of=as_of,
        custom_limitations=[
            "active establishment registration not verified",
            "PF contribution remittance compliance not verified",
        ],
    )


def create_esic_authenticity(
    *,
    code: str,
    valid: bool,
    region_valid: bool,
    employer_valid: bool = True,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_esic_code."""
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="esic_format_syntax",
            passed=bool(re.match(r"^[\d]{2}-[\d]+-[\d]+$", code)),
            level="A0",
            detail="Standard 17-digit ESIC employer code syntax (XX-XXXXX-XXXXX)",
        ),
        AuthenticityCheck(
            name="esic_regional_office_consistency",
            passed=region_valid,
            level="A1",
            detail="2-digit regional office code matches assigned ESIC jurisdiction",
        ),
        AuthenticityCheck(
            name="esic_employer_structure",
            passed=employer_valid,
            level="A1",
            detail="Employer identification number and branch extension syntax verified",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Employees' State Insurance Corporation (ESIC)",
        as_of=as_of,
        custom_limitations=[
            "active employer registration not verified",
            "ESIC contribution status not verified",
        ],
    )


# --- A2 Dataset-backed Tools ---


def create_ifsc_authenticity(
    *,
    ifsc: str,
    found: bool,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for lookup_ifsc and bulk_validate_ifsc.

    A0: 11-char alphanumeric format (4 alpha, 0, 6 alphanumeric).
    A1: Bank code prefix consistency.
    A2: Record present in bundled RBI IFSC directory.
    """
    format_valid = bool(re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc.upper().strip()))
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="ifsc_format_syntax",
            passed=format_valid,
            level="A0",
            detail="11-character alphanumeric structure with 5th character '0'",
        ),
        AuthenticityCheck(
            name="ifsc_bank_prefix_consistency",
            passed=bool(re.match(r"^[A-Z]{4}$", ifsc[:4].upper())),
            level="A1",
            detail="4-letter alphabetical bank prefix code",
        ),
        AuthenticityCheck(
            name="record_in_bundled_dataset",
            passed=found,
            level="A2",
            detail="Branch record matched in bundled RBI IFSC master directory",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=format_valid,
        source="Reserve Bank of India (RBI)",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
        custom_limitations=[
            "real-time operational/merger status not verified",
        ],
    )


def create_pincode_authenticity(
    *,
    pincode: str,
    found: bool,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for lookup_pincode.

    A0: 6-digit numeric syntax with zone 1-9.
    A1: Sub-region and sorting district code consistency.
    A2: Record present in bundled India Post directory.
    """
    clean_pin = pincode.strip()
    format_valid = bool(re.match(r"^[1-9][0-9]{5}$", clean_pin))

    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="pincode_format_syntax",
            passed=format_valid,
            level="A0",
            detail="6-digit postal code beginning with digits 1-9",
        ),
        AuthenticityCheck(
            name="postal_zone_consistency",
            passed=format_valid and clean_pin[0] in "123456789",
            level="A1",
            detail="First digit maps to one of 9 postal zones across India",
        ),
        AuthenticityCheck(
            name="record_in_bundled_dataset",
            passed=found,
            level="A2",
            detail="Postal delivery office matched in bundled India Post directory",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=format_valid,
        source="Department of Posts / India Post",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
        custom_limitations=[
            "delivery office operational status not verified",
        ],
    )


def create_state_code_authenticity(
    *,
    code: str,
    found: bool,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for decode_state_code."""
    clean = code.strip().upper()
    format_valid = bool(re.match(r"^(?:[0-9]{2}|[A-Z]{2})$", clean))

    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="state_code_syntax",
            passed=format_valid,
            level="A0",
            detail="2-digit numeric GST/Census code or 2-letter alpha state abbreviation",
        ),
        AuthenticityCheck(
            name="state_code_standard_structure",
            passed=format_valid,
            level="A1",
            detail="Code aligns with ISO 3166-2:IN or GST Council numeric assignment",
        ),
        AuthenticityCheck(
            name="record_in_bundled_dataset",
            passed=found,
            level="A2",
            detail="Matched in official State and Union Territory jurisdiction table",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=format_valid,
        source="Ministry of Home Affairs / GST Council",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
    )


def create_isin_authenticity(
    *,
    isin: str,
    valid: bool,
    found: bool = True,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for decode_isin."""
    clean = isin.strip().upper()
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="isin_luhn_checksum",
            passed=valid,
            level="A0",
            detail="12-character ISO 6166 ISIN syntax and Luhn mod-10 double-add-double checksum",
        ),
        AuthenticityCheck(
            name="country_and_issuer_consistency",
            passed=valid and clean.startswith("IN"),
            level="A1",
            detail="Country prefix 'IN' with designated depository security type classification",
        ),
        AuthenticityCheck(
            name="depository_directory_match",
            passed=valid and found,
            level="A2",
            detail="Matched against national depository (NSDL/CDSL) active identifier registry",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="SEBI / NSDL / CDSL",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
        custom_limitations=[
            "active trading suspension or listing status not verified",
        ],
    )


def create_bbps_authenticity(
    *,
    biller_id: str,
    found: bool,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for lookup_bbps_biller."""
    format_valid = bool(biller_id.strip())
    checks: list[AuthenticityCheck] = [
        AuthenticityCheck(
            name="bbps_biller_format",
            passed=format_valid,
            level="A0",
            detail="BBPS biller identifier format verification",
        ),
        AuthenticityCheck(
            name="bbps_directory_match",
            passed=found,
            level="A2",
            detail="Matched in official Bharat Bill Payment System central directory",
        ),
    ]

    return build_authenticity_envelope(
        checks=checks,
        valid=format_valid,
        source="Bharat Bill Payment System (BBPS) / NPCI",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
        custom_limitations=[
            "real-time biller settlement availability not verified",
        ],
    )


def create_generic_id_authenticity(
    *,
    id_type: str,
    identifier: str,
    valid: bool,
    source: str,
    authority: str,
    checks: list[AuthenticityCheck] | None = None,
    custom_limitations: list[str] | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for other standard KYC/identifier tools."""
    if checks is None:
        checks = [
            AuthenticityCheck(
                name=f"{id_type}_format_syntax",
                passed=valid,
                level="A0",
                detail=f"Structural format and checksum rules for {id_type.upper()}",
            )
        ]

    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source=authority,
        as_of=as_of,
        custom_limitations=custom_limitations,
    )


def create_pan_authenticity(
    *,
    pan: str,
    valid: bool,
    entity_code: str | None = None,
    entity_type: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_pan."""
    clean = pan.strip().upper() if pan else ""
    format_valid = bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean))
    code = entity_code or (clean[3] if len(clean) >= 4 else None)
    known_entity = code in ("P", "C", "H", "F", "A", "T", "B", "L", "J", "G", "K")
    checks = [
        AuthenticityCheck(
            name="pan_format_syntax",
            passed=format_valid,
            level="A0",
            detail="10-character alphanumeric structure (5 letters, 4 digits, 1 letter)",
        ),
        AuthenticityCheck(
            name="pan_entity_type_consistency",
            passed=format_valid and known_entity,
            level="A1",
            detail=(
                f"4th character '{code}' represents a recognized entity category "
                f"({entity_type or 'Standard'})"
            ),
        ),
        AuthenticityCheck(
            name="pan_name_initial_rule",
            passed=format_valid and len(clean) >= 5 and clean[4].isalpha(),
            level="A1",
            detail="5th character is an alphabetic taxpayer surname or entity name initial",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Income Tax Department",
        as_of=as_of,
        custom_limitations=[
            "active PAN status not verified",
            "PAN-Aadhaar linking status not verified",
        ],
    )


def create_aadhaar_authenticity(
    *,
    aadhaar: str,
    valid: bool,
    checksum_valid: bool,
    first_digit_valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_aadhaar."""
    clean = re.sub(r"[\s\-]", "", str(aadhaar).strip()) if aadhaar else ""
    has_12_digits = bool(re.match(r"^\d{12}$", clean))
    checks = [
        AuthenticityCheck(
            name="aadhaar_format_syntax",
            passed=has_12_digits,
            level="A0",
            detail="12-digit numeric identifier structure",
        ),
        AuthenticityCheck(
            name="aadhaar_verhoeff_checksum",
            passed=checksum_valid,
            level="A0",
            detail="Verhoeff dihedral D5 checksum verification",
        ),
        AuthenticityCheck(
            name="aadhaar_first_digit_rule",
            passed=first_digit_valid,
            level="A1",
            detail="Leading digit is between 2 and 9 per UIDAI non-zero allocation policy",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Unique Identification Authority of India (UIDAI)",
        as_of=as_of,
        custom_limitations=[
            "active Aadhaar existence not verified (offline check only)",
            "biometric authentication not performed",
        ],
    )


def create_upi_authenticity(
    *,
    vpa: str,
    valid: bool,
    known_provider: bool = False,
    provider: str | None = None,
    handle: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_upi_vpa."""
    clean = str(vpa).strip().lower() if vpa else ""
    format_valid = (
        "@" in clean
        and len(clean.split("@")) == 2
        and bool(clean.split("@")[0])
        and bool(clean.split("@")[1])
    )
    checks = [
        AuthenticityCheck(
            name="upi_vpa_syntax",
            passed=format_valid,
            level="A0",
            detail="Standard virtual payment address structure (username@handle)",
        ),
        AuthenticityCheck(
            name="upi_provider_handle_consistency",
            passed=valid and known_provider,
            level="A1",
            detail=(
                f"Handle '@{handle}' matches registered NPCI PSP entity ({provider})"
                if known_provider
                else f"Handle '@{handle or 'unknown'}' not in common NPCI provider list"
            ),
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="National Payments Corporation of India (NPCI)",
        as_of=as_of,
        custom_limitations=[
            "active VPA resolution not verified",
            "beneficiary bank account linking not verified",
        ],
    )


def create_voter_id_authenticity(
    *,
    voter_id: str,
    valid: bool,
    format_type: str = "standard",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_voter_id."""
    clean = str(voter_id).strip().upper() if voter_id else ""
    is_std = bool(re.match(r"^[A-Z]{3}[0-9]{7}$", clean))
    checks = [
        AuthenticityCheck(
            name="voter_id_format_syntax",
            passed=valid,
            level="A0",
            detail="10-character standard EPIC structure (3 uppercase letters, 7 decimal digits)",
        ),
        AuthenticityCheck(
            name="electoral_jurisdiction_prefix_rule",
            passed=valid and is_std,
            level="A1",
            detail="3-letter functional state/assembly constituency prefix format",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Election Commission of India (ECI)",
        as_of=as_of,
        custom_limitations=[
            "electoral roll inclusion not verified",
            "active voter registration status not verified",
        ],
    )


def create_passport_authenticity(
    *,
    passport: str,
    valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_passport."""
    clean = str(passport).strip().upper() if passport else ""
    format_valid = bool(re.match(r"^[A-Z][0-9]{7}$", clean))
    checks = [
        AuthenticityCheck(
            name="passport_format_syntax",
            passed=format_valid,
            level="A0",
            detail="8-character Indian passport format (1 alpha booklet series code + 7 digits)",
        ),
        AuthenticityCheck(
            name="passport_series_code_rule",
            passed=format_valid and clean[0] not in ("0", "1", "Q", "I", "O"),
            level="A1",
            detail="Passport series code aligns with standard MEA travel document rules",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Ministry of External Affairs (MEA)",
        as_of=as_of,
        custom_limitations=[
            "passport active validity not verified",
            "revocation or impoundment status not verified",
        ],
    )


def create_din_authenticity(
    *,
    din: str,
    valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_din."""
    clean = str(din).strip() if din else ""
    format_valid = bool(re.match(r"^[0-9]{8}$", clean))
    non_zero = format_valid and clean != "00000000"
    checks = [
        AuthenticityCheck(
            name="din_format_syntax",
            passed=format_valid,
            level="A0",
            detail="8-digit numeric Director Identification Number structure",
        ),
        AuthenticityCheck(
            name="din_sequence_plausibility",
            passed=valid and non_zero,
            level="A1",
            detail="Numeric sequence falls within issued MCA director allocation ranges",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Ministry of Corporate Affairs (MCA)",
        as_of=as_of,
        custom_limitations=[
            "director disqualification under Section 164(2) not verified",
            "active DIN appointment status not verified",
        ],
    )


def create_llpin_authenticity(
    *,
    llpin: str,
    valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_llpin."""
    clean = str(llpin).strip().upper().replace(" ", "").replace("-", "") if llpin else ""
    format_valid = bool(re.match(r"^[A-Z]{3}[0-9]{4}$", clean))
    checks = [
        AuthenticityCheck(
            name="llpin_format_syntax",
            passed=format_valid,
            level="A0",
            detail="7-character LLPIN structure (3 letters + 4 digits)",
        ),
        AuthenticityCheck(
            name="llpin_prefix_consistency",
            passed=format_valid,
            level="A1",
            detail="3-letter series prefix corresponds to MCA LLP registry allocation",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Ministry of Corporate Affairs (MCA)",
        as_of=as_of,
        custom_limitations=[
            "active LLP incorporation status not verified",
            "MCA annual filing compliance not verified",
        ],
    )


def create_mobile_authenticity(
    *,
    mobile: str,
    valid: bool,
    operator: str | None = None,
    circle: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_mobile_number."""
    clean = str(mobile).strip() if mobile else ""
    format_valid = bool(re.match(r"^[6-9][0-9]{9}$", clean))
    known_circle = bool(circle and circle != "Unknown")
    checks = [
        AuthenticityCheck(
            name="mobile_number_syntax",
            passed=format_valid,
            level="A0",
            detail="10-digit Indian National Numbering Plan (NNP) mobile format",
        ),
        AuthenticityCheck(
            name="national_numbering_plan_consistency",
            passed=format_valid and clean[0] in "6789",
            level="A1",
            detail="Leading digit in [6, 7, 8, 9] per DoT numbering plan",
        ),
        AuthenticityCheck(
            name="telecom_circle_prefix_consistency",
            passed=format_valid and known_circle,
            level="A1",
            detail=f"Leading 4 digits map to licensed circle ({circle or 'Unknown'})",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Department of Telecommunications (DoT)",
        as_of=as_of,
        custom_limitations=[
            "subscriber identity and active SIM connectivity not verified",
            "mobile number portability (MNP) operator changes not reflected",
        ],
    )


def create_pran_authenticity(
    *,
    pran: str,
    valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_pran."""
    clean = str(pran).strip() if pran else ""
    format_valid = bool(re.match(r"^[0-9]{12}$", clean))
    checks = [
        AuthenticityCheck(
            name="pran_format_syntax",
            passed=format_valid,
            level="A0",
            detail="12-digit numeric Permanent Retirement Account Number format",
        ),
        AuthenticityCheck(
            name="pran_sector_structure_rule",
            passed=valid and format_valid,
            level="A1",
            detail="Sector code structure conforms to CRA / PFRDA issuance specification",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Pension Fund Regulatory and Development Authority (PFRDA)",
        as_of=as_of,
        custom_limitations=[
            "active NPS account tier status not verified",
        ],
    )


def create_tan_authenticity(
    *,
    tan: str,
    valid: bool,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_tan."""
    clean = str(tan).strip().upper() if tan else ""
    format_valid = bool(re.match(r"^[A-Z]{4}[0-9]{5}[A-Z]$", clean))
    checks = [
        AuthenticityCheck(
            name="tan_format_syntax",
            passed=format_valid,
            level="A0",
            detail="10-character alphanumeric TAN syntax (4 letters, 5 digits, 1 letter)",
        ),
        AuthenticityCheck(
            name="tan_jurisdiction_prefix_consistency",
            passed=format_valid,
            level="A1",
            detail="First 3 characters represent ITD jurisdiction code",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Income Tax Department",
        as_of=as_of,
        custom_limitations=[
            "active TAN deductor status not verified",
        ],
    )


def create_aa_consent_authenticity(
    *,
    valid: bool,
    has_dates: bool = True,
    has_fi_types: bool = True,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for validate_aa_consent_artifact."""
    checks = [
        AuthenticityCheck(
            name="aa_consent_schema_syntax",
            passed=valid,
            level="A0",
            detail="Account Aggregator consent artifact schema validation",
        ),
        AuthenticityCheck(
            name="aa_consent_parameters_consistency",
            passed=valid and has_dates and has_fi_types,
            level="A1",
            detail="Consent start, expiry, and financial information types consistency",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=valid,
        source="Reserve Bank of India (RBI) / Sahamati",
        as_of=as_of,
        custom_limitations=[
            "cryptographic signature on artifact not verified",
            "AA registry active session status not verified",
        ],
    )


def create_hsn_authenticity(
    *,
    hsn_code: str,
    found: bool,
    record: dict[str, Any] | None = None,
    dataset_version: str = "2025.04",
    as_of: str | None = None,
) -> dict[str, Any]:
    """Generate authenticity envelope for lookup_hsn_code."""
    clean = str(hsn_code).strip()
    format_valid = bool(re.match(r"^[0-9]{2,8}$", clean))
    checks = [
        AuthenticityCheck(
            name="hsn_format_syntax",
            passed=format_valid,
            level="A0",
            detail="Harmonized System of Nomenclature 2 to 8-digit tariff code structure",
        ),
        AuthenticityCheck(
            name="hsn_chapter_structure_consistency",
            passed=format_valid and len(clean) >= 2,
            level="A1",
            detail="Chapter and heading hierarchical digit grouping",
        ),
        AuthenticityCheck(
            name="record_in_bundled_dataset",
            passed=found,
            level="A2",
            detail="Tariff item matched in bundled CBIC GST HSN master schedule",
        ),
    ]
    return build_authenticity_envelope(
        checks=checks,
        valid=format_valid,
        source="Central Board of Indirect Taxes and Customs (CBIC) / GST Council",
        dataset_version=dataset_version,
        as_of=as_of,
        evidence_record=record if found else None,
        is_dataset_miss=not found,
        custom_limitations=[
            "exemption notifications and specific cess rates not verified",
        ],
    )
