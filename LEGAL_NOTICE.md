# Legal Notice & Disclaimer

_Last updated: 2026-08-22_

## No Government Affiliation

This project is an independent, community-maintained software package. It is **not** affiliated with, endorsed by, or officially connected to the National Informatics Centre (NIC), the e-Committee of the Supreme Court of India, the Ministry of Electronics & Information Technology (MeitY), the Department of Personnel & Training (RTI), or any State/Central Government of India department. "eCourts," "NJDG," and "RTI Online" refer to government services described for interoperability purposes only; no trademark or endorsement is claimed or implied.

## Not Legal Advice

Nothing produced by this software — including but not limited to bare-act section lookups, limitation-period calculations, court-fee estimates, stamp-duty estimates, or RTI deadline/penalty calculations — constitutes legal advice. Outputs are algorithmic estimates based on publicly available statutory text and may not reflect the current state of law, applicable amendments, judicial interpretation, or state-specific notifications. Consult a qualified advocate or the relevant government authority before relying on any output for a legal proceeding, filing, or decision.

## Data Accuracy

- Statutory references (IPC/BNS/CrPC/BNSS/Indian Evidence Act/BSA) are provided as paraphrased summaries, not verbatim reproductions of the enacted text, and may lag official amendments.
- State-subject data (court fees, stamp duty) is curated per state and carries an `as_of` / `last_verified` field; it is **not** live-verified against the issuing state authority at query time.
- Court/case data surfaced by any live-scraping or live-proxy module reflects the source portal or third-party provider at the time of the request and may be incomplete, delayed, or inaccurate. Cross-check against the official source before relying on it.

## Third-Party Data Sources

Modules that access live government portals (e.g. RTI Online, NJDG) or third-party commercial APIs (e.g. eCourtsIndia.com, Surepass, Vakeel360, ECIAPI) are subject to those services' own Terms of Service, robots.txt directives, rate limits, and pricing. Users are responsible for:

- Reviewing and complying with the target portal's or provider's Terms of Service before use.
- Any account, API key, or session credential used is the user's own; this project does not bundle, share, or have access to user credentials.
- Any cost, rate-limiting, or account action taken by a third-party provider as a result of usage.

This project does not warrant continued availability, legality, or ToS-compliance of any scraping-based module in any jurisdiction, and reserves the right to deprecate a module if a source portal's terms change.

## Session/Credential-Based Modules

Any module requiring a user-harvested session URL or API key (e.g. an RTI-tracking or eCourts-proxy module) treats that value as a bearer credential:

- It is stored locally on the user's machine only, never transmitted to this project's maintainers or any third party other than the intended target portal/provider.
- It typically cannot be scoped or rotated by this software — revocation depends on the issuing portal/provider.
- Users should treat leakage of this value as equivalent to credential/account compromise.

## No Warranty

This software is provided "as is," without warranty of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the authors or maintainers be liable for any claim, damages, or other liability arising from use of this software, including reliance on any legal, tax, or financial calculation it produces.

## Personal Data (Aadhaar, PAN, Voter ID, etc.)

Where this project or a related package validates or decodes identity document formats (Aadhaar, PAN, Voter ID, Driving Licence, Passport), it performs structural/checksum validation only and does not verify active registration status with the issuing authority. Outputs involving Aadhaar numbers are masked. Users are responsible for their own compliance with India's Digital Personal Data Protection Act, 2023 (DPDP Act) and any other applicable data-protection law when handling personal data through this software, including deciding what personal data to input in the first place.

## License Interaction

This notice supplements, and does not replace, the project's software license (see `LICENSE`). Where a conflict exists between this notice and the license regarding warranty or liability, the license terms govern for code-copyright purposes; this notice governs disclosure and data-source obligations specific to Indian government and legal data.

## Reporting Issues

Report data inaccuracies, ToS concerns, or security issues via this repository's `SECURITY.md` / issue tracker rather than relying on outputs for a live legal matter in the interim.
