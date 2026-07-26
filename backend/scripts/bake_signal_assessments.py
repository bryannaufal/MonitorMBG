#!/usr/bin/env python3
"""One-off: print rules-based seed signal assessments + optional Kimi GIZI for photos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import seed_data as sd
from app.services.scoring.nutrition_scorer import score_nutrition_rules, score_nutrition_with_kimi
from app.services.scoring.risk_scorer import (
    _assemble_result,
    _bonus,
    _label,
    _score_signal_rules,
    _score_trust,
)


def main() -> None:
    out: dict[int, dict] = {}
    for sig in sd.SIGNALS:
        sid = int(sig["id"])
        trust, trust_reasons = _score_trust(sig)
        bonus, bonus_reasons = _bonus(sig)
        severity, sev_reasons, actionability, act_reasons = _score_signal_rules(sig)

        nutrition_score = None
        nutrition_reasons: list[str] = []
        nutrition_engine = "none"
        if sig.get("attachment_path"):
            kimi = score_nutrition_with_kimi(sig)
            if kimi:
                nutrition_score = kimi["nutrition_score"]
                nutrition_reasons = kimi["nutrition_reasons"]
                nutrition_engine = "seed_vision"
            else:
                nutrition_score, nutrition_reasons = score_nutrition_rules(sig)
                nutrition_engine = "seed_rules"

        result = _assemble_result(
            sig,
            severity=severity,
            sev_reasons=sev_reasons,
            trust=trust,
            trust_reasons=trust_reasons,
            actionability=actionability,
            act_reasons=act_reasons,
            bonus=bonus,
            bonus_reasons=bonus_reasons,
            scoring_engine="seed",
            nutrition_score=nutrition_score,
            nutrition_reasons=nutrition_reasons,
            nutrition_engine=nutrition_engine if nutrition_engine != "none" else "none",
        )
        out[sid] = result
        print(
            f"#{sid}: final={result['final_priority_score']} "
            f"sev={severity} trust={trust} act={actionability} gizi={nutrition_score}"
        )

    path = Path(__file__).resolve().parents[1] / "app" / "data" / "signal_assessment_seed.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    # Apply manual photo GIZI overrides into JSON snapshot.
    from app.services.scoring.seed_signal_assessment import _PHOTO_NUTRITION_OVERRIDES

    for sid, photo in _PHOTO_NUTRITION_OVERRIDES.items():
        if sid not in out:
            continue
        out[sid]["nutrition_score"] = photo["nutrition_score"]
        reasons = [r for r in out[sid].get("reasons") or [] if not r.startswith("Gizi:")]
        reasons.append(
            f"Gizi: {photo['nutrition_score']}/100 (estimasi seed dari bukti foto) — "
            f"{'; '.join(photo['nutrition_reasons'][:2])}"
        )
        out[sid]["reasons"] = reasons
        expl = out[sid].get("explanation") or ""
        if "Gizi" not in expl:
            out[sid]["explanation"] = expl + " Gizi diestimasi dari bukti foto (data seed). "

    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {path}")

    ts_path = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "signalAssessmentSeed.ts"
    lines = [
        '/** Auto-generated — jangan edit manual. Jalankan scripts/bake_signal_assessments.py */',
        'import type { Assessment } from "./reviewStore";',
        "",
        "export const SIGNAL_ASSESSMENT_SEED: Record<number, Assessment> = {",
    ]
    for sid, item in sorted(out.items(), key=lambda x: x[0]):
        lines.append(f"  {sid}: {json.dumps(item, ensure_ascii=False)},")
    lines.append("};")
    lines.append("")
    ts_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {ts_path}")


if __name__ == "__main__":
    main()
