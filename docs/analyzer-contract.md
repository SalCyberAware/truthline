# Writing an analyzer

An analyzer is one class with a name, the media types it handles, and one method. It receives a `Submission` and returns an `AnalyzerResult` containing zero or more `Signal`s. It never returns a verdict.

```python
from truthline.contract import Analyzer, AnalyzerResult, Direction, MediaType, Signal, Strength, Submission

class ExampleAnalyzer:
    name = "example"
    media_types = frozenset({MediaType.IMAGE})

    def analyze(self, submission: Submission) -> AnalyzerResult:
        # look at submission.path; never modify it
        return AnalyzerResult(self.name, available=True, signals=[
            Signal(
                analyzer=self.name,
                key="example.finding",          # stable, machine-readable
                direction=Direction.FABRICATED,  # authentic | fabricated | ai_generated | neutral
                strength=Strength.MODERATE,      # strong | moderate | weak
                summary="One sentence saying what was found.",
                why_it_matters="One sentence saying what that means for a non-expert.",
                details={"raw": "evidence for the case file"},
            )
        ])
```

Register it in `src/truthline/analyzers/__init__.py` by adding an instance to `REGISTRY`.

## Rules

1. **Say what you found, not what it means for the case.** The assessment engine decides grades using public rules.
2. **Pick strength honestly.** `STRONG` means this one signal would justify a grade change on its own (a valid provenance manifest; a status bar matching no shipped OS). `MODERATE` means it needs company. `WEAK` is context only and never changes a grade.
3. **Absence is usually NEUTRAL.** Missing metadata, missing watermark, missing credential: real files lack them too.
4. **If you cannot run, say so.** Return `available=False` with a note. Never return an empty success.
5. **Write for a school secretary.** Every `summary` and `why_it_matters` is shown verbatim.
6. **Never modify or re-save the submission.** Work on bytes in memory or on a copy.
7. **Include a reliability note** at the top of your module: what fools this signal, and how often.
8. **Ship a test** in `tests/` and, if possible, a consented benchmark sample that exercises it.
