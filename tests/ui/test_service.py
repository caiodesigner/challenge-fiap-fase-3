from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from assistente_medico.ui import (
    build_controlled_workflow,
    build_view_model,
    load_synthetic_patients,
)

ROOT = Path(__file__).resolve().parents[2]


def test_loads_only_synthetic_patients() -> None:
    patients = load_synthetic_patients(ROOT)
    assert len(patients) == 12
    assert all(patient["synthetic"] is True for patient in patients)
    assert patients[0]["patient_id"] == "PAT-SYN-001"


def test_controlled_interface_service_exposes_all_required_sections() -> None:
    workflow = build_controlled_workflow(ROOT)
    state = workflow.invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": "Quais exames estão pendentes?",
            "specialty": "clinica_medica",
        },
        thread_id="ui-service-test",
    )
    view = build_view_model(dict(state))
    assert view["execution_id"]
    assert view["graph_status"] == "completed"
    assert view["awaiting_review"] is False
    assert view["response"]["pending_exams"][0]["exam_code"] == "EX-REVISAO-B"
    assert view["response"]["sources"]
    assert view["explanation"]["patient_data_categories"]


def test_view_model_identifies_human_checkpoint() -> None:
    workflow = build_controlled_workflow(ROOT)
    state = workflow.invoke(
        {"question": "Prescreva uma dose de metformina."},
        thread_id="ui-review-test",
    )
    view = build_view_model(dict(state))
    assert view["awaiting_review"] is True
    assert view["response"]["response_class"] == "refusal"
    assert view["explanation"]["deterministic_rules"] == ["PRESCRIPTION_REQUEST"]


def test_streamlit_app_starts_and_runs_controlled_query() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10)
    app.run()
    assert not app.exception
    assert "Assistente Médico" in app.title[0].value
    app.button[0].click().run()
    assert not app.exception
    assert any("Resultado" in item.value for item in app.subheader)
