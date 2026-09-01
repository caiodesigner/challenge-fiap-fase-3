from pathlib import Path

from scripts.build_final_report import build_pdf


def test_builds_readable_pdf(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "report.pdf"
    generated = build_pdf(root / "docs/relatorio-tecnico-final.md", output)
    content = generated.read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 10_000
