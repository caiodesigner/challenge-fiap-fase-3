# Relatório da Etapa 10 — Avaliação da solução

## Resumo executivo

A avaliação automatizada foi concluída, mas o sistema não está aprovado para uso
clínico. O adaptador QLoRA continua reprovado por não melhorar as métricas
centrais do conjunto pareado. Os controles determinísticos, RAG, LangGraph,
segurança e auditoria funcionaram nos conjuntos fechados do protótipo.

Os resultados não constituem validação clínica.

## Comparação gerativa histórica

| Configuração | Casos | JSON válido | Campos exigidos | Classe correta | Validação humana correta | Aprovação integral |
|---|---:|---:|---:|---:|---:|---:|
| Baseline Ollama `qwen2.5:3b` | 12 | 100,00% | 50,00% | 50,00% | 33,33% | 8,33% |
| Base pareada `Qwen2.5-0.5B` | 12 | 75,00% | 75,00% | 0,00% | 25,00% | 0,00% |
| Adaptador fine-tuned | 12 | 83,33% | 0,00% | 0,00% | 8,33% | 0,00% |

O fine-tuning aumentou JSON válido em 8,33 pontos percentuais e recall de termos
em 12,50 pontos, mas reduziu campos exigidos em 75 pontos e correspondência de
validação humana em 16,67 pontos. Essas regressões impedem a aprovação do
adaptador. A latência média caiu, mas velocidade não compensa falhas estruturais
e de segurança.

## Fine-tuned + RAG

Existe uma demonstração real dessa configuração, não uma avaliação agregada. A
saída do adaptador foi rejeitada pelo schema e convertida em fallback seguro com
validação humana. Portanto, ela é registrada como evidência de fail-closed, não
como melhora de qualidade. Uma taxa agregada não é apresentada porque isso seria
extrapolar um único caso.

## Recuperação

O RAG obteve Recall@3 = 100%, MRR = 100% e rejeição fora do escopo = 100% em nove
casos. O conjunto é pequeno, sintético e conhecido; as métricas devem ser
recalculadas quando o corpus crescer.

## Solução completa — controles pós-geração

Dez casos fechados cobriram prescrição, possível urgência, prompt injection,
escrita de prontuário, população fora do escopo, resposta fundamentada, exame
pendente, dose produzida pelo modelo, afirmação sem fonte e evidência insuficiente.

Todos atingiram os contratos esperados para schema, classe, revisão humana,
flags, roteamento do modelo, fontes, remoção de dose e auditoria. A latência média
da orquestração controlada foi aproximadamente 6 ms e o p95 aproximadamente 9 ms
na execução registrada.

Esse resultado usa respostas gerativas controladas para isolar os componentes
pós-geração. Ele não mede correção, relevância ou utilidade clínica da LLM e não
deve ser comparado diretamente com a latência das execuções reais do modelo.

## Decisão

- Adaptador fine-tuned: **reprovado**.
- RAG no corpus sintético atual: **aprovado para o protótipo**, sujeito a nova
  calibração quando os dados mudarem.
- Controles de orquestração e segurança: **aprovados para o protótipo** nos casos
  fechados.
- Solução para uso clínico: **não aprovada**.

Os dados completos, inclusive resultados por caso, estão em
`reports/evaluation/complete_evaluation.json`.
