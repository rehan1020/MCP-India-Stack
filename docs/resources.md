# MCP Resources

The `mcp-india-stack` server exposes structured resources for server status, versioning, and tool schemas.

## Server Status

**URI:** `india://status`

Returns the current server configuration, versioning, and runtime status.

**Example Output:**
```json
{
  "version": "0.3.0",
  "db_connected": true,
  "live_lookup_enabled": false,
  "dry_run_mode": false,
  "db_url_configured": false,
  "tool_count": 30,
  "data_version": "2025.04"
}
```

---

## Changelog

**URI:** `india://changelog`

Returns a structured version of the project changelog.

---

## Tool Schemas

**URIs:** `india://schema/<tool_name>`

Returns the JSON schema for the output of a specific tool.

**Supported Tools:**
- `lookup_ifsc`
- `validate_gstin`
- `validate_pan`
- `validate_upi_vpa`
- `lookup_pincode`
- `lookup_hsn_code`
- `decode_state_code`
- `validate_aadhaar`
- `validate_voter_id`
- `validate_driving_license`
- `validate_passport`
- `validate_cin`
- `validate_din`
- `calculate_income_tax`
- `calculate_tds`
- `calculate_gst`
- `calculate_surcharge`
- `calculate_hra_exemption`
- `calculate_capital_gains`
- `calculate_advance_tax`
- `bulk_validate_gstin`
