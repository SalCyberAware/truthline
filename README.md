# Truthline

**Open-source verification of AI-generated and fabricated media, with reporting for schools, nonprofits and the public.**

Truthline lets a school front office, a nonprofit bookkeeper, a small business or a parent submit a suspicious image, screenshot, audio clip or document and get back, in plain language, what the evidence says: likely authentic, likely altered, likely AI-generated, or inconclusive. It then assembles the report the right authority expects (FBI, IC3, NCMEC CyberTipline, school tip lines, FTC) and the evidence-preservation request a police officer can send to a platform.

> **Status: v0.0.3 skeleton.** The pipeline runs, the contract is stable, and three analyzers exist (file metadata, C2PA Content Credentials, and first-pass chat-screenshot checks that are weak evidence only), and it can draft reports for six agencies. Nothing here is ready to make decisions with. See [Roadmap](#roadmap).

## The rules this project is built on

1. The tool informs human decisions; it never makes them.
2. Grades carry evidence. There is no bare "fake" stamp, and "inconclusive" is a normal answer.
3. Suspected child sexual abuse material is never stored, viewed or transmitted. It is hashed and reported. See [SECURITY.md](SECURITY.md).
4. No training on user submissions without explicit donation to the public benchmark.
5. Nothing is paywalled. Self-hosted equals hosted.

## Quick start (developers)

```bash
git clone https://github.com/SalCyberAware/truthline
cd truthline
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
truthline check path/to/screenshot.png
truthline check path/to/screenshot.png --json > case.json
pytest
```

Optional: `pip install c2pa-python` enables Content Credentials (C2PA) reading.

## How it works

```
file -> [safety gate] -> analyzers (run in parallel, each returns named Signals)
     -> assessment (public rules -> Grade + next steps) -> report (JSON + Markdown case file)
```

- **Analyzers** are small, independent modules that implement one contract: file in, list of `Signal` out. See [docs/analyzer-contract.md](docs/analyzer-contract.md). Anyone can add one without touching the core.
- **Assessment** is a readable rule set in `src/truthline/assessment.py`. No black-box final score.
- **Reports** are case files with the file's SHA-256, every signal, its strength, and what to do next.

## Roadmap

| Phase | What lands | Status |
| --- | --- | --- |
| 0.0.1 | Contract, pipeline, metadata + C2PA analyzers, CLI, benchmark harness | done |
| 0.0.2 | First-pass screenshot checks (dimensions, status bar, bubble alignment); stricter rules R5 and R9 | done |
| 0.0.3 | Agency report drafts: FBI, IC3, NCMEC, school tip line, FTC, police preservation letter (`truthline draft`) | here |
| 0.1 | Chat-screenshot forensics (UI templates, font metrics, clock checks), image forensics (ELA, double-JPEG), small open-model ensemble, report drafts for FBI/IC3/NCMEC/Safe2Tell/FTC | next |
| 0.2 | Audio analyzer, web interface, self-host package | |
| 0.3 | Benchmark results published, pilot with schools | |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The easiest first contribution is an analyzer or a consented benchmark sample.

## License

Core service: [AGPL-3.0](LICENSE). The analyzer SDK and report templates under `src/truthline/contract.py` and `src/truthline/reports/templates/` are additionally offered under Apache-2.0 (see [LICENSE-APACHE](LICENSE-APACHE)) so that schools and vendors can embed them freely.
