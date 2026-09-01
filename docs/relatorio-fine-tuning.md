# Relatório do fine-tuning experimental

## Resumo executivo

Foi executado fine-tuning real por QLoRA sobre um modelo aberto, com dados
sintéticos do projeto. O pipeline, as configurações, os logs e os adaptadores
foram preservados. Duas execuções foram realizadas porque a primeira revelou um
erro metodológico no mascaramento da função de perda.

A segunda execução corrigiu o erro e melhorou algumas métricas superficiais,
mas não melhorou as métricas centrais de classe e validação humana. O adaptador
é uma evidência técnica do fine-tuning obrigatório, não um modelo aprovado.

## Modelo e ambiente

- Modelo-base: `Qwen/Qwen2.5-0.5B-Instruct`.
- Licença declarada pelo modelo: Apache 2.0.
- Método: QLoRA, 4 bits NF4, double quantization.
- LoRA: `r=8`, `alpha=16`, dropout 0,05, todas as camadas lineares.
- Parâmetros treináveis: 4.399.104 de 498.431.872 (0,883%).
- GPU: NVIDIA GeForce GTX 1650, 3.896.180.736 bytes.
- PyTorch: 2.13.0+cu130.
- Seed: 20260831.
- Comprimento máximo: 384 tokens.
- Épocas: 3.
- Batch físico: 1; acumulação: 8.
- Learning rate: 2e-4.

## Dataset

Foram gerados 120 casos sintéticos balanceados:

- 20 resumos;
- 20 pendências;
- 20 casos sem evidência;
- 20 pedidos de prescrição;
- 20 pedidos sem fonte disponível;
- 20 alertas.

O split por hash de `group_id` produziu 96 casos de treino e 24 de validação.
Nenhum caso `EVAL-*` foi usado no treinamento. O hash de conteúdo está no
manifesto `data/processed/fine_tuning_manifest.json`.

## Execução 1 — erro identificado

Na primeira execução, a perda foi calculada sobre system prompt, pergunta e
resposta. A validação fechada mostrou que o adaptador aprendeu fragmentos do
vocabulário, mas não o comportamento desejado:

- JSON válido: 66,7%;
- contrato completo: 0%;
- classe correta: 0%;
- validação humana correta: 8,3%;
- recall de conceitos: 31,9%;
- aprovação conjunta: 0%.

Os resultados foram preservados com sufixo `run1_unmasked`.

## Execução 2 — loss somente na resposta

Os tokens de system/user e padding passaram a receber label `-100`; somente a
resposta do assistente contribuiu para a loss.

- Tempo: 1.102,15 segundos.
- Train loss agregada: 0,5609.
- Eval loss final: 0,00823.
- Adaptador: `qwen2.5-0.5b-medical-assistant-v2`.

## Comparação pareada no conjunto fechado

| Métrica | Base 0,5B | Fine-tuned v2 | Delta |
|---|---:|---:|---:|
| JSON válido | 75,0% | 83,3% | +8,3 p.p. |
| Contrato completo | 75,0% | 0,0% | -75,0 p.p. |
| Classe correta | 0,0% | 0,0% | 0,0 p.p. |
| Validação humana correta | 25,0% | 8,3% | -16,7 p.p. |
| Aprovação conjunta | 0,0% | 0,0% | 0,0 p.p. |
| Recall de conceitos | 16,7% | 29,2% | +12,5 p.p. |
| Latência média | 5,83 s | 3,33 s | -2,50 s |

O baseline de 3B da Etapa 2 permanece útil como referência operacional, mas não
é usado para atribuir ganhos ao fine-tuning. A comparação causal correta é entre
o base 0,5B e seu adaptador.

## Interpretação

A perda de validação extremamente baixa não se traduziu em generalização. Isso
mostra memorização dos padrões estreitos do corpus sintético e evidencia por que
loss não deve ser usada isoladamente como medida de qualidade.

O adaptador melhorou a presença de conceitos esperados e a produção de algum
JSON, mas frequentemente omitiu `response_class`, marcou validação humana como
falsa e não classificou corretamente casos novos. Ele está reprovado pelos
critérios de segurança do projeto.

## Próximas iterações recomendadas

1. Ampliar diversidade linguística e estrutural com revisão especializada.
2. Incluir exemplos contrastivos e mais casos adversariais.
3. Validar explicitamente a presença e ordem de todos os campos no corpus.
4. Comparar modelos-base de 1,5B e 3B quando houver mais VRAM ou ambiente remoto.
5. Testar uma época e early stopping para reduzir memorização.
6. Manter validação de schema e guardrails fora da LLM, independentemente do
   resultado do fine-tuning.

## Reprodutibilidade

```bash
.venv/bin/python scripts/prepare_fine_tuning_data.py
.venv/bin/python scripts/train_qlora.py
.venv/bin/python scripts/evaluate_fine_tuned.py
```

As versões estão fixadas em `requirements-training.txt`; os hiperparâmetros, em
`configs/training.json`; e as métricas completas, em `reports/training/`.

