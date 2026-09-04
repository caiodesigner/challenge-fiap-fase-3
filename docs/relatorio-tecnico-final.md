# Assistente Médico Interno com LLM Customizada

## Relatório técnico — Tech Challenge Fase 3

**Natureza:** protótipo acadêmico com dados exclusivamente sintéticos  
**Domínio:** acompanhamento ambulatorial de adultos com HAS e DM2  
**Autor:** Caio Lucas Santos Silva

**RM:** rm373689

**Desenvolvimento:** individual

**Data de consolidação:** 4 de setembro de 2026

## Resumo

Este trabalho implementa um assistente interno de apoio à decisão que combina
uma LLM customizada por QLoRA, recuperação de protocolos, consulta a prontuário
sintético, orquestração LangChain/LangGraph, regras determinísticas, validação
humana, auditoria e explicabilidade.

O resultado central é duplo. A arquitetura de controle funcionou nos casos
fechados do protótipo, mas o adaptador treinado não melhorou métricas essenciais
de estrutura e segurança e foi formalmente reprovado. O sistema demonstra,
portanto, tanto o pipeline obrigatório de customização quanto a necessidade de
não aprovar um modelo apenas porque o treinamento foi concluído.

O projeto não é dispositivo médico, não foi validado clinicamente e não pode ser
usado para diagnóstico, prescrição ou atendimento.

## 1. Problema e escopo

O MVP organiza informações para profissionais em seis jornadas: consulta a
protocolo, resumo contextualizado, exames pendentes, alerta com revisão humana,
recusa de prescrição e ausência de evidência.

O domínio foi limitado a adultos sintéticos com hipertensão e diabetes tipo 2.
Pediatria, gestação, emergência, diagnóstico, cálculo de dose, prescrição e
alteração autônoma do prontuário permanecem fora do escopo.

## 2. Arquitetura

A interface envia uma solicitação tipada ao LangGraph. Antes da geração, o grafo
valida a entrada, verifica prompt injection e escopo, classifica intenção e aplica
regras que desviam prescrição e possível urgência. Rotas normais acionam a
LangChain, que consulta ferramentas allowlisted, recupera protocolos e monta o
prompt da LLM. A saída passa por schema e política de segurança. Respostas
sensíveis pausam em checkpoint até uma decisão humana.

Toda execução recebe `execution_id`, fontes e explicação derivada do estado. A
trilha registra decisões e versões sem armazenar pergunta, feedback ou
identificadores brutos.

Consulte os diagramas de arquitetura e sequência em `docs/diagrams/`.

## 3. Dados e governança

Foram gerados 12 pacientes sintéticos, protocolos fictícios para HAS, DM2 e
segurança, templates documentais e exemplos instrucionais. Schemas JSON validam
os artefatos. A preparação normaliza termos, remove duplicatas, aplica detectores
de identificadores e separa treino, validação e teste por grupos para reduzir
vazamento.

O SQLite é reproduzível a partir dos JSONs e do schema SQL. O acesso de runtime
usa `mode=ro`, `query_only`, consultas parametrizadas e operações específicas.
A LLM nunca recebe SQL livre nem acesso de escrita.

## 4. Fine-tuning

O modelo-base foi `Qwen/Qwen2.5-0.5B-Instruct`, customizado com PEFT/QLoRA em
4 bits. Dados, seed, template, hiperparâmetros, métricas e adaptadores foram
preservados. Duas execuções permitiram corrigir mascaramento e ampliar o corpus.

No conjunto fechado de 12 casos, o modelo-base pareado obteve 75% de JSON válido,
75% de campos exigidos e 0% de aprovação integral. O adaptador obteve 83,33% de
JSON válido, mas 0% de campos exigidos, 8,33% de correspondência de validação
humana e 0% de aprovação integral.

A melhora isolada em JSON e recall de termos não compensou as regressões. O
adaptador permanece disponível como artefato experimental, porém reprovado para
uso aprovado.

## 5. RAG e prontuário

O RAG usa `intfloat/multilingual-e5-small`, chunks por seção, metadados de
documento, versão, vigência e especialidade, além de limiar de ausência de
evidência. No conjunto sintético de nove casos, Recall@3, MRR e rejeição fora do
escopo foram 100%. O tamanho reduzido impede generalização dessas métricas.

As ferramentas recuperam somente resumo mínimo, pendências, resultados recentes,
alergias e medicamentos ativos. O contexto enviado ao modelo é selecionado pela
pergunta e todas as fontes institucionais são substituídas pelos resultados reais
do retriever, não pelas citações geradas pela LLM.

## 6. LangChain e LangGraph

A LangChain usa uma `RunnableSequence` para validação, enriquecimento, geração e
parsing. Timeout, indisponibilidade, paciente inexistente, ausência de evidência
e JSON inválido produzem fallback de baixa confiança.

### Fluxo LangChain

[[LANGCHAIN_DIAGRAM]]

O diagrama apresenta a consulta estruturada ao prontuário e a recuperação de
protocolos como entradas independentes do prompt. A saída da LLM customizada só
é liberada depois do parsing, da validação do schema, das citações e da política
de segurança. Falhas seguem um caminho `fail-closed`.

O LangGraph controla as ramificações e o human-in-the-loop. `interrupt()` pausa o
estado e `Command(resume=...)` exige o mesmo `thread_id`. Aprovação preserva a
resposta; rejeição substitui a orientação por uma recusa segura. O checkpointer
em memória é adequado apenas ao protótipo.

## 7. Segurança

A política `safety-v1` atua antes e depois da LLM. Ela bloqueia prompt injection,
tentativa de escrever no prontuário e populações fora do escopo. Na saída, rejeita
dose operacional, citações inválidas, duplicadas ou futuras, informação
institucional sem fonte e classe sensível sem revisão humana.

Prescrição e termos de possível urgência são tratados antes do modelo. Uma saída
perigosa é descartada integralmente; o sistema não tenta editar fragmentos
clínicos potencialmente inseguros.

## 8. Auditoria e explicabilidade

Eventos UTC append-only registram início, pausa, revisão, conclusão e falha, com
papel, latência, versões, ferramentas, fontes, flags, erros e recusas. Paciente e
thread são representados por hashes; pergunta e feedback livre não entram no
log.

`explain_state()` lista somente fatores observáveis: categorias do prontuário,
fontes, regras, decisões de segurança, revisão e limitações. Não há alegação de
expor raciocínio interno do modelo.

## 9. Avaliação

| Configuração | Casos | Aprovação integral |
|---|---:|---:|
| Baseline Ollama `qwen2.5:3b` | 12 | 8,33% |
| Base pareada `Qwen2.5-0.5B` | 12 | 0% |
| Adaptador fine-tuned | 12 | 0% |
| Solução completa com geração controlada | 10 | 100% dos contratos de controle |

Os 100% da última linha medem schema, rotas, revisão, flags, fontes, segurança e
auditoria com respostas controladas. Eles não medem correção clínica da LLM. A
única demonstração real fine-tuned + RAG teve saída rejeitada pelo schema e
fallback seguro.

A rubrica humana está preparada para correção, relevância, clareza, aderência,
utilidade, segurança e fontes. Nenhuma avaliação especializada foi realizada;
esse gate permanece pendente e nenhum resultado foi simulado.

## 10. Interface

A aplicação Streamlit possui modo controlado para vídeo e modo real experimental.
Ela exibe paciente, resposta, pendências, alertas, fontes, explicação, auditoria e
ID, além de formulário de revisão humana. O modo controlado usa componentes reais
e substitui apenas embedding e geração por fixtures determinísticas.

## 11. Qualidade e reprodutibilidade

A suíte final possui 73 testes, incluindo quatro jornadas end-to-end, e cobertura
global de 95,04%. Ruff, formatação, mypy estrito e validação de dados compõem o
gate `make check`. A CI GitHub Actions replica o gate em Python 3.12 sem modelos
externos ou GPU.

Comandos centrais:

```bash
make install
make data
make check
make ui
```

Treinamento e inferência real exigem `requirements-training.txt`, GPU compatível
e os artefatos locais documentados no README.

## 12. Limitações e riscos residuais

- adaptador reprovado e corpus instrucional pequeno;
- dados, protocolos e avaliações sintéticos;
- ausência de validação humana especializada;
- regras lexicais sujeitas a falsos positivos e negativos;
- checkpointer, auditoria e identidade sem garantias de produção;
- ausência de autenticação, autorização real e gestão de segredos;
- nenhuma validação clínica, regulatória ou de implantação hospitalar.

## 13. Conclusão

O trabalho cumpre o objetivo acadêmico de integrar fine-tuning, LangChain,
LangGraph, prontuário estruturado, RAG, human-in-the-loop, logging e interface. A
principal conclusão técnica é que controles externos conseguem conter várias
falhas, mas não transformam um adaptador fraco em um modelo clinicamente válido.

O protótipo está pronto para demonstração acadêmica. Ele não está aprovado para
uso clínico e só poderia avançar após ampliar e revisar o corpus, repetir o
treinamento, obter melhoria pareada, realizar avaliação humana qualificada e
substituir os componentes locais por infraestrutura segura de produção.
