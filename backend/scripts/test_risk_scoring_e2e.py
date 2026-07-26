"""End-to-end risk scoring test (rules + kimi path)."""

import httpx

from app.config import settings
from app.runtime_store import append_signal
from app.services.intake.normalizer import from_public_form, from_social_raw
from app.services.scoring.risk_scorer import score_signal


def _print_result(label: str, result: dict) -> None:
    print(f"\n=== {label} ===")
    print("scoring_engine:", result.get("scoring_engine"))
    print("severity:", result["severity_score"])
    print("confidence (trust):", result["confidence_score"])
    print("actionability:", result["actionability_score"])
    print("final:", result["final_priority_score"], result["priority_label"])
    for reason in result.get("reasons", [])[:3]:
        print(" -", reason)


def main() -> None:
    print("KIMI_MODEL:", settings.KIMI_MODEL)
    print("KIMI_KEY set:", bool((settings.KIMI_API_KEY or "").strip()))

    form_signal = from_public_form({
        "description": (
            "Ada belatung di nasi MBG SDN Melati 03 Tangerang. "
            "Beberapa murid muntah setelah makan siang."
        ),
        "region": "Banten",
        "district": "Kota Tangerang",
        "school": "SDN Melati 03",
        "issue_category": "dugaan keamanan pangan",
    })
    _print_result("Formulir publik (lokasi lengkap)", score_signal(form_signal))

    social_signal = from_social_raw({
        "text": "katanya mbg enak tapi ada yang bilang nasinya aneh",
        "summary": "mbg enak nasi aneh",
        "region": "Belum teridentifikasi",
    }, intake_origin="scraper_live")
    _print_result("Media sosial (lokasi minim)", score_signal(social_signal))

    runtime_signal = append_signal(from_social_raw({
        "text": "MBG SDN Melati Tangerang diduga belatung, murid muntah",
        "summary": "MBG Tangerang belatung",
        "region": "Banten",
        "district": "Kota Tangerang",
        "issue_category": "dugaan keamanan pangan",
    }, intake_origin="scraper_live"))

    result = score_signal(runtime_signal)
    _print_result(f"Runtime signal #{runtime_signal['id']}", result)

    try:
        resp = httpx.get(
            f"http://localhost:8000/api/v1/signals/{runtime_signal['id']}/assessment",
            timeout=20,
        )
        print("\n=== API GET /signals/{id}/assessment ===")
        print("HTTP", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            print("scoring_engine:", data.get("scoring_engine", "n/a"))
            print("final:", data.get("final_priority_score"), data.get("priority_label"))
        else:
            print(resp.text[:300])
    except httpx.ConnectError:
        print("\n=== API skip (backend tidak jalan di :8000) ===")


if __name__ == "__main__":
    main()
