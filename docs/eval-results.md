# Resultados da avaliação

Comando: `uv run python -m eval.run` (35 perguntas em `eval/questions.yaml`, provedor Groq, `openai/gpt-oss-120b`).

## Rodada 1 (2026-11-05)

- **Score: 34/35 = 97%**
- Falha: "Tem graviola?" (esperado: responder que está sem estoque).
  - Resposta do bot: "Não, a graviola está fora de estoque no momento."
  - A resposta está correta. A verificação procurava "sem estoque", "indisponível", "acabou" etc. e não aceitava "fora de estoque". É uma falha do verificador, não do bot.
- Nenhuma alteração foi feita em documentos, prompt ou perguntas antes desta rodada.
- Limite: foi uma única execução. O modelo não é totalmente determinístico, então o resultado pode variar entre rodadas.
