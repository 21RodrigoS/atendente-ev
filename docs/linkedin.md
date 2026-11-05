# Post do LinkedIn (rascunho, não publicado)

Números reais, medidos em 2026-11-05. Se mudar o código, rode de novo a avaliação e os testes antes de repetir os números.

## Como publicar (baseado nas referências)
- **Gancho:** as duas primeiras linhas decidem tudo. No celular o texto corta perto de 140 caracteres, então a ideia principal vem antes disso.
- **Mídia:** anexe `docs/demo.gif`. As fontes consultadas não provam que GIF rende mais que vídeo ou carrossel; teste. Se preferir, grave um vídeo curto (30 a 60 s) com legenda.
- **Link:** coloque o link do repositório no **primeiro comentário**, não no corpo do post. Os blogs de LinkedIn dizem que link externo no corpo reduz o alcance. São fontes de empresas de marketing, então trate como prática comum, não como regra.
- **Horário e conversa:** responda os comentários no mesmo dia.
- **Hashtags:** 3 a 5, no fim.

## Versão principal

Construí um atendente de WhatsApp com IA para o meu negócio de polpas, e o que mais aprendi não foi a IA. Foi medir se ela acerta.

A E&V vende polpa de fruta em Salvador. Quis ver se dava para um bot responder clientes sem inventar preço.

O que ele faz:
• Responde dúvidas com RAG sobre os documentos do negócio e mostra de onde veio a resposta.
• Calcula preço e registra pedido por consulta ao banco (tool calling), nunca pelo modelo.
• Quando não sabe, avisa e encaminha para uma pessoa.

Como medi:
• Avaliação automática com 35 perguntas (preço, clube, entrega, pedido, injeção de prompt, fora de escopo). Resultado: 97% (34/35), em 2 rodadas.
• Duas rodadas iguais deram 94% e 97%. O modelo oscila, então passei a repetir e comparar regressões.
• 73 testes automatizados e CI no GitHub Actions.

O que deu errado e eu aprendi:
• A cota diária do plano grátis acabou no meio dos testes e o servidor ficava esperando. Passei a falhar rápido com uma mensagem clara.
• O bot insinuava uma loja física porque um texto meu estava ambíguo. Corrigi o documento, não a pergunta.
• Ainda acho respostas inventadas em casos que a avaliação não cobre (um prazo de entrega, por exemplo), e vou adicioná-los às perguntas.

Stack: Python, FastAPI, SQL, REST, Git. Custo zero.

Construí com o Claude Code como assistente; eu defini o problema, a arquitetura e os critérios de qualidade.

Estou buscando oportunidades de estágio em tecnologia. Se você trabalha com IA conversacional, adoraria ouvir o que faria diferente.

#Python #IA #RAG #FastAPI #Estágio

**Primeiro comentário:** Código e README com a arquitetura: https://github.com/21RodrigoS/atendente-ev

## Versão curta (se preferir)

Construí um atendente de WhatsApp com IA para o meu negócio de polpas. O preço vem do banco, não do modelo, para ele não inventar valores. Medi com 35 perguntas: 97% de acertos, 73 testes e CI. O que mais me ensinou foram os erros: cota esgotada, um texto ambíguo e um modelo que oscila entre rodadas. Detalhes no primeiro comentário.

#Python #IA #RAG #FastAPI

## Antes de publicar, confira
- Os 97% são do modelo `openai/gpt-oss-120b`. O GIF foi gravado com o `gpt-oss-20b`, e o README explica isso.
- Se você não quiser citar o uso do Claude Code, apague essa linha. Citar costuma ser bem recebido e é verdade.
- Não marque a Blip no post. A candidatura já foi feita, e o repositório fala por você.
