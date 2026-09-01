# Plano de Desenvolvimento — Tech Challenge Fase 3

## 1. Objetivo

Desenvolver um assistente virtual médico interno, baseado em uma LLM efetivamente customizada por fine-tuning, capaz de consultar dados estruturados de pacientes, contextualizar respostas com protocolos institucionais, coordenar fluxos clínicos por LangChain e LangGraph e manter validação humana, explicabilidade e auditoria.

O sistema será acadêmico, utilizará somente dados sintéticos ou comprovadamente anonimizados e servirá como apoio à decisão. Ele não realizará diagnóstico, prescrição ou conduta clínica autônoma.

## 2. Requisitos obrigatórios do enunciado

1. Fine-tuning de uma LLM com protocolos médicos, perguntas frequentes e modelos internos de laudos, receitas e procedimentos.
2. Preprocessamento, anonimização e curadoria dos dados.
3. Pipeline LangChain integrado à LLM customizada.
4. Consulta a bases estruturadas de prontuários e registros.
5. Contextualização das respostas com informações atualizadas do paciente.
6. Limites de atuação e validação humana para evitar sugestões impróprias.
7. Logging detalhado para rastreamento e auditoria.
8. Explicabilidade com indicação das fontes usadas.
9. Fluxos construídos com LangGraph.
10. Projeto modularizado em Python e README completo.
11. Dataset anonimizado ou sintético.
12. Relatório técnico com fine-tuning, descrição do assistente, diagrama do fluxo, avaliação e análise dos resultados.
13. Vídeo de até 15 minutos demonstrando treinamento, funcionamento, fluxo automatizado, respostas contextualizadas, logs e validação.

LLaMA, Falcon, PubMedQA e MedQuAD são exemplos ou sugestões do documento, não escolhas obrigatórias.

## 3. MVP definido

O MVP será restrito ao acompanhamento ambulatorial de adultos com hipertensão arterial sistêmica e diabetes mellitus tipo 2. O recorte permite demonstrar integração entre prontuário, exames, protocolos, alertas e validação humana sem apresentar o sistema como assistente médico generalista.

### Entradas

- Identificador de paciente sintético.
- Pergunta do profissional.
- Sintomas ou observações complementares opcionais.

### Saídas

- Resumo clínico relevante.
- Exames pendentes ou desatualizados.
- Orientação de apoio baseada em protocolo.
- Alertas detectados.
- Fontes e versões dos documentos consultados.
- Nível de confiança ou indicação de evidência insuficiente.
- Necessidade e motivo de validação humana.
- Identificador de auditoria.

## 4. Arquitetura planejada

```text
Interface CLI/API
       |
Validação da entrada e autorização simulada
       |
LangGraph — orquestrador clínico
       +--> prontuário estruturado
       +--> protocolos institucionais via RAG
       +--> verificação de exames pendentes
       +--> regras determinísticas de alerta
       +--> LLM customizada por fine-tuning
       +--> verificação de segurança e fontes
       +--> validação humana quando necessária
       |
Resposta estruturada + fontes + auditoria
```

- O fine-tuning ensinará terminologia, formato, comportamento e limites institucionais.
- O RAG fornecerá protocolos atualizados e rastreáveis; não substituirá o fine-tuning obrigatório.
- O banco estruturado fornecerá os dados atuais do paciente.
- Regras determinísticas tratarão alertas críticos que não devem depender somente da LLM.
- O LangGraph controlará estado, decisões, falhas e aprovação humana.

## 5. Estrutura pretendida

```text
data/{raw,synthetic,processed,splits,schemas}/
configs/{model,training,retrieval,safety}.yaml
src/assistente_medico/
  domain/ data/ training/ inference/ retrieval/ repositories/
  tools/ chains/ graph/ safety/ audit/ evaluation/ api/
scripts/
tests/{unit,integration,safety,evaluation}/
docs/
reports/{metrics,figures,deliverables}/
```

## 6. Etapas de desenvolvimento

### Etapa 0 — Formalizar escopo e critérios

**Status: concluída.**

- Fechar o domínio clínico do MVP.
- Definir jornadas demonstráveis.
- Separar apoio, alerta e prescrição.
- Criar matriz de rastreabilidade entre requisito, código, teste e evidência.
- Definir critérios de aceite antes do desenvolvimento.

**Saída:** especificação aprovada em `docs/etapa-0-especificacao.md`.

### Etapa 1 — Modelar e preparar dados sintéticos

**Status: concluída para o corpus inicial; ampliação e revisão especializada são portas de entrada da Etapa 3.**

- Criar protocolos fictícios, FAQs, modelos de laudos, modelos estruturais de receitas e procedimentos.
- Criar pacientes, prontuários, exames e eventos clínicos sintéticos.
- Definir schema instrucional JSONL e schemas dos dados estruturados.
- Implementar anonimização de nomes, documentos, contatos, endereços, identificadores e datas identificáveis.
- Eliminar duplicatas, normalizar termos/unidades, versionar fontes e verificar conflitos.
- Separar treino, validação e teste por documento ou paciente para evitar vazamento.

**Aceite:** dataset reproduzível, documentado, sintético/anonimizado e corretamente dividido.

### Etapa 2 — Medir o baseline

**Status: concluída com `qwen2.5:3b`; conjunto fechado e resultados preservados.**

- Selecionar o modelo-base e documentar sua licença.
- Criar conjunto fixo de avaliação não usado no treino.
- Avaliar respostas, segurança, aderência, formato, alucinações, latência e recursos.
- Preservar resultados para a comparação final.

**Aceite:** relatório de baseline com métricas e falhas representativas.

### Etapa 3 — Executar o fine-tuning

**Status: concluída como experimento reproduzível. O adaptador foi gerado, mas
reprovado para uso por não melhorar as métricas centrais de segurança; novas
iterações ficam condicionadas à ampliação e revisão especializada do corpus.**

- Usar modelo instrucional aberto compatível com o hardware.
- Aplicar PEFT com LoRA ou QLoRA.
- Versionar template, dados, seed, hiperparâmetros e ambiente.
- Monitorar treino e validação; salvar adaptadores, checkpoints, logs e curvas.
- Criar model card simplificado.

**Aceite:** pipeline reproduzível e evidência de melhoria sobre o baseline em métricas predefinidas.

### Etapa 4 — Implementar protocolos e RAG

**Status: concluída para o corpus sintético atual, com índice E5, filtros,
citações, limiar de ausência de evidência e avaliação Recall@K/MRR.**

- Dividir documentos em trechos semanticamente coerentes.
- Preservar documento, seção, versão e vigência nos metadados.
- Gerar embeddings, indexar e recuperar com filtros.
- Citar as fontes e impedir apresentação de fatos sem evidência suficiente.

**Aceite:** afirmações institucionais rastreáveis até documento e seção.

### Etapa 5 — Criar a base estruturada de prontuários

**Status: concluída com SQLite sintético, schema versionado, repositório somente
leitura, consultas parametrizadas, minimização e ferramentas allowlisted.**

- Modelar paciente, condições, alergias, medicamentos, exames, resultados, procedimentos, alertas e atendimentos.
- Usar SQLite ou PostgreSQL com dados sintéticos.
- Expor ferramentas restritas e consultas parametrizadas, sem SQL livre produzido pela LLM.
- Aplicar minimização de dados antes de montar o contexto.

**Aceite:** somente os dados necessários à solicitação chegam ao modelo.

### Etapa 6 — Integrar com LangChain

**Status: concluída com RunnableSequence, contexto mínimo, RAG, adaptador QLoRA,
schema Pydantic e fallback fail-closed para falhas de dependência ou saída.**

- Abstrair o provedor do modelo e carregar o adaptador fine-tuned.
- Versionar prompts e integrar retriever, ferramentas e parser estruturado.
- Tratar timeout, repetição, indisponibilidade e saída inválida.
- Retornar resumo, dados considerados, orientação, pendências, alertas, fontes, confiança e validação.

**Aceite:** respostas contextualizadas e rastreáveis, inclusive em falhas controladas.

### Etapa 7 — Orquestrar com LangGraph

**Status: concluída com grafo de estados, ramificações determinísticas,
checkpoint em memória e pausa/retomada explícita para revisão humana.**

- Criar estados para validar solicitação, classificar intenção, consultar prontuário, recuperar protocolos, verificar pendências, avaliar alertas, gerar e validar a resposta, obter revisão humana e auditar.
- Criar ramificações para paciente inexistente, dados insuficientes, urgência, pedido de prescrição, falta de fonte e falha de ferramenta.
- Adicionar checkpoint explícito de human-in-the-loop.

**Aceite:** decisões e estados inspecionáveis e reproduzíveis.

### Etapa 8 — Implementar segurança e validação

**Status: concluída com política `safety-v1`, barreiras de entrada e saída,
fail-closed e suíte adversarial integrada ao grafo.**

- Impedir prescrição final, alteração autônoma de prontuário e invenção de dados ou protocolos.
- Restringir ferramentas e validar entrada e saída.
- Conferir citações, escalar sinais críticos e minimizar dados pessoais.
- Testar prompt injection, acesso indevido, falta de contexto, fonte vencida, prescrição e urgência.

**Aceite:** todos os cenários críticos possuem comportamento seguro definido e testado.

### Etapa 9 — Implementar logging e explicabilidade

**Status: concluída com `execution_id`, eventos estruturados append-only,
mascaramento, reconstrução da trilha e explicação derivada do estado.**

- Registrar ID, horário, papel, versões de modelo/prompt, ferramentas, fontes, decisões, alertas, aprovação, latência, erros e recusas.
- Mascarar campos sensíveis dos logs.
- Explicar quais dados, fontes e regras influenciaram a resposta.

**Aceite:** uma execução pode ser reconstruída por seu ID de auditoria.

### Etapa 10 — Avaliar a solução

**Status: avaliação automatizada concluída e resultados consolidados. A rubrica
humana foi preparada, mas permanece pendente de dois revisores qualificados; o
adaptador e a solução para uso clínico seguem não aprovados.**

- Avaliar perguntas factuais e contextualizadas, pendências, urgências, ausência de evidência, pedidos proibidos e ataques.
- Comparar modelo-base, fine-tuned, fine-tuned + RAG e solução completa.
- Medir aderência, Recall@K/MRR, fundamentação, precisão das citações, segurança, recusas, alertas, validade estrutural e latência.
- Aplicar rubrica humana de correção, relevância, clareza, aderência, utilidade, segurança e fontes.

**Aceite:** relatório comparativo com resultados, erros, limitações e análise crítica.

### Etapa 11 — Garantir testes e qualidade

**Status: concluída com suíte unitária/integrada, quatro jornadas end-to-end
offline, cobertura mínima obrigatória e workflow de CI para Python 3.12.**

- Criar testes unitários de dados, regras, schemas, fontes e logs.
- Criar testes de integração do modelo, retriever, banco, grafo e human-in-the-loop.
- Criar testes end-to-end de casos normais, alertas, ausência de dados, recusas e falhas.
- Configurar lint, tipagem, cobertura e CI.

### Etapa 12 — Construir a interface de demonstração

**Status: concluída com interface Streamlit, modo controlado e real experimental,
visualização dos requisitos e revisão humana no checkpoint.**

- Exibir paciente sintético, pergunta, resposta, dados considerados, pendências, alertas, fontes, validação e ID de auditoria.
- Priorizar a visualização dos requisitos, sem tentar reproduzir um prontuário hospitalar completo.

### Etapa 13 — Finalizar documentação e entrega

**Status: pacote técnico concluído com README, relatório Markdown/PDF, cinco
diagramas, matriz final, licenças, checklist e roteiro. Gravação/publicação do
vídeo e avaliação humana permanecem ações manuais dos autores.**

- Completar README com instalação, configuração, dados, fine-tuning, avaliação, execução, testes, segurança e licenças.
- Produzir relatório com arquitetura, governança, treinamento, LangChain/LangGraph, avaliação, resultados, erros e limitações.
- Criar diagramas de arquitetura, LangGraph, preparação dos dados, treinamento e sequência de consulta.
- Preparar e gravar vídeo de no máximo 15 minutos.

## 7. Cronograma sugerido

1. **Sprint 1:** escopo, schemas, dados sintéticos e avaliação.
2. **Sprint 2:** baseline, fine-tuning e seleção do checkpoint.
3. **Sprint 3:** RAG, prontuário estruturado, ferramentas e LangChain.
4. **Sprint 4:** LangGraph, segurança, human-in-the-loop, logs e fontes.
5. **Sprint 5:** testes, avaliação comparativa e refinamento.
6. **Sprint 6:** README, relatório, diagramas, demonstração e vídeo.

## 8. Roteiro do vídeo

1. 0:00–1:00 — problema, escopo e segurança.
2. 1:00–2:30 — arquitetura e LangGraph.
3. 2:30–4:30 — dados, anonimização e fine-tuning.
4. 4:30–6:00 — baseline versus fine-tuned.
5. 6:00–10:00 — consulta contextualizada e fluxo automatizado.
6. 10:00–11:30 — pendências e alertas.
7. 11:30–13:00 — recusa segura e validação humana.
8. 13:00–14:00 — fontes, logs e auditoria.
9. 14:00–15:00 — resultados, limitações e conclusão.

## 9. Definição global de pronto

- [x] Pipeline reproduzível de fine-tuning.
- [x] LLM customizada realmente carregada pelo assistente.
- [x] Dataset publicado somente com dados sintéticos ou anonimizados.
- [x] Consulta a prontuários estruturados.
- [x] Protocolos recuperados e citados.
- [x] Fluxo principal com LangChain e LangGraph.
- [x] Detecção de pendências e alertas.
- [x] Condutas sensíveis submetidas à validação humana.
- [x] Logs auditáveis e explicabilidade.
- [x] Testes funcionais, adversariais e de integração.
- [x] Comparação do fine-tuned com o baseline.
- [x] README e relatório completos.
- [ ] Vídeo com todos os itens obrigatórios em até 15 minutos.
- [x] Ausência de dados reais, credenciais e segredos no repositório.
