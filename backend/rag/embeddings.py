"""Embedding generation using sentence-transformers (singleton model)."""

import logging
from typing import ClassVar

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Singleton embedding model using sentence-transformers.

    Lazily loads the model on first use and reuses it for subsequent calls.
    """

    _instance: ClassVar["EmbeddingModel | None"] = None
    _model = None

    def __new__(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                model_name = settings.CHROMA_SETTINGS["EMBEDDING_MODEL"]
                logger.info(f"Loading embedding model: {model_name}")
                self._model = SentenceTransformer(model_name)
                logger.info(f"Embedding model loaded successfully (dim={self._model.get_sentence_embedding_dimension()})")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}", exc_info=True)
                raise
        return self._model

    def encode(self, texts: list[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """Encode texts into embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])

        logger.debug(f"Encoding {len(texts)} texts")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings

    def encode_single(self, text: str) -> list[float]:
        """Encode a single text into an embedding.

        Args:
            text: Text to encode

        Returns:
            List of floats representing the embedding
        """
        embedding = self.encode([text])
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


def get_embedding_model() -> EmbeddingModel:
    """Get the singleton embedding model instance.

    Returns:
        EmbeddingModel instance
    """
    return EmbeddingModel()
