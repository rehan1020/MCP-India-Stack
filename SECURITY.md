# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please send an email to the maintainers. We appreciate responsible disclosure and will work to address issues promptly.

## Supported Versions

We release patches for security vulnerabilities. Which versions are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Security Best Practices

- This package validates Indian identity numbers (GSTIN, PAN, etc.) structurally but does not verify active status with issuing authorities
- Tax calculators are estimates for FY2025-26 — consult a qualified professional for actual tax filings
- This package makes HTTP requests to external CDNs for dataset updates; ensure network access is properly secured in production environments