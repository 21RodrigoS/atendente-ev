from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.rag.chunking import Chunk, chunk_markdown
from app.rag.embedder import Embedder


@dataclass
class Hit:
    chunk: Chunk
    score: float


class VectorIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder: Embedder):
        self.chunks = chunks
        self.vectors = vectors
        self.embedder = embedder

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> "VectorIndex":
        vectors = embedder.embed([f"{c.heading}\n{c.text}" for c in chunks]) if chunks else np.zeros((0, 1))
        return cls(chunks, vectors, embedder)

    def search(self, query: str, k: int = 4) -> list[Hit]:
        if not query.strip() or not self.chunks:
            return []
        # vetores já normalizados: produto escalar = cosseno
        scores = self.vectors @ self.embedder.embed([query])[0]
        order = np.argsort(-scores)[:k]
        return [Hit(self.chunks[i], float(scores[i])) for i in order]


def load_index(knowledge_dir: Path, embedder: Embedder) -> VectorIndex:
    chunks: list[Chunk] = []
    for path in sorted(Path(knowledge_dir).glob("*.md")):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.name))
    return VectorIndex.build(chunks, embedder)
