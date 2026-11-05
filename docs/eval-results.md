# Resultados da avaliação

Comando: `uv run python -m eval.run --repeat 3 --label "o que mudou"` (35 perguntas em `eval/questions.yaml`, Groq, `openai/gpt-oss-120b`).
Cada rodada fica salva em `eval/runs/` e `uv run python -m eval.compare` mostra regressões e melhorias entre duas rodadas.

## Rodada 0 (manual, 2026-11-05)
- **34/35 = 97%.** Falha: "Tem graviola?" (ver "Falhas do verificador" abaixo).

## Baseline: duas rodadas sem nenhuma mudança
- Rodada 1: **33/35 = 94%**. Rodada 2: **34/35 = 97%**.
- O modelo não é determinístico: a mesma pergunta mudou de resultado sem qualquer alteração. Por isso cada versão é medida com várias rodadas.
- A pergunta que oscilou foi "Qual o endereço da loja física?". Na rodada ruim, o bot respondeu que o ponto de atendimento principal fica em Brotas, o que insinua um endereço que não existe.
- **Causa:** `knowledge/entrega.md` dizia "atendimento principal no bairro de Brotas", e o modelo tratou isso como endereço.

## Mudança 1: `entrega.md` deixa explícito que não há endereço de loja nem retirada
- 3 rodadas: **33/35, 33/35, 33/35 (94%)**.
- Comportamento corrigido: o bot agora responde "Não temos endereço de loja física cadastrado. Entre em contato com a pessoa responsável", sem inventar nada.
- Mas a avaliação continua marcando essa pergunta como falha, pois o verificador de `refuse` só aceita o texto fixo de encaminhamento, e o bot respondeu com outra frase equivalente.

## Falhas do verificador (a resposta do bot está correta)
| Pergunta | Resposta do bot | Por que o verificador reprova |
|---|---|---|
| Tem graviola? | "Não, a graviola está fora de estoque." | Só aceita "sem estoque", "indisponível", "acabou"... e não "fora de estoque". |
| Qual o endereço da loja física? | "Não temos endereço de loja física cadastrado. Entre em contato com a pessoa responsável." | `refuse` exige o texto fixo exato. |

**Decisão (2026-11-05):** o verificador foi mantido como está, para não ajustar o critério depois de ver o resultado. O score reportado é **94% (33/35)**, e as duas falhas acima são conhecidas e explicadas.

## Limites
- 35 perguntas e 3 rodadas por versão dão só uma estimativa: 1 pergunta vale ~3 pontos percentuais.
- Os critérios de acerto são por palavras-chave, não por julgamento semântico.
