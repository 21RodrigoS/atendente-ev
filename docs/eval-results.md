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

**Decisão (2026-11-05):** o verificador foi mantido como está, para não ajustar o critério depois de ver o resultado. Naquela data o score era **94% (33/35)**, com as duas falhas acima conhecidas e explicadas (o score atual está mais abaixo).

## Limites
- 35 perguntas e 3 rodadas por versão dão só uma estimativa: 1 pergunta vale ~3 pontos percentuais.
- Os critérios de acerto são por palavras-chave, não por julgamento semântico.

## Mudança 2: agente sem Markdown, fontes honestas e margem de relevância (2026-11-05)
Motivo: na demo no simulador apareciam asteriscos literais (`**R$ 54,00**`) e fontes enganosas (um preço calculado pelo banco citava `pedidos.md`, `faq.md` e `sobre.md`).
- Prompt pede texto puro, sem Markdown.
- Quando a resposta usa ferramenta, a fonte mostrada é "banco de dados".
- Só entram no contexto os trechos até 0,15 de pontuação abaixo do melhor (e no máximo 2 fontes mostradas).
- 2 rodadas: **34/35 e 34/35 (97%)**.
- `eval.compare` contra a rodada anterior: **0 regressões, 1 melhoria** ("Qual o endereço da loja física?" passou a recusar). Menos contexto irrelevante fez o modelo encaminhar em vez de responder.
- Única falha restante: "Tem graviola?" (falha conhecida do verificador, mantido sem alteração conforme a decisão acima).

**Score atual reportado: 97% (34/35)**, com a ressalva do verificador.

## Incidentes durante a avaliação
- Uma rodada foi perdida por um erro de impressão de caractere especial no console do Windows. Corrigido forçando UTF-8 na saída.
- Uma terceira rodada ficou travada por mais de 8 minutos e foi encerrada manualmente. A causa não foi investigada. O plano grátis tem limite de 8.000 tokens por minuto e 1.000 requisições por dia, e o script ainda não tem um tempo máximo por rodada.

### Atualização sobre a rodada travada
A causa foi encontrada depois: a **cota diária de tokens do plano grátis do Groq** (200.000 por dia por modelo) acabou. As rodadas de avaliação consomem tokens (as 7 rodadas do dia mais testes esgotaram a cota), e o cliente esperava a liberação em vez de falhar. Agora, se o provedor pedir uma espera maior que 30 s, a chamada falha na hora e o atendente responde com a mensagem de instabilidade. Planeje as rodadas de avaliação com a cota em mente: cada rodada de 35 perguntas usa uma parte relevante dela.
