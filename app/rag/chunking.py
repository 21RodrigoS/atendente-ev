import re
from dataclasses import dataclass


@dataclass
class Chunk:
    source: str
    heading: str
    text: str


def chunk_markdown(text: str, source: str) -> list[Chunk]:
    """Quebra o Markdown em um trecho por seção `##`; seções sem corpo são descartadas."""
    chunks: list[Chunk] = []
    for part in re.split(r"(?m)^## ", text)[1:]:
        heading, _, body = part.partition("\n")
        body = body.strip()
        if body:
            chunks.append(Chunk(source=source, heading=heading.strip(), text=body))
    return chunks
