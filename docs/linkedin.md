# Rascunho de post (não publicado)

Preencha os números só depois de rodar `uv run python -m eval.run` e `uv run pytest`.

---

Montei um atendente de WhatsApp com IA para o meu negócio de polpas, a E&V.

O que ele faz:
- Responde dúvidas com **RAG** e mostra de qual documento tirou a resposta.
- Calcula preço e registra pedido por **tool calling em SQL**, não pelo modelo, para não inventar valores.
- Quando não sabe, avisa e encaminha para uma pessoa.

O que eu mais aprendi: medir a qualidade. Criei uma avaliação com 35 perguntas (inclusive tentativas de prompt injection) e o resultado atual é [X]% de acertos.

Stack: Python, FastAPI, SQL, REST, Git, CI no GitHub Actions. Custo zero, com provedor de LLM intercambiável.

Código: github.com/21RodrigoS/atendente-ev

#Python #IA #RAG #FastAPI #Blip
