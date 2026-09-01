# Relatório da Etapa 9 — Auditoria e explicabilidade

## Resultado

Cada nova execução do LangGraph recebe um UUID em `execution_id`, preservado no
checkpoint durante pausa e retomada. A trilha pode ser consultada por esse ID e
reconstrói início, pausa, decisão humana, conclusão ou falha.

## Eventos e conteúdo

Os eventos registram horário UTC, papel, estado, latência, versões de modelo,
adaptador, prompt, retrieval e política de segurança. Os detalhes incluem:

- intenção classificada;
- ferramentas/categorias de contexto efetivamente usadas;
- identificadores das fontes;
- regras determinísticas e flags de segurança;
- status e classe da resposta;
- erros e recusas;
- decisão humana e tamanho do feedback.

A pergunta, o texto do feedback, o identificador bruto do paciente e o
`thread_id` não são armazenados. Paciente e thread recebem referências SHA-256
truncadas apenas para correlação técnica. O uso de hash simples é suficiente
somente para esta base sintética; uma implantação real exigiria pseudonimização
com segredo gerenciado, política de retenção e armazenamento imutável.

## Persistência

`InMemoryAuditRecorder` atende testes isolados. `JsonlAuditRecorder` oferece uma
trilha append-only local, com um evento validado por linha, e permite filtrar os
eventos por `execution_id`. Falhas de escrita não são ocultadas: uma execução que
não possa ser auditada não deve prosseguir silenciosamente.

## Explicabilidade

`explain_state()` não chama a LLM. Ele deriva do estado persistido:

- intenção;
- categorias de dados do paciente consideradas;
- fontes com documento, seção, versão, vigência e score;
- regras e barreiras de segurança acionadas;
- revisão humana;
- erros e limitações.

Essa explicação relata fatores observáveis e não afirma explicar mecanismos
internos ou raciocínio oculto do modelo. O texto livre do feedback não é exposto;
a explicação informa somente se ele foi registrado.

## Evidência reproduzível

`make demo-audit` executa uma possível urgência, pausa para revisão, retoma com
rejeição e grava `reports/audit/demo_events.jsonl` e
`reports/audit/demo_summary.json`. O resumo inclui verificações automáticas de
que paciente, thread e pergunta não aparecem em texto puro na trilha.

## Limitações

- JSONL local não oferece imutabilidade, controle de acesso ou retenção de
  produção.
- As versões são metadados injetados pelo chamador; o bootstrap futuro da API
  deverá carregá-las das configurações versionadas.
- Métricas agregadas e avaliação longitudinal pertencem à Etapa 10.
