# Relatório da Etapa 11 — Testes e qualidade

## Estratégia

A pirâmide de testes possui unidades para dados, schemas, repositório, RAG,
ferramentas, segurança, auditoria e métricas; testes de integração para a chain e
o grafo; e uma suíte end-to-end offline marcada como `e2e`.

Os testes offline são o gate obrigatório da CI. Treinamento, inferência real com
GPU e download do embedding são processos pesados e permanecem como avaliações
reproduzíveis separadas, com seus artefatos preservados.

## Cenários end-to-end

1. Consulta de exames pendentes atravessa SQLite somente leitura, ferramentas
   allowlisted, índice de protocolos, LangChain, parser, segurança, LangGraph,
   explicabilidade e auditoria JSONL.
2. Uma dose produzida pelo modelo controlado é descartada, pausa para revisão e
   termina em rejeição humana.
3. Paciente inexistente e timeout do modelo encerram em fail-closed, sem inventar
   dados.
4. Possível urgência é detectada antes de qualquer dependência gerativa.

As fixtures substituem somente embedding e geração por implementações
determinísticas. Banco, repositório, ferramentas, RAG, chain, grafo, política e
auditoria são os componentes reais do projeto.

## Pipeline de CI

`.github/workflows/ci.yml` executa em Python 3.12:

- instalação limpa do pacote e dependências de desenvolvimento;
- Ruff lint e verificação de formatação;
- mypy estrito;
- todos os testes com cobertura de branches e piso de 90%;
- validação do dataset sintético;
- publicação do `coverage.xml` como artefato.

O token da CI recebe somente permissão de leitura de conteúdo. O workflow não
usa segredos, modelos externos nem serviços clínicos.

## Comandos locais

```bash
make test-e2e
make check
```

`make test-e2e` preserva o relatório da fatia executada, mas desativa o piso
global de cobertura porque os demais testes são intencionalmente desmarcados.
O gate de 90% continua obrigatório em `make check` e na CI, que executam a suíte
completa.

## Limitações

- A pasta ainda não possui metadados Git, portanto o workflow está configurado,
  mas somente será executado remotamente após o projeto ser versionado e enviado
  ao GitHub.
- A CI não prova compatibilidade com GPU nem reproduz o fine-tuning.
- Testes automatizados e dados sintéticos não substituem a revisão humana
  qualificada ainda pendente.
