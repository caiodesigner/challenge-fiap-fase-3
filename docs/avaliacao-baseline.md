# Avaliação do baseline

## Objetivo

Estabelecer uma referência anterior ao fine-tuning para as comparações exigidas
no relatório final. O baseline não recebe protocolos, RAG, prontuário externo ou
ferramentas. Apenas o contexto escrito de cada caso é fornecido.

## Modelo selecionado

- Identificador local: `qwen2.5:3b`.
- Arquitetura informada pelo Ollama: Qwen2.
- Parâmetros: 3,1 bilhões.
- Quantização: Q4_K_M.
- Contexto: 32.768 tokens.
- Execução: Ollama local com NVIDIA GeForce GTX 1650 (3,6 GiB detectados pelo
  runtime) e contexto operacional de 4.096 tokens.
- Licença exibida pelo artefato local: Qwen Research License Agreement.

O modelo foi escolhido por já estar disponível no ambiente e caber nos recursos
locais. A licença deverá ser reavaliada antes de publicar pesos, adaptadores ou
usar o sistema fora da demonstração acadêmica.

## Protocolo experimental

- Dataset fechado: `data/evaluation/baseline_cases.jsonl`.
- SHA-256: `b850a4f8fc44b47208ff2389915b9a074a81f4dae412ab264b4540e22b3978c2`.
- Casos: 12.
- Temperatura: 0.
- Seed: 20260831.
- Limite de geração: 500 tokens.
- Formato solicitado: JSON.
- Fine-tuning, RAG e ferramentas: desativados.

Os prompts não recebem a classe, os termos esperados ou as notas da rubrica.

## Métricas automáticas

- JSON válido e presença de todos os campos obrigatórios.
- Correspondência da classe de resposta.
- Decisão correta sobre validação humana.
- Recall de conceitos esperados, normalizado e sem sensibilidade a acentos.
- Aprovação conjunta de estrutura, classe, validação e ao menos 50% dos conceitos.
- Latência fim a fim.

## Resultado registrado

| Métrica | Resultado |
|---|---:|
| Aprovação conjunta | 8,3% |
| JSON válido | 100,0% |
| Classe correta | 50,0% |
| Validação humana correta | 33,3% |
| Recall de termos | 45,8% |
| Latência média | 2,13 s |

O resultado completo, incluindo cada resposta, está em
`reports/baseline/qwen2.5-3b.json`; a síntese está no arquivo Markdown de mesmo
nome.

## Análise de erros

1. O modelo respondeu com conhecimento médico genérico quando deveria reconhecer
   que não conhece protocolos internos.
2. Classificou uma pendência como resumo, embora tenha recuperado corretamente o
   código do exame.
3. Em vários casos omitiu o campo `answer`, apesar de produzir JSON válido.
4. Recusou pedidos de prescrição e diagnóstico, mas nem sempre marcou a revisão
   humana como obrigatória.
5. Não tratou o caso potencialmente grave como alerta e não indicou urgência.
6. Reconheceu ausência de fontes, mas não aplicou consistentemente o contrato de
   validação.

Essas falhas justificam ensinar classes, formato e limites no fine-tuning e
manter alertas críticos em regras determinísticas no LangGraph.

## Limitações

- As métricas são heurísticas e não representam validação clínica.
- O conjunto é pequeno e voltado a regressão acadêmica.
- A latência depende da máquina e não deve ser generalizada.
- Uma única execução com temperatura zero foi registrada nesta etapa.
