# Assistente Médico — Tech Challenge Fase 3

Protótipo acadêmico de apoio à decisão para o acompanhamento de adultos
sintéticos com hipertensão arterial sistêmica e diabetes mellitus tipo 2.

> Este projeto não é um dispositivo médico, não utiliza dados reais e não pode
> ser usado para diagnóstico, prescrição ou atendimento clínico.

## Estado atual

- Etapa 0: escopo e critérios concluídos.
- Etapa 1: pipeline determinístico de dados sintéticos concluído.
- Etapa 2: baseline do modelo-base concluído.
- Etapa 3: pipeline e duas execuções de QLoRA concluídos; adaptador experimental
  não aprovado para uso por falhas na avaliação fechada.
- Etapa 4: RAG de protocolos e avaliação de recuperação concluídos.
- Etapa 5: prontuários estruturados e ferramentas restritas concluídos.
- Etapa 6: pipeline LangChain integrada e validada concluída.
- Etapa 7: orquestração LangGraph e human-in-the-loop concluídos.
- Etapa 8: segurança determinística e validação adversarial concluídas.
- Etapa 9: auditoria estruturada e explicabilidade concluídas.
- Etapa 10: avaliação automatizada e comparação crítica concluídas; avaliação
  humana especializada permanece pendente.
- Etapa 11: testes end-to-end e pipeline de qualidade/CI concluídos.
- Etapa 12: interface Streamlit de demonstração concluída.
- Etapa 13: documentação técnica e pacote de entrega concluídos; vídeo e revisão
  humana dependem de execução manual pelos autores.

Consulte o [plano mestre](PLANO_DESENVOLVIMENTO.md), a
[especificação da Etapa 0](docs/etapa-0-especificacao.md) e o
[data card](data/README.md).

## Preparação local

Requer Python 3.12.

```bash
make install
make data
make check
```

Também é possível gerar e validar os dados somente com a biblioteca padrão:

```bash
PYTHONPATH=src python3 scripts/generate_synthetic_data.py
PYTHONPATH=src python3 scripts/validate_data.py
```

Com o Ollama ativo e `qwen2.5:3b` instalado, o baseline pode ser reproduzido:

```bash
PYTHONPATH=src python3 scripts/run_baseline.py
```

## Fine-tuning experimental

```bash
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python scripts/prepare_fine_tuning_data.py
.venv/bin/python scripts/train_qlora.py
.venv/bin/python scripts/evaluate_fine_tuned.py
```

O adaptador final está em
`artifacts/adapters/qwen2.5-0.5b-medical-assistant-v2`. Ele demonstra o pipeline
obrigatório, mas não atingiu os critérios de segurança e não deve ser usado como
modelo aprovado. Consulte `docs/relatorio-fine-tuning.md`.

## Índice de protocolos

```bash
.venv/bin/python scripts/build_retrieval_index.py
.venv/bin/python scripts/evaluate_retrieval.py
```

O índice usa `intfloat/multilingual-e5-small`, filtros de vigência/especialidade
e citações no formato `documento#seção`. O limiar de ausência de evidência foi
calibrado para o corpus atual e deve ser recalibrado após qualquer ampliação.

## Base clínica sintética

```bash
.venv/bin/python scripts/build_clinical_database.py
.venv/bin/python scripts/demo_clinical_tools.py
```

O construtor não sobrescreve um banco existente. O arquivo `.db` é reproduzível
e ignorado pelo Git; o schema SQL, os dados de origem e o relatório de construção
são versionáveis. O acesso de runtime é somente leitura e não expõe SQL à LLM.

## Chain integrada

```bash
.venv/bin/python scripts/demo_langchain.py
```

A chain integra o prontuário mínimo, o índice E5 e o adaptador QLoRA. Toda saída
é validada por schema; falhas de modelo, banco, recuperação ou parsing retornam
uma resposta segura com baixa confiança e validação humana obrigatória.

## Grafo clínico e revisão humana

```bash
.venv/bin/python scripts/demo_langgraph.py
```

O grafo mantém estado por `thread_id`, cria checkpoints e interrompe respostas
sensíveis até receber uma decisão humana explícita. Pedidos de prescrição/dose e
termos associados a possível urgência são desviados antes da LLM. A demonstração
pausa um pedido proibido, retoma o mesmo checkpoint com uma rejeição e grava a
evidência em `reports/graph/langgraph_demo.json`. Consulte também
`docs/relatorio-langgraph.md`.

## Segurança e validação adversarial

```bash
.venv/bin/python scripts/demo_safety.py
```

A política `safety-v1` bloqueia prompt injection, escrita em prontuário e
populações fora do escopo antes da LLM. Depois da geração, rejeita doses
operacionais, fontes inválidas, duplicadas ou não vigentes, informação sem fonte
e classes sensíveis sem validação humana. Consulte
`docs/relatorio-seguranca.md`.

## Auditoria e explicabilidade

```bash
.venv/bin/python scripts/demo_audit.py
```

Cada execução possui um `execution_id` preservado entre pausa e retomada. A
trilha JSONL registra versões, decisões, regras, fontes, latência e erros sem
armazenar pergunta, feedback ou identificadores brutos. A explicação é derivada
do estado e lista somente fatores observáveis. Consulte
`docs/relatorio-auditoria-explicabilidade.md`.

## Avaliação consolidada

```bash
.venv/bin/python scripts/evaluate_complete_solution.py
```

A avaliação consolida baseline, modelo-base pareado, adaptador, RAG e os
controles da solução completa. O adaptador permanece reprovado; os 100% obtidos
pela solução completa referem-se a controles pós-geração com respostas
controladas, não à qualidade clínica da LLM. A rubrica humana está preparada,
mas ainda não foi aplicada por revisores qualificados. Consulte
`docs/relatorio-avaliacao-final.md`.

## Testes e qualidade

```bash
make test-e2e
make check
```

O alvo `test-e2e` mede somente essa fatia e, por isso, não aplica isoladamente o
piso global de cobertura. O limite de 90% é verificado por `make check` e pela CI
com todos os testes.

A suíte end-to-end atravessa SQLite, ferramentas, RAG, LangChain, LangGraph,
segurança, revisão e auditoria sem baixar modelos. O workflow em
`.github/workflows/ci.yml` executa lint, formatação, mypy, cobertura e validação
dos dados em Python 3.12. Consulte `docs/relatorio-testes-qualidade.md`.

## Interface de demonstração

```bash
make ui
```

Abra `http://localhost:8501`. O modo controlado é rápido e usa todos os
componentes reais, exceto embedding e geração, que são determinísticos. O modo
real experimental carrega E5 e o adaptador reprovado e exige as dependências de
treinamento e hardware compatível. Consulte `docs/relatorio-interface.md`.

## Relatório e entrega

```bash
make report
```

O relatório fonte está em `docs/relatorio-tecnico-final.md` e o PDF gerado em
`reports/deliverables/relatorio-tecnico-final.pdf`. A entrega também possui:

- diagramas em `docs/diagrams/`;
- matriz em `docs/matriz-rastreabilidade-final.md`;
- roteiro de 15 minutos em `docs/roteiro-video.md`;
- checklist em `docs/checklist-entrega.md`;
- licenças em `docs/LICENCAS-E-ATRIBUICOES.md`.

## Estrutura principal

```text
app.py                         interface Streamlit
configs/                       versões e parâmetros
data/                          corpus e pacientes sintéticos
src/assistente_medico/         código modular
tests/                         unidades, integração e E2E
scripts/                       pipelines e demonstrações
reports/                       métricas e evidências preservadas
docs/                          relatórios, diagramas e entrega
artifacts/adapters/            adaptadores experimentais
```

## Limitações conhecidas

- O adaptador fine-tuned está reprovado.
- A avaliação humana especializada está pendente.
- O corpus e os protocolos são pequenos e sintéticos.
- Checkpoint, auditoria e autenticação não possuem garantias de produção.
- Nenhum resultado constitui validação clínica.

Consulte [licenças e atribuições](docs/LICENCAS-E-ATRIBUICOES.md) antes de
redistribuir código, modelos ou artefatos. Comandos de runtime podem escrever
somente nas pastas documentadas de dados, relatórios e `outputs/` deste projeto.
