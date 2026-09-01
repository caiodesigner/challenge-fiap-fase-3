# Relatório da Etapa 6 — Integração LangChain

## Objetivo

Integrar a LLM customizada, o RAG e a base clínica estruturada em uma pipeline
com contratos explícitos e comportamento seguro diante de falhas.

## Composição

A implementação usa `RunnableLambda` em uma `RunnableSequence` com quatro etapas:

1. `validate_request`: valida pergunta, paciente e especialidade com Pydantic.
2. `retrieve_context`: seleciona ferramentas mínimas e recupera protocolos.
3. `generate_with_custom_llm`: monta prompt versionado e chama o adaptador QLoRA.
4. `validate_structured_response`: aplica parser JSON e schema de saída.

Cada função permanece independente do LangGraph, que será adicionado na próxima
etapa para controlar ramificações e human-in-the-loop.

## Minimização de contexto

O resumo básico é consultado somente quando há paciente. Outras ferramentas são
selecionadas por intenção textual determinística:

- exame/resultado/pendência: exames pendentes e resultados recentes;
- alergia: alergias;
- medicamento/prescrição/dose: medicamentos ativos.

SQL e seleção autônoma de ferramentas pela LLM não são permitidos.

## Prompt e fontes

O prompt `1.0.0` contém o schema JSON, a pergunta, o contexto mínimo e somente as
fontes recuperadas. Citações devolvidas pela LLM são descartadas; a resposta
final recebe as citações produzidas deterministicamente pelo retriever.

Sem paciente e sem fonte acima do limiar, o modelo não é chamado. O resultado é
`insufficient_evidence`.

## Saída estruturada

O contrato inclui status, classe, resumo, dados utilizados, orientação,
pendências, alertas, fontes, confiança, validação humana, limitações e aviso de
uso acadêmico. Campos extras ou ausentes invalidam a saída.

Classes `alert` e `refusal` têm validação humana forçada pela aplicação, mesmo se
o modelo responder o contrário.

## Falhas controladas

São tratados:

- paciente inexistente ou inválido;
- banco indisponível;
- falha ou incompatibilidade do retriever;
- ausência total de evidência;
- falha de inferência;
- JSON inválido;
- resposta incompatível com o schema.

Nenhuma dessas situações retorna uma orientação clínica assertiva.

## Demonstração real

A consulta de `PAT-SYN-003` recuperou:

- exame pendente `EX-REVISAO-B`;
- fonte `PR-HAS-001#S2`, versão 1.0;
- score 0,84066;
- três ferramentas mínimas relacionadas a exames.

O adaptador produziu uma saída incompatível com o schema. A chain a rejeitou e
retornou `model_output_rejected`, confiança baixa e validação humana obrigatória.
Esse é o comportamento esperado para um modelo previamente reprovado.

O registro completo está em `reports/chains/langchain_demo.json`.

## Limitações

- O provider local não oferece timeout interrompível de GPU nesta versão.
- A seleção determinística por palavras-chave é inicial.
- Não há memória conversacional.
- Alertas determinísticos e aprovação humana pertencem ao LangGraph.
- A chain valida estrutura e fontes, mas ainda não verifica semanticamente cada
  afirmação produzida pela LLM.

