# Matriz de rastreabilidade final

| ID | Requisito | Implementação | Verificação | Evidência |
|---|---|---|---|---|
| R01 | Fine-tuning | `training/`, `train_qlora.py`, adaptador v2 | avaliação pareada | relatório de fine-tuning e métricas |
| R02–R07 | Dados, protocolos, FAQs, templates e anonimização | `data/`, schemas e pipeline determinístico | testes de dados | data card e política de dados |
| R08 | LangChain | `chains/assistant.py` | testes de chain e E2E | demo e relatório LangChain |
| R09–R10 | Prontuário e contexto | SQLite, repository e tools | testes de repositório/tools/E2E | relatório da base |
| R11 | Limites | `safety-v1` e regras determinísticas | suíte adversarial | relatório de segurança |
| R12 | Validação humana | `interrupt` + `Command(resume)` | testes de pausa/retomada | demo LangGraph |
| R13 | Logging | eventos JSONL por `execution_id` | reconstrução E2E | demo de auditoria |
| R14 | Fontes e explicação | citações RAG + `explain_state` | validação de fontes | relatórios RAG/auditoria |
| R15 | Python modular | pacote `assistente_medico` | Ruff, mypy, 73 testes | CI e relatório de qualidade |
| R16 | README | guia consolidado | revisão documental | `README.md` |
| R17 | LangGraph | grafo condicional persistido | testes unitários/E2E | código e diagrama |
| R18 | Dados sintéticos | 12 pacientes e corpus fictício | schemas e validação | `data/README.md` |
| R19 | Relatório técnico | relatório consolidado | checklist de entrega | Markdown e PDF |
| R20 | Avaliação | baseline, pareado, tuned, RAG e controles | métricas fechadas | relatório final de avaliação |
| R21 | Diagramas | seis diagramas Mermaid, incluindo fluxo LangChain | revisão contra código | `docs/diagrams/` |
| R22 | Vídeo ≤15 min | roteiro cronometrado | checklist manual | `docs/roteiro-video.md` |
