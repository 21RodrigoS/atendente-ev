# Atendente E&V — design (rascunho para aprovação)

Data: 2026-11-05 · Autor: Hugo Rodrigo · Repositório: `github.com/21RodrigoS/atendente-ev` (público)

## 1. Intenção e porquê
Projeto de portfólio para o **Estágio Blip 2027** (inscrições até 30/11/2026). A Blip vende IA conversacional no WhatsApp (Blip Go para pequenos negócios, Blip Studio para agentes). O projeto é um **atendente de WhatsApp com IA para a E&V Polpas**, negócio real do Hugo. Ele mostra os requisitos da vaga (Python, SQL, Git, APIs REST) aplicados ao que a Blip faz.

Frase para a entrevista: "Construí um atendente com IA para o meu negócio de polpas, com RAG, ferramentas de consulta a banco e avaliação automática da qualidade das respostas."

## 2. Objetivos
- API REST em Python que recebe mensagem de cliente e devolve resposta.
- **RAG** sobre documentos da E&V (sabores, clube, entrega, regras de pedido, perguntas frequentes), com citação da fonte.
- **Tool calling** para dados exatos: preço, disponibilidade, criar pedido. Dado exato nunca vem de busca vetorial.
- Simulador de WhatsApp (web) para demo. Webhook compatível com o formato do WhatsApp Cloud API, para plugar depois.
- Painel simples: conversas, pedidos, respostas sem base (para melhorar os documentos).
- **Avaliação do RAG**: ~30 perguntas com resposta esperada, score de acertos, rodável por comando.
- Testes automatizados, CI no GitHub Actions, README com arquitetura, GIF/vídeo de demo.
- Custo zero.

## 3. Não objetivos (por enquanto)
- Integração real com Meta/WhatsApp (exige aprovação). Fica como próximo passo documentado.
- Pagamentos, login de cliente, vários canais, app mobile.

## 4. Anti-objetivos (seria fracasso mesmo funcionando)
- Bot que inventa preço, sabor ou prazo.
- Repositório que parece cópia de tutorial, sem testes nem README claro.
- Vazar dados: custos e margem da E&V, telefone pessoal, dados de clientes reais.
- Chave de API no Git.
- Projeto que não fica pronto antes de 30/11.

## 5. Restrições
- Prazo: 25 dias, ~12h/semana de estudo/dev (plano atual) mais os 2 dias livres.
- Custo zero: sem cartão, sem crédito pago.
- Hugo está aprendendo Python; o código deve ser legível e explicável por ele em entrevista.
- Dados do repositório público: só preços de venda e informações já públicas. **Sem custo/margem, sem clientes reais** (LGPD). Clientes na demo são sintéticos.
- Sem afirmações de saúde/qualidade sobre as polpas (não há registro no MAPA).
- Conta GitHub: 21RodrigoS (perfil usado nas candidaturas).

## 6. Abordagens consideradas
| Opção | Ideia | Veredito |
|---|---|---|
| 1. Atendente E&V com RAG + tools | Negócio real, requisitos da vaga, produto da Blip | **Escolhida pelo Hugo** |
| 2. Mini-Blip Studio | Construtor de fluxos/agentes | Raso demais em 25 dias |
| 3. Análise de conversas (dados) | Sentimento, painel | Menos ligado ao produto central |

Escolha do modelo (decidida pelo Hugo, com minha recomendação):
- **Geração:** Groq (Llama 3.3 70B), plano gratuito. Limites mudam e as fontes divergem: conferir em console.groq.com antes de depender.
- **Embeddings:** local (`multilingual-e5-small`), sem cota.
- **Interface `LLMProvider`** com implementação Groq e Gemini, trocável por variável de ambiente. Testes usam um provedor falso, sem rede.
- Descartado: Ollama local como padrão (exige máquina forte e a demo pública não funcionaria).

## 7. Arquitetura (decisões minhas, ajustáveis)
- **FastAPI** + Pydantic. **SQLite** (pedidos, produtos, conversas) com SQLAlchemy. **Chroma** ou sqlite-vec para vetores (escolher o mais simples na implementação).
- Fluxo: mensagem → classificar intenção → (a) pergunta de conhecimento: RAG com *top-k*, resposta só com base nos trechos; sem trecho relevante: "não sei" e encaminha ao Hugo; (b) preço/estoque/pedido: ferramentas SQL; → resposta.
- Guardas: limite de requisições por IP, tamanho máximo de mensagem, instruções do sistema protegidas contra *prompt injection* simples (o cliente não altera preço).
- Documentos do RAG em Markdown versionados em `knowledge/`.
- Estrutura: `app/` (api, rag, tools, providers), `knowledge/`, `eval/`, `tests/`, `web/` (simulador + painel), `docs/`.

## 8. Cronograma (05/11 → 30/11)
- **Candidatura primeiro:** enviar a inscrição na Blip até ~10/11 com o perfil e GitHub; o link do projeto vai no currículo/LinkedIn assim que existir. Não esperar o projeto ficar pronto para se inscrever.
- 05–11/11: repositório, API, banco, provedor Groq, conversa básica.
- 12–18/11: RAG, documentos da E&V, citação de fonte, tools de preço e pedido.
- 19–25/11: avaliação do RAG, testes, CI, simulador web e painel.
- 26–29/11: README, GIF/vídeo, texto do LinkedIn, revisão de segurança (chaves, dados). Folga no dia 30 para imprevistos.
- Corte de escopo se atrasar: painel primeiro, depois simulador. RAG, tools e avaliação não se cortam.

## 9. O que fica para quem implementa
Escolha final do vetor (Chroma vs sqlite-vec), tamanho dos trechos, prompts, nomes de módulos, formato do simulador.

## 10. Pontos a confirmar com o Hugo
- Nome do repositório (`atendente-ev` proposto).
- Criar e publicar o repositório no GitHub exige o OK dele no momento.
- Quais informações da E&V podem ser públicas (sabores, preços de venda, região de entrega).
