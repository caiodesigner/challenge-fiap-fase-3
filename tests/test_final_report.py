from pathlib import Path

from scripts.build_final_report import _langchain_diagram, build_pdf


def test_langchain_diagram_is_embeddable() -> None:
    diagram = _langchain_diagram("Helvetica", "Helvetica-Bold")
    assert diagram.width == 440
    assert diagram.height == 430
    assert len(diagram.contents) >= 40


def test_builds_readable_pdf(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "report.pdf"
    generated = build_pdf(root / "docs/relatorio-tecnico-final.md", output)
    content = generated.read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 10_000
