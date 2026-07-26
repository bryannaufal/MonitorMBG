"""Simpan lampiran foto upload formulir publik (runtime, bukan dataset demo)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

INTAKE_MEDIA_BASE = "/intake-media"
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "public_intake"
MAX_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


async def save_public_intake_photo(file: UploadFile) -> tuple[str, str]:
    """Simpan foto upload; return (attachment_path, attachment_title)."""
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format foto tidak didukung. Gunakan JPG, PNG, WEBP, atau GIF.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File foto kosong.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Ukuran foto maksimal 5 MB.")

    ext = ALLOWED_CONTENT_TYPES[content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = ensure_upload_dir() / filename
    dest.write_bytes(data)

    original = (file.filename or "foto-laporan").strip()
    title = original if original else "Foto laporan publik"
    return f"{INTAKE_MEDIA_BASE}/{filename}", title[:120]
