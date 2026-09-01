"""Converte o relatório Markdown consolidado em um PDF simples e legível."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/relatorio-tecnico-final.md"
OUTPUT = ROOT / "reports/deliverables/relatorio-tecnico-final.pdf"


def _fonts() -> tuple[str, str]:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.exists() and bold.exists():
        registerFont(TTFont("ReportRegular", regular))
        registerFont(TTFont("ReportBold", bold))
        return "ReportRegular", "ReportBold"
    return "Helvetica", "Helvetica-Bold"


def _footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawCentredString(A4[0] / 2, 0.8 * cm, f"Página {document.page}")
    canvas.restoreState()


def build_pdf(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    regular, bold = _fonts()
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "BodyFiap",
        parent=styles["BodyText"],
        fontName=regular,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    headings = {
        1: ParagraphStyle(
            "H1Fiap",
            parent=styles["Title"],
            fontName=bold,
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F766E"),
            spaceAfter=16,
        ),
        2: ParagraphStyle(
            "H2Fiap",
            parent=styles["Heading2"],
            fontName=bold,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F766E"),
            spaceBefore=10,
            spaceAfter=7,
        ),
        3: ParagraphStyle(
            "H3Fiap",
            parent=styles["Heading3"],
            fontName=bold,
            fontSize=11,
            leading=15,
            spaceBefore=7,
            spaceAfter=5,
        ),
    }
    code = ParagraphStyle(
        "CodeFiap",
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        backColor=colors.HexColor("#E2E8F0"),
        borderPadding=6,
        spaceAfter=8,
    )
    story: list[object] = []
    in_code = False
    code_lines: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            story.append(Paragraph(escape(text), body))
            paragraph.clear()

    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code_lines), code))
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line:
            flush_paragraph()
            continue
        if line.startswith("#"):
            flush_paragraph()
            level = min(len(line) - len(line.lstrip("#")), 3)
            title = line[level:].strip()
            if level == 2 and story:
                story.append(Spacer(1, 4))
            story.append(Paragraph(escape(title), headings[level]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(f"• {escape(line[2:])}", body))
            continue
        if line.startswith("|"):
            flush_paragraph()
            if set(line.replace("|", "").replace("-", "").replace(":", "").strip()):
                story.append(Preformatted(line, code))
            continue
        paragraph.append(line)
    flush_paragraph()
    story.append(PageBreak())
    story.append(Paragraph("Aviso final", headings[2]))
    story.append(
        Paragraph(
            "Protótipo acadêmico com dados sintéticos. Não utilizar para "
            "diagnóstico, prescrição ou atendimento clínico.",
            body,
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.5 * cm,
        title="Assistente Médico — Tech Challenge Fase 3",
        author="Equipe do Tech Challenge FIAP",
        subject="Relatório técnico final",
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output


if __name__ == "__main__":
    generated = build_pdf()
    print(f"PDF gerado: {generated} ({generated.stat().st_size} bytes)")
