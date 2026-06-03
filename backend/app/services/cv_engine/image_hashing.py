"""Perceptual hashing for duplicate and manipulated image detection."""

from typing import Any

from PIL import Image

# TODO: Uncomment when imagehash is available
# import imagehash

from app.utils.constants import PHASH_DUPLICATE_THRESHOLD, PHASH_SIMILAR_THRESHOLD


class ImageHasher:
    """
    Perceptual hashing engine for detecting duplicate or manipulated images.

    Uses pHash (perceptual hash) and dHash (difference hash) to generate
    fingerprints that are robust to minor image transformations.
    """

    @staticmethod
    def compute_phash(image_path: str, hash_size: int = 16) -> str:
        """
        Compute a perceptual hash for an image.

        Args:
            image_path: Path to the image file
            hash_size: Hash granularity (higher = more precise)

        Returns:
            Hex string of the perceptual hash
        """
        # TODO: Implement with imagehash
        # img = Image.open(image_path)
        # return str(imagehash.phash(img, hash_size=hash_size))
        return "0000000000000000"  # Placeholder

    @staticmethod
    def compute_dhash(image_path: str, hash_size: int = 16) -> str:
        """Compute a difference hash for an image."""
        # TODO: Implement with imagehash
        # img = Image.open(image_path)
        # return str(imagehash.dhash(img, hash_size=hash_size))
        return "0000000000000000"  # Placeholder

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """Compute the Hamming distance between two hash strings."""
        # TODO: Implement with imagehash
        # h1 = imagehash.hex_to_hash(hash1)
        # h2 = imagehash.hex_to_hash(hash2)
        # return h1 - h2
        return 0  # Placeholder

    @classmethod
    def is_duplicate(cls, hash1: str, hash2: str) -> bool:
        """Check if two images are likely duplicates."""
        return cls.hamming_distance(hash1, hash2) <= PHASH_DUPLICATE_THRESHOLD

    @classmethod
    def is_similar(cls, hash1: str, hash2: str) -> bool:
        """Check if two images are visually similar."""
        return cls.hamming_distance(hash1, hash2) <= PHASH_SIMILAR_THRESHOLD

    @classmethod
    def find_duplicates(
        cls, target_hash: str, existing_hashes: dict[int, str]
    ) -> list[dict[str, Any]]:
        """
        Find duplicate or similar images from a set of existing hashes.

        Args:
            target_hash: Hash of the image to check
            existing_hashes: {report_id: hash_string} mapping

        Returns:
            List of matches: [{"report_id": int, "distance": int, "is_duplicate": bool}]
        """
        matches = []
        for report_id, existing_hash in existing_hashes.items():
            distance = cls.hamming_distance(target_hash, existing_hash)
            if distance <= PHASH_SIMILAR_THRESHOLD:
                matches.append({
                    "report_id": report_id,
                    "distance": distance,
                    "is_duplicate": distance <= PHASH_DUPLICATE_THRESHOLD,
                })
        return sorted(matches, key=lambda x: x["distance"])


# ── Singleton ──
image_hasher = ImageHasher()
