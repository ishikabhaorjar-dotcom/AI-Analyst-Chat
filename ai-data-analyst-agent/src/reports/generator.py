"""
Builds the downloadable PDF report: dataset overview, data quality, key
stats, insights, and recommendations. Uses ReportLab directly (no LLM call
required to lay out a PDF) but pulls its narrative content from insights
that were already computed elsewhere — this module never invents numbers.
"""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from src.core.profiler import DatasetProfile
from src.tools.eda_tool import EDAResult

ACCENT = colors.HexColor("#1F4E79")
LIGHT = colors.HexColor("#EEF3F8")


def generate_pdf_report(profile: DatasetProfile, eda: EDAResult,
                        insights: list[str], recommendations: list[str],
                        dataset_name: str = "Uploaded Dataset") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"AI Data Analysis Report - {dataset_name}")

    ss = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=ss["Title"], fontSize=19, textColor=ACCENT)
    sub_style = ParagraphStyle("S", parent=ss["Normal"], fontSize=9.5, textColor=colors.HexColor("#555555"))
    h_style = ParagraphStyle("H", parent=ss["Heading2"], fontSize=12, textColor=ACCENT, spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("B", parent=ss["Normal"], fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY)

    story = []
    story.append(Paragraph("AI Data Analysis Report", title_style))
    story.append(Paragraph(f"{dataset_name} &nbsp;|&nbsp; Generated {datetime.now().strftime('%d %b %Y')}", sub_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1, spaceAfter=8))

    # 1. Dataset overview
    story.append(Paragraph("1. Dataset Overview", h_style))
    overview_data = [
        ["Rows", f"{profile.n_rows:,}"],
        ["Columns", str(profile.n_cols)],
        ["Memory Usage", f"{profile.memory_mb:.2f} MB"],
        ["Duplicate Rows", str(profile.duplicate_rows)],
        ["Overall Missing %", f"{profile.missing_total_pct:.2f}%"],
        ["Numerical Columns", str(len(profile.numerical_cols))],
        ["Categorical Columns", str(len(profile.categorical_cols))],
        ["Date Columns", str(len(profile.date_cols))],
    ]
    t = Table(overview_data, colWidths=[60 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C5D3E2")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    # 2. Data quality
    story.append(Paragraph("2. Data Quality Summary", h_style))
    if eda.missing_by_column:
        rows = [["Column", "Missing %"]] + [[c, f"{p}%"] for c, p in eda.missing_by_column.items()]
        tq = Table(rows, colWidths=[100 * mm, 60 * mm])
        tq.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C5D3E2")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]))
        story.append(tq)
    else:
        story.append(Paragraph("No missing values detected across any column.", body_style))

    if eda.outlier_summary:
        story.append(Spacer(1, 4))
        outlier_text = ", ".join(f"{c} ({n} values)" for c, n in eda.outlier_summary.items())
        story.append(Paragraph(f"<b>Potential outliers detected in:</b> {outlier_text}", body_style))

    # 3. Correlations
    if eda.top_correlated_pairs:
        story.append(Paragraph("3. Strongest Relationships", h_style))
        rows = [["Column A", "Column B", "Correlation"]] + [
            [a, b, f"{v:+.2f}"] for a, b, v in eda.top_correlated_pairs
        ]
        tc = Table(rows, colWidths=[55 * mm, 55 * mm, 50 * mm])
        tc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C5D3E2")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]))
        story.append(tc)

    # 4. Insights
    story.append(Paragraph("4. Key Insights", h_style))
    if insights:
        story.append(ListFlowable(
            [ListItem(Paragraph(i, body_style), leftIndent=10) for i in insights],
            bulletType="bullet", bulletColor=ACCENT, leftIndent=12,
        ))
    else:
        story.append(Paragraph("No narrative insights were generated for this session.", body_style))

    # 5. Recommendations
    story.append(Paragraph("5. Recommendations", h_style))
    if recommendations:
        story.append(ListFlowable(
            [ListItem(Paragraph(r, body_style), leftIndent=10) for r in recommendations],
            bulletType="bullet", bulletColor=ACCENT, leftIndent=12,
        ))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#C5D3E2"), thickness=0.6))
    story.append(Paragraph(
        "<font size=8 color='#777777'>Generated by AI Data Analyst Agent — "
        "an autonomous agent pipeline built with LangGraph, Groq, and Pydantic.</font>",
        sub_style,
    ))

    doc.build(story)
    return buffer.getvalue()
