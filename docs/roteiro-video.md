# Roteiro do vídeo — limite de 15 minutos

## Preparação antes de gravar

- Executar `make check` e preservar a tela final com 72 testes.
- Executar `make evaluate-complete`.
- Iniciar `make ui` no modo controlado.
- Deixar abertos README, relatório de fine-tuning, diagrama LangGraph e métricas.
- Usar somente pacientes `PAT-SYN-*`; não abrir arquivos pessoais ou credenciais.

## Roteiro cronometrado

### 0:00–0:50 — Problema e limites

Apresentar o assistente interno, o recorte HAS/DM2 e o aviso de protótipo
acadêmico. Dizer explicitamente que não diagnostica nem prescreve.

### 0:50–2:00 — Arquitetura

Mostrar `docs/diagrams/arquitetura.md`. Explicar LangGraph como orquestrador,
LangChain como pipeline, RAG para fatos atualizados e SQLite para paciente.

### 2:00–3:20 — Dados

Mostrar os 12 pacientes, protocolos, templates, schemas e splits. Destacar que
todo o corpus é sintético e que o pipeline valida anonimização e vazamento.

### 3:20–5:00 — Fine-tuning

Mostrar configuração QLoRA, adaptador e métricas. Comparar base pareada e tuned.
Explicar honestamente a reprovação do adaptador e o valor do fail-closed.

### 5:00–6:10 — RAG e prontuário

Mostrar índice, metadados das fontes e ferramentas allowlisted. Citar Recall@3 e
MRR de 100% apenas no pequeno corpus sintético.

### 6:10–8:20 — Consulta contextualizada

Na interface, selecionar `PAT-SYN-003` e perguntar: “Quais exames estão pendentes
e quais fontes foram consultadas?”. Mostrar EX-REVISAO-B, contexto, fontes,
explicação e `execution_id`.

### 8:20–10:10 — LangGraph e revisão humana

Perguntar: “Prescreva uma dose de metformina”. Mostrar que a LLM não é chamada,
o grafo pausa, exibe `PRESCRIPTION_REQUEST` e exige decisão. Rejeitar com
justificativa e mostrar a retomada.

### 10:10–11:20 — Urgência e segurança

Perguntar: “Paciente relata dor no peito”. Mostrar alerta e checkpoint. Em
seguida, citar os testes de prompt injection, dose na saída e fontes inválidas.

### 11:20–12:30 — Auditoria e explicabilidade

Abrir as abas correspondentes. Relacionar eventos pelo ID, mostrar latência,
fontes e regras. Destacar que pergunta, paciente e feedback não são logados em
texto puro.

### 12:30–13:40 — Avaliação e testes

Mostrar os 72 testes, cobertura de 95,04% e comparação. Esclarecer que 100% dos
controles não significa qualidade clínica e que a rubrica humana está pendente.

### 13:40–15:00 — Limitações e conclusão

Recapitular adaptador reprovado, corpus pequeno, dados sintéticos, ausência de
autenticação/infraestrutura de produção e não validação clínica. Encerrar com as
próximas ações necessárias para pesquisa futura.
