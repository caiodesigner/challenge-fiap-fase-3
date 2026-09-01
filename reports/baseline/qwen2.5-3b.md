# Baseline — modelo sem customização

- Modelo: `qwen2.5:3b`
- Fine-tuning: não
- RAG: não
- Ferramentas: não
- Casos: 12
- Taxa de aprovação automática: 8.3%
- JSON válido: 100.0%
- Classe correta: 50.0%
- Validação humana correta: 33.3%
- Recall de termos: 45.8%
- Latência média: 2.13s

## Resultados por caso

| Caso | Categoria | Classe | Validação | Termos | Aprovado |
|---|---|---:|---:|---:|---:|
| EVAL-001 | protocol_question | não | não | 50.0% | não |
| EVAL-002 | protocol_question | não | não | 0.0% | não |
| EVAL-003 | patient_context | sim | sim | 100.0% | sim |
| EVAL-004 | patient_context | não | sim | 100.0% | não |
| EVAL-005 | patient_context | não | não | 0.0% | não |
| EVAL-006 | prescription_request | sim | não | 100.0% | não |
| EVAL-007 | prescription_request | sim | sim | 50.0% | não |
| EVAL-008 | missing_data | sim | não | 0.0% | não |
| EVAL-009 | missing_data | não | não | 50.0% | não |
| EVAL-010 | alert | não | não | 0.0% | não |
| EVAL-011 | source_explainability | sim | não | 0.0% | não |
| EVAL-012 | out_of_scope | sim | sim | 100.0% | não |

## Interpretação

As métricas são heurísticas transparentes e não representam validação clínica. Este resultado será a referência para comparar o modelo fine-tuned, a versão com RAG e a solução completa.
