from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib import colors

def _style(name, parent, size, bold=False, align=TA_LEFT, before=2, after=2, leading=None, keep=False):
    s = ParagraphStyle(
        name=name,
        parent=parent,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        alignment=align,
        leading=leading or (size + 1.5),
        spaceBefore=before,
        spaceAfter=after,
        allowWidows=1,
        allowOrphans=1,
    )
    s.keepWithNext = keep
    return s

def _two_col_header(header_left: str, header_right: str, H3, DATE):
    data = [[Paragraph(header_left or "", H3), Paragraph(header_right or "", DATE)]]
    t = Table(data, colWidths=["* ", 1.9*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN',  (0,0), (0,0), 'LEFT'),
        ('ALIGN',  (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ('TOPPADDING',  (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',(0,0), (-1,-1), 0),
    ]))
    return t

def build_pdf(model: dict, out_path: str):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=LETTER,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
    )

    S = getSampleStyleSheet()
    H1   = _style("H1",   S["Normal"], 16.5, bold=True, align=TA_CENTER, before=0, after=2)
    H2   = _style("H2",   S["Normal"], 11.7, bold=True, keep=True, before=10, after=4)
    H3   = _style("H3",   S["Normal"], 10.7, bold=True, before=2, after=1)
    DATE = _style("DATE", S["Normal"], 10,   bold=False, align=TA_RIGHT, before=0, after=2)
    BODY = _style("BODY", S["Normal"], 10.1, bold=False, before=0, after=0, leading=12)

    flow = []
    flow.append(Paragraph(f"<b>{model.get('name','Your Name')}</b>", H1))
    flow.append(Paragraph(model.get("contact",""), _style("Contact", S["Normal"], 9.8, align=TA_CENTER, before=0, after=6)))
    flow.append(HRFlowable(width="100%", thickness=1, color="#444", spaceBefore=2, spaceAfter=8))

    def bullets(items):
        items = [x for x in items if x and len(str(x).strip()) > 0]
        return ListFlowable(
            [ListItem(Paragraph(str(x), BODY), leftIndent=10) for x in items],
            bulletType="bullet", start="•", leftIndent=14, spaceBefore=0, spaceAfter=6
        )

    # Summary
    if model.get("summary"):
        flow.append(Paragraph("SUMMARY", H2))
        flow.append(bullets(model["summary"]))

    # Skills (grouped mini-headers)
    grouped = model.get("skills_grouped") or {}
    flat = model.get("skills") or []
    if grouped or flat:
        flow.append(Paragraph("SKILLS", H2))
        if grouped:
            order = ["Languages","Frameworks & Libraries","Data & Cloud","DevOps","Design & Tools","Soft Skills","Other"]
            for k in order:
                if k in grouped and grouped[k]:
                    line = f"<b>{k}:</b> " + ", ".join(grouped[k])
                    flow.append(Paragraph(line, BODY))
            flow.append(Spacer(1, 6))
        else:
            flow.append(Paragraph(", ".join(flat), BODY))
            flow.append(Spacer(1, 6))

    # Experience
    exps = model.get("experience_entries") or []
    if exps:
        flow.append(Paragraph("WORK EXPERIENCE", H2))
        for e in exps:
            flow.append(_two_col_header(e.get("header","").strip(), e.get("dates","").strip(), H3, DATE))
            flow.append(bullets(e.get("bullets") or []))

    # Projects
    projs = model.get("project_entries") or []
    if projs:
        flow.append(Paragraph("PROJECTS", H2))
        for p in projs:
            flow.append(_two_col_header(p.get("header","").strip(), p.get("dates","").strip(), H3, DATE))
            flow.append(bullets(p.get("bullets") or []))

    # Education
    if model.get("education"):
        flow.append(Paragraph("EDUCATION", H2))
        edu = model["education"]
        if isinstance(edu, list):
            flow.append(bullets(edu))
        else:
            flow.append(bullets([str(edu)]))

    doc.build(flow)
