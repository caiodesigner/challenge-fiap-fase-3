"""Interface Streamlit do protótipo acadêmico."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.ui import (  # noqa: E402
    build_controlled_workflow,
    build_real_workflow,
    build_view_model,
    load_synthetic_patients,
)

st.set_page_config(page_title="Assistente Médico FIAP", page_icon="🩺", layout="wide")


@st.cache_resource
def controlled_workflow():  # type: ignore[no-untyped-def]
    return build_controlled_workflow(PROJECT_ROOT)


@st.cache_resource
def real_workflow():  # type: ignore[no-untyped-def]
    return build_real_workflow(PROJECT_ROOT)


def render_result(workflow, state):  # type: ignore[no-untyped-def]
    view = build_view_model(dict(state))
    response = view["response"]
    st.subheader("Resultado")
    first, second, third = st.columns(3)
    first.metric("Estado do grafo", view["graph_status"])
    second.metric("Classe", response["response_class"] if response else "—")
    third.metric("Confiança", response["confidence"] if response else "—")
    st.caption(f"execution_id: {view['execution_id']}")

    if response:
        answer, context, alerts, sources, explanation, audit = st.tabs(
            ["Resposta", "Contexto", "Alertas", "Fontes", "Explicação", "Auditoria"]
        )
        with answer:
            st.write(response["summary"])
            st.info(response["guidance"])
            for limitation in response["limitations"]:
                st.warning(limitation)
            st.caption(response["disclaimer"])
        with context:
            st.write("Categorias consultadas:", response["patient_context_used"] or "—")
            st.dataframe(response["pending_exams"], use_container_width=True)
        with alerts:
            if response["alerts"]:
                for alert in response["alerts"]:
                    st.error(alert)
            else:
                st.success("Nenhum alerta registrado.")
        with sources:
            st.dataframe(response["sources"], use_container_width=True)
        with explanation:
            st.json(view["explanation"])
        with audit:
            events = workflow.audit_trail(str(view["execution_id"]))
            st.dataframe(
                [
                    {
                        "timestamp": event.timestamp,
                        "evento": event.event_type,
                        "papel": event.actor_role,
                        "estado": event.status,
                        "latência_ms": event.duration_ms,
                    }
                    for event in events
                ],
                use_container_width=True,
            )

    if view["awaiting_review"]:
        st.error("Execução pausada: uma decisão humana é obrigatória.")
        with st.form("human-review"):
            decision = st.radio("Decisão", ["approve", "reject"], horizontal=True)
            feedback = st.text_area("Justificativa")
            submitted = st.form_submit_button("Registrar revisão")
        if submitted:
            try:
                resumed = workflow.resume(
                    thread_id=st.session_state.thread_id,
                    decision=decision,
                    feedback=feedback,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state.result = resumed
                st.rerun()


st.title("🩺 Assistente Médico — Tech Challenge Fase 3")
st.warning(
    "Protótipo acadêmico com dados sintéticos. Não utilizar para diagnóstico, "
    "prescrição ou atendimento clínico."
)

patients = load_synthetic_patients(PROJECT_ROOT)
patient_by_id = {patient["patient_id"]: patient for patient in patients}

with st.sidebar:
    st.header("Configuração")
    mode = st.radio(
        "Modo",
        ["Controlado", "Real experimental"],
        help="O modo real carrega o adaptador reprovado e pode exigir GPU.",
    )
    patient_id = st.selectbox("Paciente sintético", ["Sem paciente", *patient_by_id])
    if patient_id != "Sem paciente":
        st.json(patient_by_id[patient_id])
    if mode == "Controlado":
        st.success("Rápido, determinístico e adequado à apresentação.")
    else:
        st.error("Adaptador reprovado; saídas podem ser rejeitadas pelo sistema.")

question = st.text_area(
    "Pergunta do profissional",
    value="Quais exames estão pendentes e quais fontes foram consultadas?",
    max_chars=1000,
)

if st.button("Executar consulta", type="primary"):
    workflow = controlled_workflow() if mode == "Controlado" else real_workflow()
    thread_id = str(uuid4())
    request = {
        "question": question,
        "patient_id": None if patient_id == "Sem paciente" else patient_id,
        "specialty": "clinica_medica",
        "requester_role": "professional",
    }
    with st.spinner("Executando o fluxo..."):
        st.session_state.result = workflow.invoke(request, thread_id=thread_id)
    st.session_state.thread_id = thread_id
    st.session_state.workflow_mode = mode

if "result" in st.session_state:
    active_workflow = (
        controlled_workflow()
        if st.session_state.workflow_mode == "Controlado"
        else real_workflow()
    )
    render_result(active_workflow, st.session_state.result)
