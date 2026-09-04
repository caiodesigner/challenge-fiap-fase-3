# Relatório da Etapa 4 — Protocolos e RAG

## Objetivo

Recuperar seções de protocolos institucionais sintéticos com metadados
auditáveis, sem depender da memória da LLM. A camada não gera orientação; ela
entrega evidências que serão consumidas posteriormente por LangChain.

## Modelo de embeddings

- Modelo: `intfloat/multilingual-e5-small`.
- Licença declarada: MIT.
- Porte: aproximadamente 0,1B parâmetros.
- Dimensão: 384.
- Idiomas: modelo multilíngue.
- Pooling: média dos estados não mascarados.
- Normalização: L2.
- Prefixos: `passage:` na indexação e `query:` na consulta.
- Tamanho máximo: 512 tokens.

## Chunking

Foi adotado um chunk por seção porque cada seção sintética contém uma unidade
semântica curta. Cada chunk preserva:

- `source_id` no formato `protocol_id#section_id`;
- título e conteúdo;
- especialidade;
- versão;
- status;
- data de vigência.

Protocolos inativos, futuros ou de especialidade diferente são eliminados antes
do ranking. Duplicidade de `source_id` interrompe a construção.

## Armazenamento e busca

O índice auditável fica em `data/indexes/protocols-e5-small.json`. A busca usa
produto escalar exato sobre vetores normalizados, equivalente à similaridade de
cosseno. A implementação é local e não depende de serviço externo.

Cada resultado contém score, texto original e citação estruturada com documento,
seção, versão e vigência.

## Limiar de evidência

As seis consultas positivas tiveram score máximo entre 0,854 e 0,909. Três
consultas negativas — clima, automóvel e culinária — ficaram entre 0,814 e
0,832. Foi fixado provisoriamente o limiar `0,84`.

O valor é válido somente para esta combinação de corpus, modelo e consultas de
calibração. Ele deverá ser recalibrado sempre que o corpus ou embedder mudar.

Quando nenhum resultado supera o limiar, a camada retorna lista vazia. A chain
converte esse estado em `insufficient_evidence`, nunca em uma resposta
institucional sem fonte.

## Avaliação

| Métrica | Resultado |
|---|---:|
| Consultas positivas | 6 |
| Consultas negativas | 3 |
| Recall@3 | 100% |
| MRR | 1,0 |
| Rejeição fora do escopo | 100% |

Os resultados completos, incluindo ranking, score e citações, estão em
`reports/retrieval/evaluation.json`.

## Limitações

- O corpus possui apenas seis chunks e favorece métricas altas.
- Os negativos são poucos e foram usados para calibrar o limiar.
- Os protocolos são sintéticos e não possuem validade clínica.
- A recuperação semântica não garante que o conteúdo seja correto.
- O índice deve ser reconstruído após mudanças de conteúdo ou modelo.
- O retriever é integrado à LLM pela LangChain.

## Reprodução

```bash
.venv/bin/python scripts/build_retrieval_index.py
.venv/bin/python scripts/evaluate_retrieval.py
```
