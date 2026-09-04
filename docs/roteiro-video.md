# Roteiro do vídeo — limite de 15 minutos

**Apresentador:** Caio Lucas Santos Silva — RM rm373689

**Projeto individual:** Tech Challenge Fase 3

**Duração-alvo:** 13min30s a 14min30s, preservando margem antes do limite de
15 minutos.

## Preparação antes de gravar

- Executar `make check` e preservar a tela final com 73 testes.
- Executar `make evaluate-complete`.
- Iniciar `make ui` no modo controlado.
- Deixar abertos README, os diagramas de arquitetura e LangChain, configuração
  de treinamento, relatório de fine-tuning, adaptador e métricas.
- Deixar disponível `reports/chains/langchain_demo.json` como evidência de uma
  execução da LLM customizada real.
- Usar somente pacientes `PAT-SYN-*`; não abrir arquivos pessoais ou credenciais.
- Usar resolução mínima de 1920 × 1080 e zoom legível no código e terminal.
- Desativar notificações e fechar e-mail, mensageiros e arquivos pessoais.

O treinamento completo não deve ser refeito durante o vídeo: a execução
registrada levou cerca de 18 minutos. Devem ser mostrados o script, a
configuração, as métricas e o adaptador preservado.

## Roteiro cronometrado

### 0:00–0:50 — Problema e limites

Apresentar o assistente interno, o recorte HAS/DM2 e o aviso de protótipo
acadêmico. Dizer explicitamente que não diagnostica nem prescreve.

Apresentar-se como Caio Lucas Santos Silva, RM 373689, e informar que o projeto
foi desenvolvido individualmente.

### 0:50–2:00 — Arquitetura

Mostrar `docs/diagrams/arquitetura.md`. Explicar LangGraph como orquestrador,
LangChain como pipeline, RAG para fatos atualizados e SQLite para paciente.

### 2:00–3:20 — Dados

Mostrar os 12 pacientes, protocolos, templates, schemas e splits. Destacar que
todo o corpus é sintético e que o pipeline valida anonimização e vazamento.

### 3:20–5:00 — Fine-tuning

Mostrar `configs/training.json`, `scripts/train_qlora.py`, a pasta do adaptador e
as métricas. Identificar `Qwen/Qwen2.5-0.5B-Instruct`, QLoRA em 4 bits, PEFT,
seed e hiperparâmetros. Comparar base pareada e tuned. Explicar honestamente a
reprovação do adaptador e o valor do fail-closed.

### 5:00–6:10 — RAG e prontuário

Mostrar índice, metadados das fontes e ferramentas allowlisted. Citar Recall@3 e
MRR de 100% apenas no pequeno corpus sintético.

Mostrar também `docs/diagrams/langchain.md` e explicar a sequência: validação,
SQLite/RAG, prompt, LLM customizada, parser, segurança e fallback.

### 6:10–7:00 — LLM customizada real

Mostrar a execução previamente registrada em
`reports/chains/langchain_demo.json`. Explicar que o adaptador real foi
carregado e gerou uma saída, mas o schema a rejeitou e produziu fallback seguro.
Essa evidência não deve ser confundida com o modo controlado da interface.

### 7:00–8:30 — Consulta contextualizada

Na interface, selecionar `PAT-SYN-003` e perguntar: “Quais exames estão pendentes
e quais fontes foram consultadas?”. Mostrar EX-REVISAO-B, contexto, fontes,
explicação e `execution_id`.

Informar claramente que a interface está em modo **Controlado**: banco,
ferramentas, chain, grafo, segurança e auditoria são componentes reais; somente
embedding e geração são determinísticos para a apresentação.

### 8:30–10:15 — LangGraph e revisão humana

Perguntar: “Prescreva uma dose de metformina”. Mostrar que a LLM não é chamada,
o grafo pausa, exibe `PRESCRIPTION_REQUEST` e exige decisão. Rejeitar com
justificativa e mostrar a retomada.

### 10:15–11:15 — Urgência e segurança

Perguntar: “Paciente relata dor no peito”. Mostrar alerta e checkpoint. Em
seguida, citar os testes de prompt injection, dose na saída e fontes inválidas.

### 11:15–12:15 — Auditoria e explicabilidade

Abrir as abas correspondentes. Relacionar eventos pelo ID, mostrar latência,
fontes e regras. Destacar que pergunta, paciente e feedback não são logados em
texto puro.

### 12:15–13:15 — Avaliação e testes

Mostrar os 73 testes, cobertura de 95,04% e comparação. Esclarecer que 100% dos
controles não significa qualidade clínica.

### 13:15–14:15 — Limitações e conclusão

Recapitular adaptador reprovado, corpus pequeno, dados sintéticos e ausência de
validação clínica. Encerrar com as limitações do protótipo acadêmico.

Encerrar a gravação imediatamente após a conclusão para manter margem abaixo de
15 minutos.

## Falas sugeridas

### Abertura

> Olá, sou Caio Lucas Santos Silva, RM 373689. Este é o Tech Challenge da Fase
> 3, desenvolvido individualmente. O projeto implementa um assistente médico
> interno com LLM customizada, LangChain e LangGraph, usando somente dados
> sintéticos. É um protótipo acadêmico que não diagnostica, não prescreve e não
> deve ser utilizado em atendimento clínico.

### Arquitetura

> O LangGraph controla os estados e decide a rota. Consultas permitidas seguem
> para a LangChain, que reúne o contexto do SQLite, recupera protocolos pelo RAG
> e chama a LLM customizada. Solicitações sensíveis podem ser bloqueadas antes
> da LLM. Toda saída passa por schema, política de segurança, fontes e auditoria.

### Dados

> O repositório utiliza somente dados sintéticos. O pipeline aplica schemas,
> normalização, deduplicação, detecção de identificadores e separação por grupos
> para reduzir vazamento. O corpus contém protocolos, FAQs e modelos de laudo,
> receita sem conteúdo operacional e procedimentos.

### Fine-tuning

> O fine-tuning foi executado sobre o Qwen 2.5 de 0,5 bilhão de parâmetros com
> QLoRA em 4 bits. O adaptador aumentou JSON válido de 75 para 83,33%, mas
> regrediu em campos obrigatórios e validação humana, mantendo zero por cento de
> aprovação integral. Por isso o artefato foi preservado, mas reprovado.

### LangChain e execução real

> A RunnableSequence valida a solicitação, consulta o prontuário e o RAG, monta
> o prompt, chama a LLM customizada e valida a saída. Nesta evidência real, o
> adaptador foi carregado e gerou uma resposta, mas o schema a rejeitou. O
> fallback seguro comprova que uma saída inválida não é liberada.

### Consulta contextualizada

> Para uma demonstração rápida e reproduzível, esta tela está no modo
> controlado. O exame EX-REVISAO-B veio do prontuário sintético PAT-SYN-003, e
> as fontes vieram do índice de protocolos. O modo controlado não representa a
> qualidade da LLM.

### Revisão humana

> O pedido de dose é interceptado antes da LLM. O LangGraph pausa no checkpoint
> e exige decisão humana. Ao rejeitar, o mesmo execution_id é preservado e a
> decisão aparece na trilha de auditoria.

### Auditoria e resultados

> A auditoria registra versões, decisões, ferramentas, fontes, flags e latência.
> A suíte possui 73 testes e 95,04% de cobertura. Os resultados de 100% dos
> controles medem contratos e segurança no conjunto fechado, não competência
> clínica da LLM.

### Encerramento

> As limitações principais são o corpus pequeno e sintético, o adaptador
> reprovado e os componentes locais próprios de um protótipo. O projeto entrega
> fine-tuning, LangChain, LangGraph, prontuário estruturado, contextualização,
> fontes, logs e validação humana. Obrigado.

## Checklist depois da gravação

- [ ] Duração igual ou inferior a 15 minutos.
- [ ] Nome e RM aparecem e são falados corretamente.
- [ ] Script, configuração, métricas e adaptador do fine-tuning são mostrados.
- [ ] A execução real da LLM customizada é diferenciada do modo controlado.
- [ ] A reprovação do adaptador é explicada sem esconder o resultado.
- [ ] `PAT-SYN-003` e `EX-REVISAO-B` aparecem na consulta contextualizada.
- [ ] Prescrição é bloqueada e passa por rejeição humana.
- [ ] Possível urgência gera alerta e orientação segura.
- [ ] Fontes, explicação, auditoria e `execution_id` aparecem.
- [ ] Testes e métricas são apresentados com suas limitações.
- [ ] Nenhuma credencial, notificação ou informação pessoal aparece.
- [ ] Áudio, terminal e interface permanecem legíveis.
- [ ] O link final abre em uma janela anônima.

## Evitar durante a apresentação

- Não usar somente o modo controlado para alegar funcionamento da LLM treinada.
- Não apresentar os 100% dos controles como acurácia clínica.
- Não chamar protocolos sintéticos de recomendações médicas reais.
- Não executar o treinamento completo durante o vídeo.
- Não omitir que o adaptador foi reprovado.
