"""
Generates a PDF report from a stored analysis result using reportlab
(pure-Python, no system dependency — installs via pip on Windows).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io


def generate_pdf(analysis: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=colors.HexColor("#6d28d9"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#6d28d9"))
    body = styles["BodyText"]

    result = analysis.get("result", {})
    elements = [
        Paragraph("CodeLens Analysis Report", title_style),
        Spacer(1, 6),
        Paragraph(f"Language: {analysis.get('language', '').title()}", body),
        Paragraph(f"Generated: {analysis.get('created_at', '')}", body),
        Spacer(1, 12),

        Paragraph("Explanation", h2),
        Paragraph(result.get("explanation", {}).get("summary", "N/A"), body),
        Spacer(1, 10),

        Paragraph("Submitted Code", h2),
        Preformatted(analysis.get("code", ""), styles["Code"]),
        Spacer(1, 10),
    ]

    errors = result.get("errors", [])
    elements.append(Paragraph(f"Errors Detected ({len(errors)})", h2))
    if errors:
        data = [["Line", "Type", "Severity", "Problem"]]
        for e in errors:
            data.append([str(e.get("line", "")), e.get("type", ""), e.get("severity", ""), e.get("problem", "")])
        t = Table(data, colWidths=[40, 90, 60, 260])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1030")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No confirmed errors found.", body))
    elements.append(Spacer(1, 10))

    issues = result.get("issues", [])
    elements.append(Paragraph(f"Potential Issues / Bugs ({len(issues)})", h2))
    if issues:
        data = [["Line", "Type", "Description"]]
        for i in issues:
            data.append([str(i.get("line", "")), i.get("type", ""), i.get("description", "")])
        t = Table(data, colWidths=[40, 110, 300])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1030")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No potential issues found.", body))
    elements.append(Spacer(1, 10))

    quality = result.get("quality", {})
    elements.append(Paragraph("Quality Score", h2))
    elements.append(Paragraph(
        f"Overall: {quality.get('overall', 'N/A')}/100 &nbsp; | &nbsp; "
        f"Readability: {quality.get('readability', 'N/A')} &nbsp; "
        f"Maintainability: {quality.get('maintainability', 'N/A')} &nbsp; "
        f"Complexity: {quality.get('complexity', 'N/A')} &nbsp; "
        f"Security: {quality.get('security', 'N/A')}", body))
    elements.append(Spacer(1, 10))

    improvements = result.get("improvements", [])
    elements.append(Paragraph("Improvement Suggestions", h2))
    for s in improvements:
        elements.append(Paragraph(f"• {s}", body))

    doc.build(elements)
    return buf.getvalue()
