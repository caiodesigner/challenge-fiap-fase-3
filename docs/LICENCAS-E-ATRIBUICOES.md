# Licenças e atribuições

## Código deste projeto

Protótipo acadêmico desenvolvido para o Tech Challenge FIAP. O campo de licença
do pacote está definido como `Proprietary`; redistribuição pública deve ser
decidida pelos autores antes da entrega.

## Modelos

| Componente | Identificador | Licença declarada pelo fornecedor |
|---|---|---|
| Modelo-base do fine-tuning | `Qwen/Qwen2.5-0.5B-Instruct` | Apache-2.0 |
| Embedding | `intfloat/multilingual-e5-small` | MIT |
| Baseline via Ollama | `qwen2.5:3b` | verificar os termos do artefato Ollama distribuído |

O adaptador LoRA é uma modificação treinada sobre o Qwen e não altera as
obrigações da licença do modelo-base. O projeto não redistribui os pesos-base.

## Bibliotecas principais

| Biblioteca | Licença declarada |
|---|---|
| LangGraph | MIT |
| LangChain Core | MIT |
| Streamlit | Apache-2.0 |
| Pydantic | MIT |
| PyTorch | BSD-3-Clause |
| Transformers | Apache-2.0 |
| PEFT | Apache-2.0 |

As dependências transitivas mantêm suas próprias licenças. Antes de qualquer
distribuição fora do contexto acadêmico, deve-se gerar um inventário completo do
ambiente instalado e revisar compatibilidade e avisos de copyright.

## Dados

Pacientes, protocolos, templates e exemplos instrucionais deste repositório são
sintéticos. Não há autorização para tratá-los como conteúdo clínico validado.
