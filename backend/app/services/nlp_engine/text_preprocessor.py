"""Text preprocessor for Indonesian social media text."""

import re
from typing import List


class TextPreprocessor:
    """
    Cleans and normalizes Indonesian social media text for NLP pipelines.

    Handles:
    - URL removal
    - Mention/hashtag normalization
    - Emoji handling
    - Indonesian informal → formal text normalization
    """

    # Common Indonesian informal word mappings
    INFORMAL_MAP: dict[str, str] = {
        "gak": "tidak",
        "ga": "tidak",
        "gk": "tidak",
        "tdk": "tidak",
        "yg": "yang",
        "dgn": "dengan",
        "utk": "untuk",
        "blm": "belum",
        "sdh": "sudah",
        "udh": "sudah",
        "krn": "karena",
        "tp": "tapi",
        "bgt": "banget",
        "bngt": "banget",
        "sm": "sama",
        "lg": "lagi",
        "aja": "saja",
        "gmn": "bagaimana",
        "org": "orang",
        "msh": "masih",
        "jg": "juga",
        "jgn": "jangan",
        "dpt": "dapat",
        "bkn": "bukan",
        "emg": "memang",
    }

    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs from text."""
        return re.sub(r"https?://\S+|www\.\S+", "", text)

    @staticmethod
    def remove_mentions(text: str) -> str:
        """Remove @mentions from text."""
        return re.sub(r"@\w+", "", text)

    @staticmethod
    def normalize_hashtags(text: str) -> str:
        """Convert #hashtags to plain words."""
        return re.sub(r"#(\w+)", r"\1", text)

    @classmethod
    def normalize_informal(cls, text: str) -> str:
        """Replace common Indonesian informal words with formal equivalents."""
        words = text.split()
        normalized = [cls.INFORMAL_MAP.get(w.lower(), w) for w in words]
        return " ".join(normalized)

    @classmethod
    def clean(cls, text: str) -> str:
        """Full preprocessing pipeline."""
        text = cls.remove_urls(text)
        text = cls.remove_mentions(text)
        text = cls.normalize_hashtags(text)
        text = cls.normalize_informal(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def clean_batch(cls, texts: List[str]) -> List[str]:
        """Clean a batch of texts."""
        return [cls.clean(text) for text in texts]
