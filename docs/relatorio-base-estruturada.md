# Relatório da Etapa 5 — Base estruturada e ferramentas

## Objetivo

Disponibilizar contexto atualizado de pacientes sintéticos sem conceder à LLM
acesso direto ao banco ou capacidade de gerar SQL. A camada foi construída com
SQLite e biblioteca padrão do Python.

## Modelo de dados

O schema versionado contém:

- pacientes;
- condições;
- alergias;
- medicamentos;
- exames concluídos e pendentes;
- atendimentos;
- alertas propostos, reservados para etapas futuras;
- metadados de schema e dataset.

Restrições `CHECK`, chaves estrangeiras e índices protegem as invariantes
básicas. Todos os pacientes possuem identificadores `PAT-SYN-*` e a coluna
`synthetic=1` é obrigatória.

## Construção

O script `build_clinical_database.py` transforma deterministicamente
`data/synthetic/patients.json` usando `data/database/schema.sql`. Ele:

1. recusa pacientes sem `synthetic=true`;
2. cria um banco novo sem sobrescrever arquivo existente;
3. executa toda a carga em transação;
4. verifica chaves estrangeiras;
5. remove apenas o arquivo recém-criado se a transação falhar;
6. registra versão, quantidade e SHA-256.

O banco materializado contém 12 pacientes e tem schema `1.0.0`. O arquivo é
ignorado pelo Git para evitar versionar binários; sua reconstrução é feita pelos
artefatos textuais.

## Segurança do acesso

O `ClinicalRepository` abre SQLite com `mode=ro` e `PRAGMA query_only=ON`. Todas
as consultas são constantes e parametrizadas. Identificadores obedecem a um
formato estrito e limites numéricos são validados.

Não existe ferramenta `executar_sql`. Tentativas de invocar ferramenta, campo ou
argumento não autorizado são recusadas antes de chegar ao repositório.

## Ferramentas permitidas

| Ferramenta | Dados retornados |
|---|---|
| `buscar_resumo_paciente` | ID sintético, idade, condições e última revisão |
| `listar_exames_pendentes` | código, solicitação e status |
| `buscar_resultados_recentes` | código, conclusão e resumo sintético |
| `listar_alergias` | substâncias registradas |
| `listar_medicamentos_ativos` | rótulos registrados |

Cada ferramenta aplica minimização por finalidade; nenhuma retorna o prontuário
completo. O registro de alertas não foi exposto porque o acesso do protótipo é
deliberadamente somente leitura.

## Evidência de funcionamento

Para `PAT-SYN-003`, a demonstração recuperou condições `DM2` e `HAS`, exame
pendente `EX-REVISAO-B` e resultado sintético de `EX-PRESSAO`. Nenhum nome,
contato, endereço ou identificador real existe no resultado.

## Limitações

- A base é pequena e inteiramente artificial.
- Resultados não contêm valores clínicos reais.
- A base é consultada pela LangChain por meio das ferramentas permitidas.
- Escritas e transições de alertas permanecem fora do escopo do protótipo.
