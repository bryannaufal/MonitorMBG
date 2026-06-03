"""Topic clustering using BERTopic for dynamic issue discovery."""

from typing import Any

# TODO: Uncomment when dependencies are installed
# from bertopic import BERTopic


class TopicClusterer:
    """
    BERTopic-based dynamic topic modeling for complaint clustering.

    Discovers emerging issue themes from complaint text without
    pre-defined categories.
    """

    def __init__(self):
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Lazy-load or initialize the BERTopic model."""
        if self._loaded:
            return
        # TODO: Initialize BERTopic with Indonesian embedding model
        # self.model = BERTopic(
        #     embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        #     language="indonesian",
        #     verbose=True,
        # )
        self._loaded = True
        print("✅ BERTopic model initialized")

    def fit_transform(self, documents: list[str]) -> tuple[list[int], Any]:
        """
        Fit the model and transform documents into topic assignments.

        Returns:
            (topic_ids, topic_info)
        """
        self.load_model()
        # TODO: Implement actual clustering
        # topics, probs = self.model.fit_transform(documents)
        # return topics, self.model.get_topic_info()

        return [0] * len(documents), {}  # Placeholder

    def transform(self, documents: list[str]) -> list[int]:
        """Assign topics to new documents using a pre-fitted model."""
        self.load_model()
        # TODO: self.model.transform(documents)
        return [0] * len(documents)  # Placeholder

    def get_topics(self) -> dict[int, list[tuple[str, float]]]:
        """Get discovered topics and their top keywords."""
        if self.model is None:
            return {}
        # TODO: return self.model.get_topics()
        return {}


# ── Singleton ──
topic_clusterer = TopicClusterer()
