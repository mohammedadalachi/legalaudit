# pdf report generator
# layout matches the html interface: navy header, white cards, blue accents

import io
import logging
import traceback
from datetime import datetime

log = logging.getLogger("legalaudit.pdf")

# reportlab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
except ImportError as e:
    raise ImportError(
        f"ReportLab is not installed or incomplete: {e}. "
        "Run: pip install reportlab"
    ) from e

# colours, should match the css in index.html
C_NAVY       = colors.HexColor("#0a1f4e")   # --navy
C_BLUE       = colors.HexColor("#1a5fd4")   # --blue
C_BLUE_MID   = colors.HexColor("#4a85e8")   # --blue-mid
C_BLUE_DARK  = colors.HexColor("#0f3e9e")   # --blue-dark
C_BLUE_LIGHT = colors.HexColor("#e8f0fd")   # --blue-light
C_BG         = colors.HexColor("#f0f4fa")   # --bg
C_SURFACE    = colors.HexColor("#ffffff")   # --surface
C_SURFACE2   = colors.HexColor("#f7f9fc")   # --surface2
C_BORDER     = colors.HexColor("#dde3ee")   # --border
C_BORDER_MID = colors.HexColor("#c5cfe0")   # --border-mid
C_TEXT       = colors.HexColor("#0d1829")   # --text
C_MUTED      = colors.HexColor("#5a6a85")   # --text-muted
C_FAINT      = colors.HexColor("#9aa8bc")   # --text-faint
C_RED        = colors.HexColor("#d63a3a")   # --red
C_RED_DIM    = colors.HexColor("#fdf0f0")   # --red-dim
C_ORANGE     = colors.HexColor("#d97706")   # --orange
C_ORANGE_DIM = colors.HexColor("#fef8ee")   # --orange-dim
C_GREEN      = colors.HexColor("#1a7a56")   # --green
C_GREEN_DIM  = colors.HexColor("#eef8f4")   # --green-dim
C_BLUE_BD    = colors.HexColor("#c4d8f7")   # blue border

RISK_COLOR = {"HIGH": C_RED,     "MEDIUM": C_ORANGE, "LOW": C_BLUE}
RISK_BG    = {"HIGH": C_RED_DIM, "MEDIUM": C_ORANGE_DIM, "LOW": C_BLUE_LIGHT}
RISK_BD    = {
    "HIGH":   colors.HexColor("#f5c0c0"),
    "MEDIUM": colors.HexColor("#f8dfa0"),
    "LOW":    C_BLUE_BD,
}
STATUS_COLOR = {
    "CRITICAL": C_RED,    "RISK":   C_ORANGE,
    "REVIEW":   C_BLUE_MID, "MINOR": C_BLUE_MID, "PASS": C_GREEN,
}
STATUS_BG = {
    "CRITICAL": C_RED_DIM,    "RISK":   C_ORANGE_DIM,
    "REVIEW":   C_BLUE_LIGHT, "MINOR":  C_BLUE_LIGHT, "PASS": C_GREEN_DIM,
}


# main entry point
def generate_pdf_report(report_data: dict) -> bytes:
    if not isinstance(report_data, dict):
        raise RuntimeError(f"report_data must be a dict, got {type(report_data).__name__}.")

    try:
        summary    = report_data.get("summary") or {}
        findings   = report_data.get("findings") or []
        extraction = report_data.get("extraction_info") or {}

        if not isinstance(summary, dict):
            raise RuntimeError(f"'summary' must be a dict, got {type(summary).__name__}.")
        if not isinstance(findings, list):
            raise RuntimeError(f"'findings' must be a list, got {type(findings).__name__}.")

        doc_type  = report_data.get("doc_type", summary.get("doc_type", "employment"))
        doc_label = (
            "Employment Contract" if doc_type == "employment"
            else "Residential Tenancy Agreement"
        )
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to parse report data: {e}") from e

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=18*mm, rightMargin=18*mm,
            topMargin=18*mm, bottomMargin=18*mm,
            title="LegalAudit Compliance Report", author="LegalAudit"
        )
        story = []
        S = _build_styles()

        # 1. Navy topbar
        try:
            story.append(_topbar(S, doc_label))
        except Exception as e:
            log.warning("Topbar failed: %s", e)
            story.append(Paragraph(f"<b>LegalAudit</b>", S["logo"]))
        story.append(Spacer(1, 5*mm))

        # 2. Meta strip (mirrors the .ocr-info mono line on the website, no boxes)
        try:
            now       = datetime.now().strftime("%d %B %Y, %I:%M %p")
            chars     = extraction.get("characters_extracted", 0)
            chars_str = f"{chars:,}" if isinstance(chars, int) else str(chars)
            method    = _safe_str(extraction.get("method", ","))
            pages     = str(extraction.get("pages", ","))
            meta_line = (
                f'<font color="#{_hex(C_BLUE_MID)}">&#9656;</font> {now}'
                f'    <font color="#{_hex(C_BLUE_MID)}">&#9656;</font> {doc_label}'
                f'    <font color="#{_hex(C_BLUE_MID)}">&#9656;</font> {method}'
                f'    <font color="#{_hex(C_BLUE_MID)}">&#9656;</font> {pages} page(s)'
                f'    <font color="#{_hex(C_BLUE_MID)}">&#9656;</font> {chars_str} chars'
            )
            story.append(Paragraph(meta_line, S["meta_strip"]))
        except Exception as e:
            log.warning("Meta strip failed: %s", e)
        story.append(Spacer(1, 5*mm))

        # 3. Overall status banner (left accent only, like .overall-status on the site)
        try:
            code   = summary.get("overall_code", "PASS")
            sc     = STATUS_COLOR.get(code, C_GREEN)
            sbg    = STATUS_BG.get(code, C_GREEN_DIM)
            status = _safe_str(summary.get("overall_status", ""))
            st = Table([[Paragraph(status, S["status_text"])]], colWidths=[174*mm])
            st.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), sbg),
                ("TOPPADDING",    (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING",   (0, 0), (-1, -1), 14),
                ("LINEBEFORE",    (0, 0), (0, -1),  3, sc),
            ]))
            story.append(st)
        except Exception as e:
            log.warning("Status banner failed: %s", e)
        story.append(Spacer(1, 5*mm))

        # 4. Stats grid: five separate light cards with gaps, like .stat on the site
        try:
            def _stat_card(num, label, col):
                cell = Table([
                    [Paragraph(f'<font color="#{_hex(col)}"><b>{num}</b></font>', S["stat_num"])],
                    [Paragraph(label, S["stat_label"])],
                ], colWidths=[31.6*mm])
                cell.setStyle(TableStyle([
                    ("BOX",           (0, 0), (-1, -1), 0.75, C_BORDER),
                    ("BACKGROUND",    (0, 0), (-1, -1), C_SURFACE),
                    ("TOPPADDING",    (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ]))
                return cell

            cards = [
                _stat_card(str(summary.get("total_rules_checked", 0)), "CHECKED",   C_TEXT),
                _stat_card(str(summary.get("high_risk",  0)),          "HIGH RISK", C_RED),
                _stat_card(str(summary.get("medium_risk", 0)),         "MEDIUM",    C_ORANGE),
                _stat_card(str(summary.get("low_risk",   0)),          "LOW RISK",  C_BLUE),
                _stat_card(str(summary.get("compliant",  0)),          "PASSED",    C_GREEN),
            ]
            gap = 1.6*mm
            sg = Table([cards], colWidths=[31.6*mm, gap, 31.6*mm, gap, 31.6*mm, gap, 31.6*mm, gap, 31.6*mm])
            # interleave the gap columns are handled by spacing the row manually below instead
            row_cells = []
            for i, c in enumerate(cards):
                row_cells.append(c)
            sg = Table([row_cells], colWidths=[34.8*mm] * 5, spaceBefore=0)
            sg.setStyle(TableStyle([
                ("LEFTPADDING",   (0, 0), (-1, -1), 1.5*mm),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 1.5*mm),
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(sg)
        except Exception as e:
            log.warning("Stats grid failed: %s", e)
        story.append(Spacer(1, 7*mm))

        # 5. Findings header
        count = len(findings)
        story.append(Paragraph(
            f"Findings , {count} issue{'s' if count != 1 else ''} detected",
            S["section_title"]
        ))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=3*mm))

        # 6. Each finding card
        if not findings:
            story.append(Paragraph("All rules passed. No issues detected.", S["pass_text"]))
        else:
            for i, f in enumerate(findings):
                if not isinstance(f, dict):
                    continue
                try:
                    story.append(KeepTogether(_finding_block(f, S)))
                    story.append(Spacer(1, 4*mm))
                except Exception as e:
                    log.warning("Could not render finding %d: %s", i, e)
                    try:
                        story.append(Paragraph(
                            f"[Render error , {f.get('name', '?')}]", S["body"]
                        ))
                    except Exception:
                        pass

        # 7. Disclaimer
        story.append(Spacer(1, 6*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=3*mm))
        story.append(Paragraph(
            "<b>Disclaimer:</b> LegalAudit is a first-line compliance screening "
            "tool and does not constitute legal advice. All findings should be "
            "verified against current Malaysian statutes by a qualified legal "
            "practitioner before any legal decision is made.",
            S["disclaimer"]
        ))

        # Build
        try:
            doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
        except Exception as e:
            log.error("doc.build() failed: %s\n%s", e, traceback.format_exc())
            raise RuntimeError(f"PDF rendering failed: {e}") from e

        buffer.seek(0)
        pdf_bytes = buffer.read()
        if not pdf_bytes:
            raise RuntimeError("PDF build completed but produced 0 bytes.")

        log.info("PDF generated: %s bytes", f"{len(pdf_bytes):,}")
        return pdf_bytes

    except RuntimeError:
        raise
    except Exception as e:
        log.error("Unexpected error in generate_pdf_report: %s\n%s", e, traceback.format_exc())
        raise RuntimeError(f"PDF generation failed unexpectedly: {e}") from e


# topbar
def _topbar(S, doc_label: str) -> Table:
    t = Table([
        [
            Paragraph("<b>LegalAudit</b>", S["logo"]),
            Paragraph("EA 1955 · MALAYSIA", S["topbar_pill"]),
            Paragraph(f"Compliance Report  ·  {doc_label}", S["topbar_right"]),
        ]
    ], colWidths=[60*mm, 54*mm, 60*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, 0),   12),
        ("RIGHTPADDING",  (2, 0), (2, 0),   12),
        ("ALIGN",         (1, 0), (1, 0),   "CENTER"),
        ("ALIGN",         (2, 0), (2, 0),   "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# finding block
def _finding_block(f: dict, S) -> list:
    risk = f.get("risk", "LOW")
    bg   = RISK_BG.get(risk, C_SURFACE2)
    rc   = RISK_COLOR.get(risk, C_BLUE)
    bd   = RISK_BD.get(risk, C_BORDER)

    name      = _safe_str(f.get("name", "Unknown"))
    issue     = _safe_str(f.get("issue_type", ""))
    statute   = _safe_str(f.get("statute", ""))
    desc      = _safe_str(f.get("description", ""))
    rec       = _safe_str(f.get("recommendation", ""))
    kw        = f.get("matched_keyword")
    reasoning = f.get("reasoning_chain") or []

    # Header row: RISK | issue_type | name + statute
    header = Table([[
        Paragraph(f"<b>{risk}</b>", S["risk_badge"]),
        Paragraph(issue,            S["issue_badge"]),
        [Paragraph(f"<b>{name}</b>", S["finding_name"]),
         Paragraph(statute,          S["statute"])],
    ]], colWidths=[16*mm, 38*mm, 120*mm])
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0),   rc),
        ("TEXTCOLOR",     (0, 0), (0, 0),   colors.white),
        ("ALIGN",         (0, 0), (0, 0),   "CENTER"),
        ("BACKGROUND",    (1, 0), (1, 0),   C_SURFACE2),
        ("ALIGN",         (1, 0), (1, 0),   "CENTER"),
        ("BACKGROUND",    (2, 0), (2, 0),   bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, bd),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, bd),
    ]))

    # Body rows
    body_rows = [
        [Paragraph(desc, S["body"])],
        [Spacer(1, 2*mm)],
        [Paragraph(f"<b>Recommendation ,</b> {rec}", S["recommendation"])],
    ]
    if kw:
        body_rows += [
            [Spacer(1, 1*mm)],
            [Paragraph(f"matched: <i>{_safe_str(kw)}</i>", S["matched_kw"])],
        ]
    if reasoning:
        body_rows += [
            [Spacer(1, 3*mm)],
            [Paragraph("<b>Explanation Facility , Reasoning Trace</b>", S["trace_title"])],
        ]
        for i, step in enumerate(reasoning, 1):
            try:
                body_rows.append([Paragraph(f"{i}.  {_safe_str(step)}", S["trace_step"])])
            except Exception as e:
                log.warning("Reasoning step %d failed: %s", i, e)
    body_rows.append([Spacer(1, 3*mm)])

    body = Table(body_rows, colWidths=[174*mm])
    body.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, rc),
        ("LINEAFTER",     (0, 0), (-1, -1), 0.5, bd),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.5, bd),
    ]))

    return [header, body]


# footer
def _page_footer(canvas, doc):
    try:
        canvas.saveState()
        canvas.setStrokeColor(C_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(18*mm, 13*mm, A4[0] - 18*mm, 13*mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_FAINT)
        canvas.drawString(18*mm, 9*mm, "LegalAudit , Malaysian Contract Auditor")
        canvas.drawRightString(
            A4[0] - 18*mm, 9*mm,
            f"Page {doc.page}  ·  {datetime.now().strftime('%d %b %Y')}"
        )
        canvas.restoreState()
    except Exception as e:
        log.warning("Footer rendering failed on page %d: %s", doc.page, e)


# styles
def _build_styles() -> dict:
    return {
        "logo": ParagraphStyle(
            "logo", fontName="Helvetica-Bold", fontSize=14, textColor=colors.white),
        "topbar_right": ParagraphStyle(
            "topbar_right", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#c8d8f0"), alignment=TA_RIGHT, leading=12),
        "topbar_pill": ParagraphStyle(
            "topbar_pill", fontName="Helvetica", fontSize=7,
            textColor=colors.HexColor("#7f9ac0"), alignment=TA_CENTER),
        "meta_key": ParagraphStyle(
            "meta_key", fontName="Helvetica-Bold", fontSize=8, textColor=C_MUTED),
        "meta_val": ParagraphStyle(
            "meta_val", fontName="Helvetica", fontSize=8, textColor=C_TEXT),
        "status_text": ParagraphStyle(
            "status_text", fontName="Helvetica-Bold", fontSize=10,
            textColor=C_TEXT, leading=14),
        "stat_num": ParagraphStyle(
            "stat_num", fontName="Helvetica-Bold", fontSize=20,
            alignment=TA_CENTER, leading=24),
        "stat_label": ParagraphStyle(
            "stat_label", fontName="Helvetica", fontSize=7,
            textColor=C_FAINT, alignment=TA_CENTER, leading=10),
        "section_title": ParagraphStyle(
            "section_title", fontName="Helvetica-Bold", fontSize=11,
            textColor=C_TEXT, spaceAfter=2),
        "risk_badge": ParagraphStyle(
            "risk_badge", fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.white, alignment=TA_CENTER),
        "issue_badge": ParagraphStyle(
            "issue_badge", fontName="Helvetica", fontSize=7,
            textColor=C_MUTED, alignment=TA_CENTER),
        "finding_name": ParagraphStyle(
            "finding_name", fontName="Helvetica-Bold", fontSize=9,
            textColor=C_TEXT, leading=13),
        "statute": ParagraphStyle(
            "statute", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=C_FAINT, leading=11),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=8.5,
            textColor=C_MUTED, leading=13),
        "recommendation": ParagraphStyle(
            "recommendation", fontName="Helvetica", fontSize=8.5,
            textColor=C_NAVY, leading=13),
        "matched_kw": ParagraphStyle(
            "matched_kw", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=C_BLUE, leading=11),
        "trace_title": ParagraphStyle(
            "trace_title", fontName="Helvetica-Bold", fontSize=8,
            textColor=C_BLUE, spaceBefore=3, leading=12),
        "trace_step": ParagraphStyle(
            "trace_step", fontName="Helvetica", fontSize=7.5,
            textColor=C_MUTED, leading=11, leftIndent=8),
        "pass_text": ParagraphStyle(
            "pass_text", fontName="Helvetica-Bold", fontSize=11,
            textColor=C_GREEN, alignment=TA_CENTER),
        "disclaimer": ParagraphStyle(
            "disclaimer", fontName="Helvetica", fontSize=7.5,
            textColor=C_FAINT, leading=11),
    }


# utils
def _hex(color) -> str:
    """Extract 6-char hex from a ReportLab color for inline font tags."""
    return color.hexval()[2:]


def _safe_str(value) -> str:
    if value is None:
        return ""
    try:
        import re
        s = str(value).replace("\x00", "")
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
        return s
    except Exception:
        return ""