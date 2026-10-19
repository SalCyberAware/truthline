# Contributing to Truthline

Thank you. This project exists so that people without forensic budgets can get honest answers. Contributions that help most, in order:

1. **Benchmark samples.** Real and fabricated screenshots, voice notes or images you have the right to share. Fabricated samples should be made with public generator sites or ordinary editing, never with anyone's real private messages. See `benchmark/README.md` for the consent form and folder layout. Never submit anything involving a minor in a sexual context; see SECURITY.md.
2. **Analyzers.** A new signal source in `src/truthline/analyzers/`. Read `docs/analyzer-contract.md`; an analyzer is one class with one method. Include a test and a one-paragraph note on how reliable the signal is on its own.
3. **Report templates.** If you know what a specific agency or platform wants in a report, improve the template in `src/truthline/reports/templates/`.
4. **Language.** Plain-language review of every string a user sees. If a sentence would confuse a school secretary, it is a bug.

## Ground rules

- Signals, not verdicts. An analyzer reports what it found and how strong that is. It never returns "fake".
- Every accuracy claim must be reproducible from the benchmark.
- Be kind. We work on upsetting material; take care of each other.

## Workflow

- Fork, branch, `pip install -e ".[dev]"`, `pytest`, open a pull request.
- Small pull requests merge faster.
- By contributing you agree your code is licensed under the project licenses (AGPL-3.0 for the core, Apache-2.0 for the SDK and templates).
