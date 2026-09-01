# Data card — corpus sintético da Etapa 1

Todo o conteúdo foi criado programaticamente para este projeto. Ele não
representa pacientes, protocolos ou instituições reais e seu uso clínico é
proibido.

## Conteúdo

| Arquivo | Conteúdo |
|---|---|
| `synthetic/metadata.json` | versão, seed e restrições |
| `synthetic/protocols.json` | protocolos fictícios |
| `synthetic/document_templates.json` | laudo, receita não operacional e procedimento |
| `synthetic/patients.json` | prontuários artificiais mínimos |
| `synthetic/instruction_examples.jsonl` | FAQs e casos instrucionais |
| `splits/{train,validation,test}.jsonl` | exemplos separados para modelagem |
| `splits/manifest.json` | estratégia, atribuições e contagens |
| `schemas/*.schema.json` | contratos formais |
| `processed/fine_tuning_*.jsonl` | 120 casos balanceados para QLoRA |
| `processed/fine_tuning_manifest.json` | versão, hash e contagens do fine-tuning |

## Geração e validação

```bash
PYTHONPATH=src python3 scripts/generate_synthetic_data.py
PYTHONPATH=src python3 scripts/validate_data.py
```

A seed `20260831` e a versão são registradas em `metadata.json`. Execuções
repetidas produzem conteúdo idêntico.

## Curadoria

- IDs artificiais explícitos.
- Campos identificadores proibidos.
- Detecção de CPF, telefone e e-mail no conteúdo publicável.
- IDs únicos e fontes em todos os exemplos.
- Vocabulário limitado ao escopo HAS/DM2.
- Respostas com limites e validação humana.
- Receita somente como estrutura não operacional.

## Divisão e prevenção de vazamento

O split usa hash SHA-256 determinístico de `seed + group_id`, com alvo 70/20/10.
O isolamento ocorre por paciente ou documento: variações do mesmo grupo não
cruzam splits. Em um corpus pequeno, a proporção observada pode diferir do alvo;
o isolamento tem prioridade. O teste fica fechado durante ajuste e seleção.

## Limitações

- Corpus inicial pequeno, voltado à validação do pipeline.
- Conteúdo sem validade clínica.
- O scanner não certifica anonimização de dados reais.
- Antes do fine-tuning, o corpus deverá ser ampliado e revisado por especialista.
- A ampliação inicial para 120 casos viabilizou o experimento, mas continua
  insuficiente para aprovação clínica ou de segurança.
