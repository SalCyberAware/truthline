"""C2PA / Content Credentials analyzer.

Reliability note: a VALID manifest is the strongest signal this project has.
If it names an AI generator (OpenAI, Adobe Firefly, Google, Anthropic, ...) the
file is AI-generated or AI-edited; if it names a camera and the chain is
intact, the file is what it claims to be. An ABSENT manifest is NEUTRAL: fewer
than 1% of images online carry credentials and platforms strip them.
A BROKEN manifest (signature does not validate) is MODERATE evidence of
tampering after signing.

Requires the optional dependency `c2pa-python`. Without it, the analyzer
reports itself unavailable rather than guessing.
"""

from __future__ import annotations

import json
import time

from ..contract import (
    AnalyzerResult,
    Direction,
    MediaType,
    Signal,
    Strength,
    Submission,
)

AI_GENERATOR_HINTS = (
    "openai", "dall-e", "dall·e", "chatgpt", "sora", "firefly", "adobe firefly", "gemini",
    "imagen", "veo", "anthropic", "claude", "midjourney", "stability", "stable diffusion",
    "microsoft designer", "bing image creator", "copilot", "ideogram", "runway", "pika",
)


class C2PAAnalyzer:
    name = "c2pa"
    media_types = frozenset({MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO, MediaType.DOCUMENT})

    def analyze(self, submission: Submission) -> AnalyzerResult:
        t0 = time.perf_counter()
        try:
            import c2pa  # type: ignore
        except ImportError:
            return AnalyzerResult(
                self.name, available=False,
                note="c2pa-python not installed; run `pip install c2pa-python` to enable Content Credentials checks.",
            )

        try:
            reader = c2pa.Reader(str(submission.path))
            manifest_json = reader.json()
        except Exception as exc:
            msg = str(exc).lower()
            if "no manifest" in msg or "jumbf not found" in msg or "manifest not found" in msg:
                return AnalyzerResult(
                    self.name, available=True,
                    signals=[Signal(
                        analyzer=self.name, key="c2pa.absent",
                        direction=Direction.NEUTRAL, strength=Strength.WEAK,
                        summary="No Content Credentials (C2PA) are attached to this file.",
                        why_it_matters="This proves nothing either way. Most real files have none, and platforms strip them. A present, valid credential would be strong evidence; its absence is not.",
                        details={},
                    )],
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                )
            return AnalyzerResult(self.name, available=False, note=f"could not read manifest: {exc}")

        try:
            store = json.loads(manifest_json)
        except json.JSONDecodeError:
            return AnalyzerResult(self.name, available=False, note="manifest JSON unreadable")

        active = store.get("active_manifest")
        manifests = store.get("manifests", {})
        manifest = manifests.get(active, {}) if active else {}
        validation = store.get("validation_status") or []
        errors = [v for v in validation if str(v.get("code", "")).startswith(("signingCredential.", "claimSignature.", "assertion.")) and "failure" in json.dumps(v).lower()]

        generator = (manifest.get("claim_generator") or manifest.get("claim_generator_info", [{}])[0].get("name", "")) if manifest else ""
        gen_lower = str(generator).lower()
        actions = []
        for a in manifest.get("assertions", []):
            if a.get("label", "").startswith("c2pa.actions"):
                for act in a.get("data", {}).get("actions", []):
                    actions.append({k: act.get(k) for k in ("action", "softwareAgent", "digitalSourceType") if k in act})
        source_types = " ".join(str(a.get("digitalSourceType", "")) for a in actions).lower()

        signals: list[Signal] = []
        details = {"claim_generator": generator, "actions": actions, "validation_status": validation}

        if errors:
            signals.append(Signal(
                analyzer=self.name, key="c2pa.invalid",
                direction=Direction.FABRICATED, strength=Strength.MODERATE,
                summary="Content Credentials are present but do not validate.",
                why_it_matters="The file was changed after it was signed, or the credential was copied from another file. Either way the credential cannot be trusted and the change should be explained.",
                details=details,
            ))
            return AnalyzerResult(self.name, True, signals, duration_ms=int((time.perf_counter() - t0) * 1000))

        is_ai = any(h in gen_lower for h in AI_GENERATOR_HINTS) or "trainedalgorithmicmedia" in source_types
        if is_ai:
            signals.append(Signal(
                analyzer=self.name, key="c2pa.ai_generated",
                direction=Direction.AI_GENERATED, strength=Strength.STRONG,
                summary=f"Valid Content Credentials say this file was created or edited with an AI tool ({generator}).",
                why_it_matters="This is a signed statement from the tool that made the file. It is the strongest evidence available that the content is synthetic or AI-edited.",
                details=details,
            ))
        else:
            signals.append(Signal(
                analyzer=self.name, key="c2pa.valid",
                direction=Direction.AUTHENTIC, strength=Strength.STRONG,
                summary=f"Valid Content Credentials are attached ({generator or 'signer named in manifest'}).",
                why_it_matters="A valid, unbroken credential chain means the file has not been altered since it was signed by the named device or software.",
                details=details,
            ))

        return AnalyzerResult(self.name, True, signals, duration_ms=int((time.perf_counter() - t0) * 1000))
