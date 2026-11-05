from pathlib import Path

from app.rag.chunking import chunk_markdown
from app.rag.embedder import HashEmbedder
from app.rag.index import VectorIndex, load_index


def test_chunk_by_h2_keeps_source_and_heading():
    text = "# Titulo\n\nintro\n\n## Entrega\n\nEntregamos em Salvador.\n\n## Vazio\n\n## Pagamento\n\nPix."
    chunks = chunk_markdown(text, "faq.md")
    headings = [c.heading for c in chunks]
    assert "Entrega" in headings and "Pagamento" in headings
    assert "Vazio" not in headings
    entrega = next(c for c in chunks if c.heading == "Entrega")
    assert entrega.source == "faq.md"
    assert "Salvador" in entrega.text


def test_search_returns_relevant_chunk():
    index = load_index(Path("knowledge"), HashEmbedder())
    hits = index.search("qual o desconto do clube quinzenal?")
    assert hits[0].chunk.source == "clube.md"


def test_search_scores_sorted_desc():
    index = load_index(Path("knowledge"), HashEmbedder())
    scores = [h.score for h in index.search("entrega em Brotas", k=4)]
    assert scores == sorted(scores, reverse=True)
    assert len(scores) == 4


def test_empty_query_returns_empty():
    index = load_index(Path("knowledge"), HashEmbedder())
    assert index.search("   ") == []


def test_build_with_no_chunks():
    index = VectorIndex.build([], HashEmbedder())
    assert index.search("oi") == []


def test_knowledge_has_no_sensitive_terms():
    text = " ".join(p.read_text(encoding="utf-8").lower() for p in Path("knowledge").glob("*.md"))
    for banned in ("custo", "margem", "atacado", "mapa"):
        assert banned not in text
