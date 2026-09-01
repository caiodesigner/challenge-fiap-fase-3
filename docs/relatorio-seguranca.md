# Relatório da Etapa 8 — Segurança e validação

## Resultado

A Etapa 8 adiciona uma política determinística, independente da LLM, em dois
pontos do LangGraph: antes do processamento da solicitação e depois da geração
da resposta. A configuração e a versão da política estão registradas em
`configs/safety.json`.

O comportamento padrão é fail-closed. Entradas bloqueadas não chegam à chain;
saídas inseguras são descartadas e substituídas por uma recusa estruturada de
baixa confiança.

## Controles implementados

| Controle | Comportamento seguro |
|---|---|
| Prompt injection | Bloqueia antes da LLM e retorna recusa |
| Alteração de prontuário | Bloqueia comandos de escrita |
| População fora do escopo | Recusa pediatria e gestação no MVP |
| Prescrição/dose na entrada | Regra determinística do grafo e revisão humana |
| Prescrição/dose na saída | Descarta a saída e solicita revisão |
| Paciente inexistente | Chain não chama a LLM e retorna evidência insuficiente |
| SQL/ferramenta não autorizada | Allowlist rejeita ferramenta ou argumento |
| Fonte inválida/duplicada | Descarta a saída |
| Fonte ainda não vigente | RAG não recupera e validador rejeita citação |
| Informação sem fonte | Descarta afirmação institucional não fundamentada |
| Classe sensível sem revisão | Obriga validação humana |

## Limites e decisões

- As regras são uma defesa adicional, não uma validação clínica.
- Detecção por termos possui falsos positivos e negativos; a Etapa 10 medirá o
  comportamento em um conjunto adversarial maior.
- A política não tenta higienizar uma saída perigosa. Ela descarta integralmente
  a orientação original para evitar que fragmentos operacionais sejam expostos.
- Autorização real, identidade do usuário, rate limiting e gestão de segredos são
  controles de implantação e não são simulados como segurança de produção.
- O protótipo continua restrito a dados sintéticos e ferramentas somente leitura.

## Evidência

`scripts/demo_safety.py` executa dois cenários: uma prompt injection bloqueada
antes da chain e uma saída propositalmente contendo dose. No segundo caso, a
saída é substituída, a dose não aparece na orientação liberada e o grafo pausa
para revisão humana. O resultado fica em
`reports/safety/adversarial_demo.json`.
