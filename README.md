# mcp-india-stack

MCP server exposing Indian financial and government APIs - GSTIN, IFSC, PAN, UPI, pincode, HSN/SAC - for AI agents. Zero auth. Offline-first.

## Status

[![CI](https://github.com/mcp-india-stack/mcp-india-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/mcp-india-stack/mcp-india-stack/actions/workflows/ci.yml)

## Install

```bash
pip install mcp-india-stack
```

## Run

```bash
mcp-india-stack
```

or

```bash
python -m mcp_india_stack
```

## Tools

- `lookup_ifsc`
- `validate_gstin`
- `validate_pan`
- `validate_upi_vpa`
- `lookup_pincode`
- `lookup_hsn_code`
- `decode_state_code`

## Bundled Data Size

This package bundles static datasets for offline-first workflows.

- IFSC dataset (Razorpay releases)
- India pincode dataset (GeoNames IN postal dump, CC-BY)
- HSN/SAC master (GST tutorial workbook transformed to CSV)
- State codes and curated UPI handles

Expected install footprint includes approximately 10-11MB compressed static data.

## Limitations

- GSTIN validation checks format and checksum, not active GSTN status.
- PAN validation is structural; PAN check character is not publicly algorithmic.
- HSN/SAC rates are static references and may vary by conditions/notifications.

## Legal and Attribution

See `NOTICES` for dataset attribution and licensing details.

