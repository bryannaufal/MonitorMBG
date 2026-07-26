#!/usr/bin/env python3
"""Build copilot_rag_fixture.json from seed cases (Gemini or local fallback)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import seed_data as sd
from app.config import settings
from app.services.copilot.embedder import active_embedding_model, embed_batch
from app.services.copilot.indexer import build_case_document, document_metadata

OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "copilot_rag_fixture.json"


def main() -> None:
    engine = active_embedding_model()
    print(f"Building fixture with engine={engine}")

    docs: list[dict] = []
    texts: list[str] = []
    metas: list[dict] = []
    ids: list[str] = []
    for case in sd.CASES:
        cid = case["case_id"]
        text = build_case_document(cid)
        if not text:
            continue
        ids.append(f"case:{cid}")
        texts.append(text)
        metas.append(document_metadata(cid))

    vectors, model = embed_batch(texts)
    for i, doc_id in enumerate(ids):
        docs.append(
            {
                "id": doc_id,
                "text": texts[i],
                "embedding": vectors[i],
                "metadata": metas[i],
            }
        )

    payload = {
        "version": 1,
        "embedding_model": model,
        "embedding_dim": len(vectors[0]) if vectors else settings.GEMINI_EMBEDDING_DIM,
        "documents": docs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(docs)} documents → {OUT}")


if __name__ == "__main__":
    main()
