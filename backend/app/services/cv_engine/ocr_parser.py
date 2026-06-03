"""OCR document parser for extracting text from receipts and reports."""

from typing import Any

# TODO: Uncomment when OCR engines are installed
# import pytesseract
# from PIL import Image
# import easyocr


class OCRParser:
    """
    OCR engine for extracting text from document images.

    Supports Tesseract and EasyOCR backends for Indonesian text.
    """

    def __init__(self, backend: str = "tesseract"):
        """
        Args:
            backend: "tesseract" or "easyocr"
        """
        self.backend = backend
        self._reader = None

    def _get_easyocr_reader(self):
        """Lazy-load EasyOCR reader."""
        if self._reader is None:
            pass
            # TODO: self._reader = easyocr.Reader(["id", "en"])
        return self._reader

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image.

        Args:
            image_path: Path to the document/receipt image

        Returns:
            Extracted text string
        """
        if self.backend == "tesseract":
            return self._extract_tesseract(image_path)
        elif self.backend == "easyocr":
            return self._extract_easyocr(image_path)
        else:
            raise ValueError(f"Unknown OCR backend: {self.backend}")

    def _extract_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR."""
        # TODO: Implement
        # img = Image.open(image_path)
        # text = pytesseract.image_to_string(img, lang="ind+eng")
        # return text.strip()
        return ""  # Placeholder

    def _extract_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR."""
        # TODO: Implement
        # reader = self._get_easyocr_reader()
        # results = reader.readtext(image_path)
        # return " ".join([text for _, text, _ in results])
        return ""  # Placeholder

    def extract_structured(self, image_path: str) -> dict[str, Any]:
        """
        Extract structured data from a receipt/invoice image.

        Returns:
            {"raw_text": str, "items": [...], "total": float | None}
        """
        raw_text = self.extract_text(image_path)

        # TODO: Parse structured fields from raw OCR text
        return {
            "raw_text": raw_text,
            "items": [],
            "total": None,
        }


# ── Singleton ──
ocr_parser = OCRParser()
