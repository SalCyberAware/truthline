# Truthline benchmark

The benchmark is how this project keeps itself honest. Every release re-runs it and publishes the numbers, including the bad ones.

## Folder layout

```
benchmark/
  samples/
    real/           files that are what they claim to be (consented)
    fabricated/     edited or generator-made files (no AI involved)
    ai_generated/   files produced by an AI tool
  manifest.csv      one row per sample: path, category, claimed_type, source, consent_ref, notes
  run_benchmark.py  runs the pipeline over the manifest and prints per-category results
```

Sample files are **not committed** to the repository. They are shared with contributors under the consent terms below, and only their hashes and the results are published.

## What goes in

- **real/**: screenshots, photos, voice notes or documents you created yourself or have written permission to share. Nothing involving private conversations of other people without their consent.
- **fabricated/**: files made with public fake-text generators, image editors, or by editing a real sample of your own. Record the method in `notes`.
- **ai_generated/**: files produced by an AI tool. Record the tool and version in `source`.

## What never goes in

- Anything sexual involving a minor, in any form. See SECURITY.md.
- Real threats, real victims' material, or anything taken from a live case without written authorization.
- Content you do not have the right to share.

## Consent

Each sample needs a `consent_ref` pointing to a signed consent record (template: `consent-form.md`). Samples without one are rejected.

## Running

```bash
truthline analyzers
python benchmark/run_benchmark.py benchmark/manifest.csv
```

Output: per-category grade distribution and the two numbers that matter most:
- **Wrongful fabricated rate**: real samples graded Likely/Very likely fabricated. Target: 0.
- **Catch rate**: fabricated or AI samples graded Likely/Very likely fabricated. Reported honestly, however low.
