"""BBPS Biller Directory - bundled offline lookup."""

from __future__ import annotations

from typing import Any

_BILLERS: dict[str, list[dict[str, Any]]] = {
    "electricity": [
        {
            "biller_id": "ELEC_MH_MSEDC",
            "biller_name": "Maharashtra State Electricity Distribution Co.",
            "state": "Maharashtra",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "ELEC_DL_BSES",
            "biller_name": "BSES Rajdhani Power",
            "state": "Delhi",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "ELEC_DL_TPDDL",
            "biller_name": "Tata Power Delhi",
            "state": "Delhi",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "ELEC_KA_BESCOM",
            "biller_name": "BESCOM - Bangalore Electricity",
            "state": "Karnataka",
            "category": "electricity",
            "parameters": ["consumer_id"],
        },
        {
            "biller_id": "ELEC_TN_TANGEDCO",
            "biller_name": "Tamil Nadu Generation and Distribution Corp",
            "state": "Tamil Nadu",
            "category": "electricity",
            "parameters": ["service_number"],
        },
        {
            "biller_id": "ELEC_WB_WBSEDCL",
            "biller_name": "West Bengal State Electricity Distribution",
            "state": "West Bengal",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "ELEC_GJ_GUVNL",
            "biller_name": "Gujarat Urja Vikas Nigam",
            "state": "Gujarat",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "ELEC_RJ_JVVNL",
            "biller_name": "Jaipur Vidyut Vitran Nigam",
            "state": "Rajasthan",
            "category": "electricity",
            "parameters": ["account_number"],
        },
        {
            "biller_id": "ELEC_UP_PVVNL",
            "biller_name": "Purvanchal Vidyut Vitran Nigam",
            "state": "Uttar Pradesh",
            "category": "electricity",
            "parameters": ["consumer_id"],
        },
        {
            "biller_id": "ELEC_MP_MPMKVV",
            "biller_name": "Madhya Pradesh Madhya Kshetra Vidyut",
            "state": "Madhya Pradesh",
            "category": "electricity",
            "parameters": ["consumer_number"],
        },
    ],
    "gas": [
        {
            "biller_id": "GAS_MH_MGL",
            "biller_name": "Mahanagar Gas Limited",
            "state": "Maharashtra",
            "category": "gas",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "GAS_DL_IGL",
            "biller_name": "Indraprastha Gas Limited",
            "state": "Delhi",
            "category": "gas",
            "parameters": ["customer_id"],
        },
        {
            "biller_id": "GAS_GJ_GSPC",
            "biller_name": "Gujarat State Petronet",
            "state": "Gujarat",
            "category": "gas",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "GAS_KA_GAIL",
            "biller_name": "GAIL Gas",
            "state": "Karnataka",
            "category": "gas",
            "parameters": ["consumer_id"],
        },
        {
            "biller_id": "GAS_UP_GAIL",
            "biller_name": "GAIL Gas Uttar Pradesh",
            "state": "Uttar Pradesh",
            "category": "gas",
            "parameters": ["customer_id"],
        },
    ],
    "dth": [
        {
            "biller_id": "DTH_DISH",
            "biller_name": "Dish TV",
            "state": "all",
            "category": "dth",
            "parameters": ["smart_card_number", "registered_mobile"],
        },
        {
            "biller_id": "DTH_TATA",
            "biller_name": "Tata Play",
            "state": "all",
            "category": "dth",
            "parameters": ["subscriber_id"],
        },
        {
            "biller_id": "DTH_SUN",
            "biller_name": "Sun Direct",
            "state": "all",
            "category": "dth",
            "parameters": ["smart_card_number"],
        },
        {
            "biller_id": "DTH_AIRTEL",
            "biller_name": "Airtel Digital TV",
            "state": "all",
            "category": "dth",
            "parameters": ["dth_number"],
        },
    ],
    "water": [
        {
            "biller_id": "WATER_MH_MCGM",
            "biller_name": "Brihanmumbai Municipal Corporation Water",
            "state": "Maharashtra",
            "category": "water",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "WATER_DL_DJB",
            "biller_name": "Delhi Jal Board",
            "state": "Delhi",
            "category": "water",
            "parameters": ["property_id", "k_number"],
        },
        {
            "biller_id": "WATER_KA_BWSSB",
            "biller_name": "Bangalore Water Supply and Sewerage",
            "state": "Karnataka",
            "category": "water",
            "parameters": ["consumer_number"],
        },
        {
            "biller_id": "WATER_CH_PUNWATER",
            "biller_name": "Pune Municipal Corporation Water",
            "state": "Maharashtra",
            "category": "water",
            "parameters": ["consumer_id"],
        },
    ],
    "broadband": [
        {
            "biller_id": "BB_AIRTEL",
            "biller_name": "Airtel Xstream Fiber",
            "state": "all",
            "category": "broadband",
            "parameters": ["account_number", "phone_number"],
        },
        {
            "biller_id": "BB_JIO",
            "biller_name": "JioFiber",
            "state": "all",
            "category": "broadband",
            "parameters": ["consumer_id"],
        },
        {
            "biller_id": "BB_ACT",
            "biller_name": "ACT Fibernet",
            "state": "all",
            "category": "broadband",
            "parameters": ["customer_id"],
        },
        {
            "biller_id": "BB_EXCITEL",
            "biller_name": "Excitel Broadband",
            "state": "all",
            "category": "broadband",
            "parameters": ["subscriber_id"],
        },
        {
            "biller_id": "BSNL_FTTH",
            "biller_name": "BSNL FTTH",
            "state": "all",
            "category": "broadband",
            "parameters": ["landline_number"],
        },
    ],
    "fastag": [
        {
            "biller_id": "FASTAG_ICICI",
            "biller_name": "ICICI Bank Fastag",
            "state": "all",
            "category": "fastag",
            "parameters": ["vehicle_number", "fastag_id"],
        },
        {
            "biller_id": "FASTAG_HDFC",
            "biller_name": "HDFC Bank Fastag",
            "state": "all",
            "category": "fastag",
            "parameters": ["vehicle_number", "fastag_id"],
        },
        {
            "biller_id": "FASTAG_KOTAK",
            "biller_name": "Kotak Mahindra Bank Fastag",
            "state": "all",
            "category": "fastag",
            "parameters": ["vehicle_number"],
        },
        {
            "biller_id": "FASTAG_AXIS",
            "biller_name": "Axis Bank Fastag",
            "state": "all",
            "category": "fastag",
            "parameters": ["vehicle_number"],
        },
        {
            "biller_id": "FASTAG_SBI",
            "biller_name": "State Bank of India Fastag",
            "state": "all",
            "category": "fastag",
            "parameters": ["vehicle_number"],
        },
    ],
    "insurance": [
        {
            "biller_id": "INS_LIC",
            "biller_name": "LIC of India",
            "state": "all",
            "category": "insurance",
            "parameters": ["policy_number", "premium_reference"],
        },
        {
            "biller_id": "INS_HDFC_LIFE",
            "biller_name": "HDFC Life Insurance",
            "state": "all",
            "category": "insurance",
            "parameters": ["policy_number"],
        },
        {
            "biller_id": "INS_SBI_LIFE",
            "biller_name": "SBI Life Insurance",
            "state": "all",
            "category": "insurance",
            "parameters": ["policy_number"],
        },
    ],
    "mobile": [
        {
            "biller_id": "MOB_JIO",
            "biller_name": "Jio Prepaid/Postpaid",
            "state": "all",
            "category": "mobile",
            "parameters": ["mobile_number"],
        },
        {
            "biller_id": "MOB_AIRTEL",
            "biller_name": "Airtel Prepaid/Postpaid",
            "state": "all",
            "category": "mobile",
            "parameters": ["mobile_number"],
        },
        {
            "biller_id": "MOB_VI",
            "biller_name": "Vi (Vodafone Idea)",
            "state": "all",
            "category": "mobile",
            "parameters": ["mobile_number"],
        },
        {
            "biller_id": "MOB_BSNL",
            "biller_name": "BSNL",
            "state": "all",
            "category": "mobile",
            "parameters": ["mobile_number"],
        },
    ],
}


def lookup_bbps_biller(
    category: str | None = None,
    state: str | None = None,
    biller_id: str | None = None,
) -> dict[str, Any]:
    """Look up BBPS biller details.

    Args:
        category: Category (electricity, gas, dth, water, broadband, fastag, insurance, mobile)
        state: State name (e.g., 'Maharashtra', 'Delhi', 'all')
        biller_id: Specific biller ID for direct lookup

    Returns:
        Dict with matching billers and their parameter schemas.
    """
    errors: list[str] = []
    warnings: list[str] = []

    valid_categories = list(_BILLERS.keys())
    if category and category.lower() not in valid_categories:
        errors.append(f"Invalid category. Valid: {valid_categories}")
        return {"found": False, "billers": [], "errors": errors, "warnings": warnings}

    results = []

    if biller_id:
        for cat_billers in _BILLERS.values():
            for biller in cat_billers:
                if biller["biller_id"].lower() == biller_id.lower():
                    results.append(biller)
        if not results:
            errors.append(f"Biller ID '{biller_id}' not found")

    elif category:
        cat_billers = _BILLERS.get(category.lower(), [])
        if state:
            state_lower = state.lower().strip()
            if state_lower == "all":
                results = cat_billers
            else:
                for biller in cat_billers:
                    if biller["state"].lower() == state_lower or biller["state"].lower() == "all":
                        results.append(biller)
        else:
            results = cat_billers

    else:
        for cat_billers in _BILLERS.values():
            results.extend(cat_billers)

    return {
        "found": len(results) > 0,
        "billers": results,
        "count": len(results),
        "categories": list(_BILLERS.keys()),
        "errors": errors,
        "warnings": warnings,
    }
