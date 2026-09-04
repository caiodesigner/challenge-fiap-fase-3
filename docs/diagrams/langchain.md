# Diagrama do fluxo LangChain

```mermaid
flowchart TD
    REQ[AssistantRequest validado] --> VALIDATE[validate_request]
    VALIDATE --> ENRICH[retrieve_context]
    ENRICH --> TOOLS[Ferramentas clínicas allowlisted]
    TOOLS --> DB[(SQLite sintético somente leitura)]
    ENRICH --> RAG[Retriever E5]
    RAG --> INDEX[(Índice de protocolos versionados)]
    DB --> PROMPT[Prompt com contexto mínimo do paciente]
    INDEX --> PROMPT
    PROMPT --> LLM[Qwen + adaptador QLoRA]
    LLM --> PARSE[validate_structured_response]
    PARSE --> POLICY[Schema, citações e política de segurança]
    POLICY -->|válida| RESPONSE[AssistantResponse estruturada]
    POLICY -->|erro ou evidência insuficiente| FALLBACK[Fallback fail-closed]
    FALLBACK --> RESPONSE
```

O pipeline é implementado como uma `RunnableSequence`. As consultas clínicas são
restritas a ferramentas permitidas, e as fontes finais são substituídas pelas
citações efetivamente retornadas pelo retriever.
