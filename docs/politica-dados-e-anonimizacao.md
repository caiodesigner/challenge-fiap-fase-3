# Política de dados, anonimização e curadoria

## Regra principal

Na versão acadêmica atual, somente dados sintéticos podem entrar no repositório,
nos testes, nos logs e nas demonstrações.

## Dados proibidos

- Nome ou iniciais reais.
- CPF, RG, CNS, matrícula ou prontuário real.
- Telefone, e-mail e endereço.
- Identificadores reais de profissionais ou instituições.
- Datas ou eventos que possibilitem reidentificação.
- Texto copiado de prontuário real e metadados ocultos de arquivos.

## Processo para qualquer futura importação

1. Registrar origem, autorização e finalidade.
2. Manter a fonte fora do repositório publicável.
3. Remover identificadores diretos.
4. Generalizar ou deslocar quasi-identificadores.
5. Examinar campos estruturados e texto livre.
6. Executar revisão independente e avaliar reidentificação.
7. Publicar somente após aprovação documentada.

Sem autorização e revisão, a importação deve falhar de forma fechada.

## Curadoria

- Validar schemas e campos obrigatórios.
- Deduplicar IDs e conteúdo.
- Normalizar terminologia e datas.
- Versionar documentos e identificar conflitos.
- Exigir fonte nos exemplos instrucionais.
- Revisar respostas potencialmente prescritivas.
- Registrar seed, versão, transformações e contagens.

## Prevenção de vazamento

A separação ocorre por `group_id`: paciente em casos de prontuário e documento
em conhecimento institucional. Variações do mesmo caso não cruzam splits.

O scanner implementado é uma barreira adicional; ele não certifica anonimização
nem autoriza a publicação de dados reais.

