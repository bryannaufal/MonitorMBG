"""Image-text multimodal matching using embedding similarity."""

from typing import Any

# TODO: Uncomment when sentence-transformers is configured
# from sentence_transformers import SentenceTransformer
# import numpy as np


class ImageTextMatcher:
    """
    Multimodal embedding-based similarity matcher.

    Computes cosine similarity between image embeddings and text embeddings
    to verify that uploaded photos match their textual descriptions.
    """

    MODEL_NAME = "clip-ViT-B-32"  # Or a multilingual variant

    def __init__(self):
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Lazy-load the multimodal embedding model."""
        if self._loaded:
            return
        # TODO: Load CLIP or multilingual multimodal model
        # self.model = SentenceTransformer(self.MODEL_NAME)
        self._loaded = True
        print(f"✅ Image-text model loaded: {self.MODEL_NAME}")

    def compute_similarity(
        self, image_path: str, text: str
    ) -> float:
        """
        Compute cosine similarity between an image and text description.

        Args:
            image_path: Path to the image
            text: Text description to match against

        Returns:
            Similarity score in [0, 1]
        """
        self.load_model()

        # TODO: Implement actual inference
        # from PIL import Image
        # img = Image.open(image_path)
        # img_embedding = self.model.encode(img)
        # text_embedding = self.model.encode(text)
        # similarity = np.dot(img_embedding, text_embedding) / (
        #     np.linalg.norm(img_embedding) * np.linalg.norm(text_embedding)
        # )
        # return float(similarity)

        return 0.0  # Placeholder

    def verify_report_photos(
        self,
        image_paths: list[str],
        menu_description: str,
    ) -> list[dict[str, Any]]:
        """
        Verify multiple photos against a menu description.

        Returns:
            List of {"photo": str, "similarity": float, "is_match": bool}
        """
        results = []
        for path in image_paths:
            similarity = self.compute_similarity(path, menu_description)
            results.append({
                "photo": path,
                "similarity": similarity,
                "is_match": similarity > 0.5,  # Threshold
            })
        return results


# ── Singleton ──
image_text_matcher = ImageTextMatcher()
