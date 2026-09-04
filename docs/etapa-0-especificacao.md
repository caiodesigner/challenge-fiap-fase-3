# Etapa 0 — Especificação do escopo e critérios

**Status:** concluída para início da Etapa 1  
**Fonte normativa:** enunciado do Tech Challenge — Fase 3  
**Natureza do produto:** protótipo acadêmico de apoio à decisão, sem uso clínico real

## 1. Decisões de escopo

### 1.1 Domínio do MVP

O assistente atenderá exclusivamente o acompanhamento ambulatorial de pacientes adultos sintéticos com:

- hipertensão arterial sistêmica (HAS);
- diabetes mellitus tipo 2 (DM2);
- coexistência de HAS e DM2.

O assistente poderá responder sobre protocolos institucionais fictícios, resumir o contexto do paciente, identificar exames pendentes, produzir alertas predefinidos e sugerir próximos passos para revisão profissional.

### 1.2 Fora do escopo

- Diagnóstico autônomo.
- Prescrição, renovação ou alteração autônoma de medicamentos.
- Cálculo de dose para uso clínico real.
- Atendimento de emergência ou substituição de triagem profissional.
- Pacientes pediátricos, gestantes ou outras especialidades no MVP.
- Uso de prontuários ou documentos reais.
- Alteração direta do prontuário pela LLM.
- Assistente médico generalista.
- Implantação em ambiente hospitalar real.

### 1.3 Premissas

- Todos os pacientes e protocolos do protótipo serão sintéticos.
- Alertas críticos serão produzidos por regras explícitas, e não somente pela LLM.
- O fine-tuning e o RAG terão papéis complementares.
- Toda orientação será apresentada como apoio e dependerá de validação humana.
- Resultados acadêmicos não serão descritos como validação clínica.

## 2. Papéis e permissões

### Profissional solicitante

- Seleciona um paciente sintético.
- Faz perguntas e fornece observações.
- Consulta respostas, alertas e fontes.
- Não recebe uma prescrição autônoma.

### Revisor humano

- Aprova, rejeita ou solicita revisão de uma orientação sensível.
- Registra justificativa na decisão.

## 3. Jornadas do MVP

### J01 — Consulta a protocolo

**Entrada:** pergunta sobre acompanhamento de HAS ou DM2, sem paciente selecionado.  
**Fluxo:** classificar intenção, recuperar protocolo, gerar resposta, conferir fontes e auditar.  
**Saída:** orientação geral, fontes, limitações e aviso de apoio à decisão.  
**Aceite:** nenhuma informação específica de paciente é inventada; ao menos uma fonte válida sustenta a resposta.

### J02 — Pergunta contextualizada

**Entrada:** paciente sintético selecionado e pergunta clínica.  
**Fluxo:** recuperar dados mínimos do prontuário e protocolos relevantes, gerar e validar resposta.  
**Saída:** resumo dos dados considerados, orientação, fontes e ID de auditoria.  
**Aceite:** a resposta utiliza somente dados existentes e expõe quais dados influenciaram o resultado.

### J03 — Exames pendentes

**Entrada:** solicitação de revisão do acompanhamento do paciente.  
**Fluxo:** consultar exames, comparar com a regra/protocolo versionado e listar pendências.  
**Saída:** exame, motivo, data de referência e fonte da regra.  
**Aceite:** pendências correspondem exatamente aos registros e regras sintéticos.

### J04 — Alerta e validação humana

**Entrada:** caso sintético que atende a uma regra de alerta.  
**Fluxo:** regra determinística gera alerta, LangGraph encaminha para revisão e bloqueia conclusão autônoma.  
**Saída:** alerta, evidências, prioridade simulada e estado aguardando validação.  
**Aceite:** a execução não apresenta conduta final antes da decisão humana e registra toda a transição.

### J05 — Pedido de prescrição direta

**Entrada:** solicitação de medicamento, dose ou prescrição definitiva.  
**Fluxo:** detectar intenção proibida, recusar ação autônoma, apresentar limites e encaminhar ao profissional.  
**Saída:** recusa segura, explicação breve e ID de auditoria.  
**Aceite:** nenhuma prescrição final ou dose operacional é produzida.

### J06 — Evidência ou dados insuficientes

**Entrada:** pergunta sem suporte nos protocolos ou prontuário incompleto.  
**Fluxo:** detectar ausência de evidência, impedir resposta assertiva e pedir complemento ou revisão.  
**Saída:** limitação explícita, dados ausentes e fontes consultadas.  
**Aceite:** o assistente não preenche lacunas com informação inventada.

## 4. Classificação das respostas

| Classe | Descrição | Pode concluir automaticamente? | Validação humana |
|---|---|---:|---:|
| Informação | Explica protocolo geral com fontes | Sim | Opcional |
| Resumo | Organiza dados existentes do prontuário | Sim | Opcional |
| Pendência | Sinaliza exame ausente/desatualizado | Sim, como sinalização | Recomendada |
| Sugestão | Propõe próximo passo com base em protocolo | Não | Obrigatória |
| Alerta | Aponta condição definida por regra | Não | Obrigatória |
| Prescrição | Define medicamento, dose ou receita | Não permitida | Sempre encaminhada |
| Sem evidência | Não há base suficiente | Sim, como recusa/limitação | Conforme o caso |

## 5. Contrato funcional da resposta

Toda resposta final deverá disponibilizar:

- `execution_id`;
- `status`;
- `summary`;
- `patient_context_used`;
- `guidance`;
- `pending_exams`;
- `alerts`;
- `sources` com documento, seção e versão;
- `confidence` ou suficiência de evidência;
- `requires_human_validation`;
- `validation_reason`;
- `limitations`;
- aviso de uso acadêmico e apoio à decisão.

## 6. Requisitos não funcionais iniciais

### Segurança e privacidade

- Nenhum dado pessoal real no código, datasets, testes, logs ou demonstração.
- Princípio de menor privilégio para ferramentas.
- Consultas parametrizadas e sem SQL livre gerado pela LLM.
- Segredos fora do Git.
- Mascaramento de conteúdo sensível em auditoria.

### Reprodutibilidade

- Dependências e configurações versionadas.
- Seeds registradas quando aplicáveis.
- Versões de modelo, adaptador, dataset, prompt, protocolo e regra presentes nos artefatos.
- Comandos documentados no README.

### Manutenibilidade

- Código Python modular e tipado.
- Domínio desacoplado de LangChain/LangGraph sempre que possível.
- Testes automatizados e CI.
- Configuração externa ao código.

## 7. Critérios de aceite da Etapa 0

- [x] Domínio clínico restrito e registrado.
- [x] Público, finalidade e natureza acadêmica definidos.
- [x] Escopo e fora de escopo explícitos.
- [x] Seis jornadas demonstráveis definidas.
- [x] Apoio, alerta e prescrição diferenciados.
- [x] Human-in-the-loop definido para sugestões e alertas.
- [x] Contrato conceitual da resposta definido.
- [x] Requisitos não funcionais iniciais definidos.
- [x] Matriz de rastreabilidade criada.
- [x] Critérios de pronto globais registrados no plano mestre.

## 8. Matriz de rastreabilidade

| ID | Exigência do PDF | Implementação planejada | Verificação | Evidência de entrega |
|---|---|---|---|---|
| R01 | Fine-tuning de LLM | `training/`, script e configuração LoRA/QLoRA | comparação com baseline e teste de carregamento | código, adaptador, logs e relatório |
| R02 | Protocolos médicos | corpus sintético versionado e RAG | testes de recuperação e citação | dataset, índice reproduzível e exemplos |
| R03 | FAQs médicas | dataset instrucional sintético | validação de schema e curadoria | JSONL e documentação |
| R04 | Laudos, receitas e procedimentos | modelos sintéticos; receitas somente como estrutura documental | inspeção e validação de schema | dataset versionado |
| R05 | Preprocessing | pipeline determinístico | testes unitários e relatório de qualidade | script, logs e dados processados |
| R06 | Anonimização | detectores/substituidores e uso exclusivo de dados sintéticos | testes com identificadores artificiais | política, testes e relatório |
| R07 | Curadoria | deduplicação, normalização, versionamento e splits sem vazamento | testes estatísticos e revisão | relatório do dataset |
| R08 | Pipeline LangChain | chain com LLM fine-tuned, retriever, tools e parser | testes de integração | código e demonstração |
| R09 | Base estruturada | banco sintético e repositories parametrizados | testes de integração | schema, seed e consultas demonstradas |
| R10 | Contexto atualizado do paciente | ferramentas de leitura mínima | casos J02 e J03 | resposta e trace de execução |
| R11 | Limites de atuação | políticas, regras, validador de saída e recusas | suíte adversarial | testes e seção de segurança |
| R12 | Validação humana | checkpoint no LangGraph | caso J04 | trace e vídeo |
| R13 | Logging detalhado | auditoria estruturada e mascarada | reconstrução por `execution_id` | logs da demonstração |
| R14 | Explainability/fontes | metadados de documentos e regras | precisão de citações | resposta, testes e relatório |
| R15 | Python modular | pacote por responsabilidades | lint, tipagem e testes | árvore do repositório e CI |
| R16 | README completo | guia reprodutível | execução limpa seguindo o guia | `README.md` |
| R17 | Fluxos LangGraph | grafo com estados, ramos e checkpoint | testes de transição e E2E | código, diagrama e vídeo |
| R18 | Dataset anonimizado ou sintético | dados sintéticos publicados | inspeção automática/manual | diretório `data/` e data card |
| R19 | Relatório técnico | documento nas seções previstas no plano | checklist documental | relatório fonte e PDF |
| R20 | Avaliação e resultados | baseline e quatro configurações comparadas | métricas automáticas | tabelas, gráficos e análise |
| R21 | Diagrama do fluxo | diagramas versionados | revisão contra código | documentação e relatório |
| R22 | Vídeo de até 15 minutos | roteiro cronometrado | checklist antes da entrega | link/arquivo final |
