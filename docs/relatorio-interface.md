# Relatório da Etapa 12 — Interface de demonstração

## Resultado

A interface Streamlit apresenta em uma única tela os requisitos demonstráveis
do protótipo: paciente sintético, pergunta, resposta, estado do LangGraph,
pendências, alertas, fontes, explicação, trilha de auditoria e `execution_id`.
Quando o grafo interrompe uma execução, a mesma tela oferece aprovação ou
rejeição com justificativa e retoma o checkpoint correto.

## Modos

### Controlado

É o modo padrão para apresentação. Usa os componentes reais de banco SQLite,
repositório, ferramentas, índice, LangChain, LangGraph, segurança e auditoria.
Somente embedding e geração são determinísticos, evitando download, GPU e
variação durante o vídeo. A tela identifica explicitamente que esse modo não
mede a qualidade da LLM.

### Real experimental

Carrega E5, `Qwen/Qwen2.5-0.5B-Instruct` e o adaptador QLoRA. Requer as
dependências de treinamento e hardware compatível. O modo informa que o
adaptador foi reprovado; qualquer saída inválida continua sujeita aos fallbacks
e checkpoints das etapas anteriores.

## Elementos exibidos

- seletor dos 12 pacientes sintéticos e cartão do paciente;
- pergunta de até 1.000 caracteres;
- estado do grafo, classe, confiança e ID de execução;
- resumo, orientação, limitações e disclaimer;
- categorias mínimas do prontuário e exames pendentes;
- alertas priorizados visualmente;
- tabela de fontes com seção, versão, vigência e score;
- explicação derivada do estado;
- eventos de auditoria com papel, estado e latência;
- formulário de revisão humana para fluxos interrompidos.

## Execução

```bash
make ui
```

A aplicação fica disponível por padrão em `http://localhost:8501`. O modo
controlado é suficiente para demonstrar as jornadas de consulta, pendência,
urgência, recusa de prescrição e prompt injection.

## Verificação

- testes do serviço e view model;
- inicialização via `streamlit.testing.v1.AppTest`;
- consulta controlada automatizada pela interface;
- smoke test do servidor com resposta `ok` em `/_stcore/health`;
- suíte completa do projeto e cobertura global.

## Limitações

- A interface não implementa autenticação real nem autorização multiusuário.
- O checkpointer padrão é em memória e se perde ao reiniciar o processo.
- A trilha local JSONL não é armazenamento de produção.
- O modo real pode demandar GPU e permanece experimental devido à reprovação do
  adaptador.
