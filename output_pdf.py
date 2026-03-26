"""
output_pdf.py
PDF generation using ReportLab — professional book-style formatting.
"""

import logging
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Page dimensions and margins
# ─────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN_LEFT = 1.25 * inch
MARGIN_RIGHT = 1.25 * inch
MARGIN_TOP = 1.0 * inch
MARGIN_BOTTOM = 1.0 * inch

# ─────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────
BLACK = colors.black
WHITE = colors.white
DARK_GRAY = colors.HexColor("#222222")


def _build_styles() -> dict:
    """Define all paragraph styles for the book."""
    base = getSampleStyleSheet()

    styles = {}

    # Title page: book title
    styles["BookTitle"] = ParagraphStyle(
        "BookTitle",
        parent=base["Normal"],
        fontName="Times-Bold",
        fontSize=32,
        leading=40,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=24,
    )

    # Title page: subtitle / author
    styles["BookAuthor"] = ParagraphStyle(
        "BookAuthor",
        parent=base["Normal"],
        fontName="Times-Italic",
        fontSize=16,
        leading=24,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    # Chapter heading
    styles["ChapterHeading"] = ParagraphStyle(
        "ChapterHeading",
        parent=base["Normal"],
        fontName="Times-Bold",
        fontSize=22,
        leading=30,
        textColor=DARK_GRAY,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=18,
    )

    # Chapter number label (e.g. "CHAPTER ONE")
    styles["ChapterLabel"] = ParagraphStyle(
        "ChapterLabel",
        parent=base["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#666666"),
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=6,
        tracking=2,
    )

    # Body text
    styles["BodyText"] = ParagraphStyle(
        "BodyText",
        parent=base["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=20,
        textColor=DARK_GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        firstLineIndent=0.3 * inch,
    )

    # Page number
    styles["PageNumber"] = ParagraphStyle(
        "PageNumber",
        parent=base["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
    )

    return styles


# ─────────────────────────────────────────────
# Page templates
# ─────────────────────────────────────────────

def _make_page_templates(doc) -> list:
    """Create page templates: blank title page + body pages with footer."""

    def _footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(colors.HexColor("#888888"))
        page_num = doc_obj.page
        if page_num > 1:
            canvas.drawCentredString(
                PAGE_WIDTH / 2,
                0.6 * inch,
                f"— {page_num} —",
            )
        canvas.restoreState()

    # Title page (no footer)
    title_frame = Frame(
        MARGIN_LEFT,
        MARGIN_BOTTOM,
        PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        id="title_frame",
    )
    title_template = PageTemplate(
        id="TitlePage",
        frames=[title_frame],
    )

    # Body pages with footer
    body_frame = Frame(
        MARGIN_LEFT,
        MARGIN_BOTTOM + 0.3 * inch,
        PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - 0.3 * inch,
        id="body_frame",
    )
    body_template = PageTemplate(
        id="BodyPage",
        frames=[body_frame],
        onPage=_footer,
    )

    return [title_template, body_template]


# ─────────────────────────────────────────────
# PDF builder
# ─────────────────────────────────────────────

def generate_pdf(book, output_path: Path) -> Path:
    """
    Generate a professionally formatted PDF book.

    Args:
        book: Book dataclass with title, author, chapters list
        output_path: Full path where the PDF should be saved

    Returns:
        Path to the saved PDF file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _build_styles()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=book.title,
        author=book.author,
    )

    doc.addPageTemplates(_make_page_templates(doc))

    story = []

    # ── Title Page ──────────────────────────────
    story.append(NextPageTemplate("TitlePage"))
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph(book.title, styles["BookTitle"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("by", styles["BookAuthor"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(book.author, styles["BookAuthor"]))
    story.append(PageBreak())

    # ── Chapters ────────────────────────────────
    story.append(NextPageTemplate("BodyPage"))

    ORDINALS = [
        "One", "Two", "Three", "Four", "Five",
        "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
        "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
    ]

    for chapter in book.chapters:
        ordinal = (
            ORDINALS[chapter.number - 1]
            if chapter.number <= len(ORDINALS)
            else str(chapter.number)
        )

        story.append(Paragraph(f"CHAPTER {ordinal.upper()}", styles["ChapterLabel"]))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph(chapter.title, styles["ChapterHeading"]))
        story.append(Spacer(1, 0.2 * inch))

        # Split content into paragraphs and render each
        paragraphs = [p.strip() for p in chapter.content.split("\n") if p.strip()]
        for para_text in paragraphs:
            story.append(Paragraph(para_text, styles["BodyText"]))

        story.append(PageBreak())

    # Build PDF
    try:
        doc.build(story)
        logger.info("PDF saved to: %s", output_path)
    except Exception as exc:
        logger.error("Failed to build PDF: %s", exc)
        raise RuntimeError(f"PDF generation failed: {exc}") from exc

    return output_path