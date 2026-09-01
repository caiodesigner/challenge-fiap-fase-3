# Model card — adaptador experimental FIAP

## Identificação

- Base: `Qwen/Qwen2.5-0.5B-Instruct` (Apache 2.0).
- Método: QLoRA 4-bit NF4.
- Dados: 120 exemplos integralmente sintéticos.
- Finalidade: demonstração acadêmica do Tech Challenge Fase 3.

## Uso permitido

Reprodução do experimento, estudo de PEFT e demonstração acadêmica offline.

## Uso proibido

Diagnóstico, prescrição, triagem, decisão clínica, atendimento real ou qualquer
tratamento de dados pessoais reais.

## Resultado

O adaptador não passou nos critérios de classe, contrato de saída e validação
humana. Ele não é um modelo aprovado e deve permanecer atrás de validação de
schema, regras determinísticas e revisão humana.

Consulte `docs/relatorio-fine-tuning.md` para métricas e análise completa.

