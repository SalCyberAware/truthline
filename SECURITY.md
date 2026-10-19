# Security and safeguarding policy

## Reporting a vulnerability

Email the maintainers (address to be published with the first release) with a description and steps to reproduce. Do not open a public issue for security problems. We aim to acknowledge within 72 hours.

## Child sexual abuse material (CSAM)

Truthline will never store, display, transmit or let staff view suspected CSAM.

- The hosted service (when it exists) will hash on the submitter's device and compare hashes against authorized lists; the file itself does not leave the device.
- Any suspected CSAM encountered by the project is reported to the NCMEC CyberTipline (https://report.cybertip.org) and, where required, to law enforcement.
- Contributors must never add such material to the benchmark or to issues, and must never attempt to "test" the pipeline with it.
- This protocol will be reviewed by counsel before any public upload endpoint is enabled. Until then, the public repository ships code only; there is no hosted upload service.

## Data handling (planned for the hosted service)

- Submissions are deleted after a user-chosen retention window (default 30 days for organizations; immediately for the anonymous public tier). Only hashes and the report are kept.
- No submission is used for model training unless explicitly donated to the public benchmark.
- Every disclosure made from a school account is logged, to support FERPA record-keeping.
