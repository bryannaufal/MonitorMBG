"""Live Kimi connectivity check (run from backend/)."""

import httpx

from app.config import settings
from app.services.intake.normalizer import from_public_form
from app.services.scoring.kimi_signal_scorer import score_signal_with_kimi
from app.services.scoring.risk_scorer import score_signal


def main() -> None:
    key = (settings.KIMI_API_KEY or "").strip()
    print("KIMI_API_KEY loaded:", bool(key))
    print("KIMI_MODEL config:", settings.KIMI_MODEL)
    print("KIMI_BASE_URL:", settings.KIMI_BASE_URL)

    if not key:
        print("FAIL: no API key in .env")
        return

    body = {
        "model": settings.KIMI_MODEL,
        "messages": [{"role": "user", "content": "Balas satu kata: ok"}],
    }
    url = f"{settings.KIMI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=settings.KIMI_TIMEOUT_SECONDS) as client:
        resp = client.post(url, headers=headers, json=body)
        print(f"probe {settings.KIMI_MODEL}: HTTP {resp.status_code}")
        if resp.status_code != 200:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
            print(f"  -> {err[:180]}")
            return
        print("  -> model works for simple prompt")

    signal = from_public_form({
        "description": "Ada belatung di nasi MBG SDN Melati 03 Tangerang, murid muntah.",
        "region": "Banten",
        "district": "Kota Tangerang",
        "school": "SDN Melati 03",
        "issue_category": "dugaan keamanan pangan",
    })

    kimi = score_signal_with_kimi(signal)
    result = score_signal(signal)
    if kimi:
        print("SCORER_OK engine=kimi")
        print("  severity:", kimi["severity_score"])
        print("  actionability:", kimi["actionability_score"])
    else:
        print("SCORER_FAIL fallback=rules")
    print("  final engine:", result.get("scoring_engine"))
    print("  final score:", result["final_priority_score"], result["priority_label"])


if __name__ == "__main__":
    main()
