import re
import zlib
from typing import Protocol

import numpy as np

from app.tools import normalize

FASTEMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...


def _unit(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


class FastEmbedder:
    """Embeddings multilíngues locais (baixa o modelo na primeira execução)."""

    def __init__(self, model: str = FASTEMBED_MODEL):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model)

    def embed(self, texts: list[str]) -> np.ndarray:
        return _unit(np.array(list(self._model.embed(texts)), dtype=float))


class HashEmbedder:
    """Bag-of-words determinístico; só para testes, sem baixar modelo."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim))
        for i, text in enumerate(texts):
            for word in re.findall(r"\w+", normalize(text)):
                if len(word) > 2:
                    out[i, zlib.crc32(word.encode()) % self.dim] += 1
        return _unit(out)
