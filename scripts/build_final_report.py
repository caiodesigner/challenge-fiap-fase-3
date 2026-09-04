"""Converte o relatório Markdown consolidado em um PDF simples e legível."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
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


def _langchain_diagram(regular: str, bold: str) -> Drawing:
    """Cria uma figura vetorial do pipeline sem depender de renderizador externo."""
    drawing = Drawing(440, 430)
    teal = colors.HexColor("#0F766E")
    navy = colors.HexColor("#0F172A")
    light = colors.HexColor("#E2E8F0")
    pale = colors.HexColor("#CCFBF1")
    warning = colors.HexColor("#FEF3C7")

    def box(
        x: float,
        y: float,
        width: float,
        label: str,
        *,
        fill=light,  # type: ignore[no-untyped-def]
        font: str = regular,
        size: float = 7.5,
    ) -> None:
        drawing.add(Rect(x, y, width, 30, rx=5, ry=5, fillColor=fill, strokeColor=teal))
        drawing.add(
            String(
                x + width / 2,
                y + 11,
                label,
                textAnchor="middle",
                fontName=font,
                fontSize=size,
                fillColor=navy,
            )
        )

    def arrow(x1: float, y1: float, x2: float, y2: float) -> None:
        drawing.add(Line(x1, y1, x2, y2, strokeColor=teal, strokeWidth=1.2))
        drawing.add(
            Polygon(
                [x2 - 3.5, y2 + 6, x2 + 3.5, y2 + 6, x2, y2],
                fillColor=teal,
                strokeColor=teal,
            )
        )

    box(130, 390, 180, "AssistantRequest validado", fill=pale, font=bold)
    box(130, 345, 180, "validate_request")
    box(130, 300, 180, "retrieve_context", font=bold)
    box(20, 245, 180, "Ferramentas clínicas allowlisted")
    box(240, 245, 180, "Retriever E5")
    box(20, 200, 180, "SQLite sintético (somente leitura)")
    box(240, 200, 180, "Índice de protocolos versionados")
    box(110, 145, 220, "Prompt com contexto + fontes", fill=pale, font=bold)
    box(110, 100, 220, "Qwen + adaptador QLoRA")
    box(110, 55, 220, "Parsing, schema, citações e safety-v1", font=bold)
    box(110, 10, 220, "AssistantResponse estruturada", fill=pale, font=bold)
    box(345, 55, 85, "Fallback fail-closed", fill=warning, size=6.3)

    arrow(220, 390, 220, 375)
    arrow(220, 345, 220, 330)
    drawing.add(Line(220, 300, 220, 287, strokeColor=teal, strokeWidth=1.2))
    drawing.add(Line(110, 287, 330, 287, strokeColor=teal, strokeWidth=1.2))
    arrow(110, 287, 110, 275)
    arrow(330, 287, 330, 275)
    arrow(110, 245, 110, 230)
    arrow(330, 245, 330, 230)
    drawing.add(Line(110, 200, 110, 185, strokeColor=teal, strokeWidth=1.2))
    drawing.add(Line(330, 200, 330, 185, strokeColor=teal, strokeWidth=1.2))
    drawing.add(Line(110, 185, 220, 185, strokeColor=teal, strokeWidth=1.2))
    drawing.add(Line(330, 185, 220, 185, strokeColor=teal, strokeWidth=1.2))
    arrow(220, 185, 220, 175)
    arrow(220, 145, 220, 130)
    arrow(220, 100, 220, 85)
    arrow(220, 55, 220, 40)
    drawing.add(Line(330, 70, 345, 70, strokeColor=teal, strokeWidth=1.2))
    drawing.add(Line(387.5, 55, 387.5, 25, strokeColor=teal, strokeWidth=1.2))
    arrow(387.5, 25, 330, 25)
    drawing.add(String(334, 76, "erro", fontName=regular, fontSize=6.5))
    drawing.add(String(226, 43, "válida", fontName=regular, fontSize=6.5))
    return drawing


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
        if line == "[[LANGCHAIN_DIAGRAM]]":
            flush_paragraph()
            story.append(_langchain_diagram(regular, bold))
            story.append(
                Paragraph(
                    "Figura 1 — Fluxo da RunnableSequence LangChain e suas "
                    "dependências controladas.",
                    body,
                )
            )
            story.append(Spacer(1, 8))
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
