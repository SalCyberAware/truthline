# Report templates

The agency drafts live in `agencies.py` as plain data (sections of text with `{fields}` taken from the
case file and `[FILL IN: ...]` markers for what only a person knows). Render them with:

    truthline check suspicious.png --as "a screenshot of a text" --json --out case.json
    truthline agencies
    truthline draft case.json --to ic3 --name "Pat Lee" --org "Lincoln Middle School" --out ic3-draft.md

| id | Destination | Notes |
| --- | --- | --- |
| `fbi` | tips.fbi.gov / field office | Threats and serious federal crimes |
| `ic3` | ic3.gov | Fraud, extortion, impersonation |
| `ncmec` | report.cybertip.org | Any case involving a minor; the file is never attached, hash only |
| `school` | State or district tip line (FortifyFL, Safe2Tell, Say Something) | School threats |
| `ftc` | reportfraud.ftc.gov | Scams, fake reviews, impersonation |
| `preservation` | Platform legal contact, sent by police | 18 U.S.C. 2703(f); only a governmental entity may send it |

Rules: Truthline writes drafts, a person sends them. If a case may involve sexual content about a minor,
the submitter's description is withheld from every draft. Drafts never say a crime occurred.

These templates are offered under Apache-2.0 so agencies and vendors can reuse them.
Corrections from agency staff and school safety officers are the most valuable contribution you can make.
