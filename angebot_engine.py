from io import BytesIO
from datetime import date
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models import AngebotRequest

# ── Company constants ─────────────────────────────────────────────────────────

_COMPANY = "TER-BOX"
_INHABER = "Sven Terhardt"
_STREET  = "Domstraße 84"
_CITY    = "50668 Köln"
_COUNTRY = "Deutschland"
_PHONE   = "01721041972"
_EMAIL   = "sven@ter-box.com"
_WEB     = "www.ter-box.com"
_UST_ID  = "DE460259212"
_STEUER  = "21551718131"
_BANK    = "Volksbank Bocholt"
_KONTO   = "0228236302"
_BLZ     = "42860003"
_IBAN    = "DE58 4286 0003 0228 2363 02"
_BIC     = "GENODEM1BOH"

# ── Page geometry ─────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4           # 595.28 × 841.89 pt
ML = 25 * mm                  # left margin
MR = 20 * mm                  # right margin
MT = 50 * mm                  # top margin (leaves room for header canvas)
MB = 38 * mm                  # bottom margin (leaves room for footer canvas)
BODY_W = PAGE_W - ML - MR     # usable width  ≈ 165 mm

# ── Colours ───────────────────────────────────────────────────────────────────

_DARK   = colors.HexColor("#1a1a1a")
_GREY   = colors.HexColor("#555555")
_LGREY  = colors.HexColor("#999999")
_RULE   = colors.HexColor("#cccccc")
_HEAD   = colors.HexColor("#2c3e50")
_TBLHDR = colors.HexColor("#2c3e50")

# ── Styles ────────────────────────────────────────────────────────────────────

def _styles():
    base = ParagraphStyle
    return {
        "normal":   base("normal",   fontName="Helvetica",       fontSize=9,  leading=12, textColor=_DARK),
        "small":    base("small",    fontName="Helvetica",       fontSize=7.5,leading=10, textColor=_GREY),
        "bold":     base("bold",     fontName="Helvetica-Bold",  fontSize=9,  leading=12, textColor=_DARK),
        "bold_sm":  base("bold_sm",  fontName="Helvetica-Bold",  fontSize=8,  leading=11, textColor=_DARK),
        "title":    base("title",    fontName="Helvetica-Bold",  fontSize=13, leading=16, textColor=_HEAD),
        "intro":    base("intro",    fontName="Helvetica",       fontSize=9,  leading=13, textColor=_DARK),
        "tbl_hdr":  base("tbl_hdr", fontName="Helvetica-Bold",  fontSize=8,  leading=10, textColor=colors.white),
        "tbl_cell": base("tbl_cell", fontName="Helvetica",       fontSize=8.5,leading=11, textColor=_DARK),
        "tbl_desc": base("tbl_desc", fontName="Helvetica",       fontSize=8.5,leading=12, textColor=_DARK),
        "tbl_r":    base("tbl_r",    fontName="Helvetica",       fontSize=8.5,leading=11, textColor=_DARK,   alignment=TA_RIGHT),
        "tot_lbl":  base("tot_lbl",  fontName="Helvetica",       fontSize=9,  leading=13, textColor=_DARK,   alignment=TA_RIGHT),
        "tot_val":  base("tot_val",  fontName="Helvetica",       fontSize=9,  leading=13, textColor=_DARK,   alignment=TA_RIGHT),
        "tot_bold": base("tot_bold", fontName="Helvetica-Bold",  fontSize=10, leading=14, textColor=_HEAD,   alignment=TA_RIGHT),
        "footer":   base("footer",   fontName="Helvetica",       fontSize=7,  leading=9,  textColor=_LGREY),
        "closing":  base("closing",  fontName="Helvetica",       fontSize=9,  leading=13, textColor=_DARK),
    }


# ── Header (drawn on canvas) ──────────────────────────────────────────────────

def _draw_header(canvas, doc, req: AngebotRequest):
    canvas.saveState()
    s = _styles()

    # Sender line above recipient address
    sender_y = PAGE_H - 22 * mm
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_LGREY)
    canvas.drawString(ML, sender_y, f"{_COMPANY} Inhaber {_INHABER}  ·  {_STREET}  ·  {_CITY}")

    # Thin underline under sender
    canvas.setStrokeColor(_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(ML, sender_y - 1.5 * mm, PAGE_W - MR, sender_y - 1.5 * mm)

    # Recipient address block (left)
    addr_lines = []
    if req.anrede:
        addr_lines.append(req.anrede + " " + req.name)
    else:
        addr_lines.append(req.name)
    if req.firma:
        addr_lines.append(req.firma)
    addr_lines += [req.strasse, f"{req.plz} {req.ort}", req.land]

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(_DARK)
    ay = PAGE_H - 32 * mm
    for line in addr_lines:
        canvas.drawString(ML, ay, line)
        ay -= 12

    # Document info table (right column)
    col_lbl = PAGE_W - MR - 70 * mm
    col_val = PAGE_W - MR - 5 * mm
    info_rows = [
        ("Angebots-Nr.",    req.angebots_nr),
        ("Datum",           req.datum or date.today().strftime("%d.%m.%Y")),
    ]
    if req.kundennummer:
        info_rows.append(("Ihre Kundennummer", req.kundennummer))
    info_rows.append(("Ihr Ansprechpartner", req.ansprechpartner))

    iy = PAGE_H - 32 * mm
    canvas.setFont("Helvetica", 8.5)
    for lbl, val in info_rows:
        canvas.setFillColor(_LGREY)
        canvas.drawString(col_lbl, iy, lbl)
        canvas.setFillColor(_DARK)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawRightString(col_val, iy, val)
        canvas.setFont("Helvetica", 8.5)
        iy -= 13

    canvas.restoreState()


# ── Footer (drawn on canvas) ──────────────────────────────────────────────────

def _draw_footer(canvas, doc):
    canvas.saveState()
    y_rule = MB - 6 * mm
    canvas.setStrokeColor(_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(ML, y_rule, PAGE_W - MR, y_rule)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_LGREY)

    # Left block
    lx = ML
    canvas.drawString(lx, y_rule - 8,  f"{_COMPANY} Inhaber {_INHABER}")
    canvas.drawString(lx, y_rule - 17, f"{_STREET}")
    canvas.drawString(lx, y_rule - 26, f"{_CITY}")
    canvas.drawString(lx, y_rule - 35, _COUNTRY)

    # Middle block
    mx = ML + 55 * mm
    canvas.drawString(mx, y_rule - 8,  f"Tel. {_PHONE}")
    canvas.drawString(mx, y_rule - 17, f"E-Mail {_EMAIL}")
    canvas.drawString(mx, y_rule - 26, f"Web {_WEB}")

    # Right block (tax)
    rx = ML + 105 * mm
    canvas.drawString(rx, y_rule - 8,  f"USt.-ID {_UST_ID}")
    canvas.drawString(rx, y_rule - 17, f"Steuer-Nr. {_STEUER}")
    canvas.drawString(rx, y_rule - 26, f"Inhaber/-in {_INHABER}")

    # Bank block
    bx = ML + 135 * mm
    canvas.drawString(bx, y_rule - 8,  f"Bank {_BANK}")
    canvas.drawString(bx, y_rule - 17, f"Konto {_KONTO}")
    canvas.drawString(bx, y_rule - 26, f"BLZ {_BLZ}")
    canvas.drawString(bx, y_rule - 35, f"IBAN {_IBAN}")
    canvas.drawString(bx, y_rule - 44, f"BIC {_BIC}")

    # Page number
    page_num = f"{doc.page}/{doc._pageCount if hasattr(doc, '_pageCount') else '?'}"
    canvas.drawRightString(PAGE_W - MR, y_rule - 8, page_num)

    canvas.restoreState()


# ── Column widths for line-item table ─────────────────────────────────────────

_COL_POS   = 9  * mm
_COL_DESC  = 89 * mm
_COL_QTY   = 18 * mm
_COL_UNIT  = 18 * mm
_COL_TOTAL = 22 * mm
# Sum must equal BODY_W ≈ 165 mm  →  9+89+18+18+22 = 156 … leave 9mm slack via desc
_COL_DESC  = BODY_W - _COL_POS - _COL_QTY - _COL_UNIT - _COL_TOTAL


# ── Main generator ────────────────────────────────────────────────────────────

def generate_angebot_pdf(req: AngebotRequest) -> bytes:
    buf = BytesIO()
    s = _styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB,
        title=f"Angebot {req.angebots_nr}",
        author=_COMPANY,
    )

    def on_page(canvas, doc):
        _draw_header(canvas, doc, req)
        _draw_footer(canvas, doc)

    story = []

    # ── Subject line ──────────────────────────────────────────────────────────
    story.append(Paragraph(f"Angebot {req.angebots_nr}", s["title"]))
    story.append(Spacer(1, 5 * mm))

    # ── Intro text ────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Sehr geehrte Damen und Herren,<br/>"
        "vielen Dank für Ihre Anfrage. Gerne unterbreiten wir Ihnen das gewünschte "
        "freibleibende Angebot:",
        s["intro"],
    ))
    story.append(Spacer(1, 6 * mm))

    # ── Line-item table ───────────────────────────────────────────────────────
    col_ws = [_COL_POS, _COL_DESC, _COL_QTY, _COL_UNIT, _COL_TOTAL]

    tbl_data = [[
        Paragraph("Pos.", s["tbl_hdr"]),
        Paragraph("Beschreibung", s["tbl_hdr"]),
        Paragraph("Menge", s["tbl_hdr"]),
        Paragraph("Einzelpreis", s["tbl_hdr"]),
        Paragraph("Gesamtpreis", s["tbl_hdr"]),
    ]]

    for i, pos in enumerate(req.positionen, start=1):
        gesamtpreis = pos.menge * pos.einzelpreis
        desc_text = pos.beschreibung.replace("\n", "<br/>")
        tbl_data.append([
            Paragraph(str(i) + ".", s["tbl_cell"]),
            Paragraph(desc_text, s["tbl_desc"]),
            Paragraph(f"{pos.menge:,.2f} {pos.einheit}".replace(",", "X").replace(".", ",").replace("X", "."), s["tbl_r"]),
            Paragraph(_eur(pos.einzelpreis), s["tbl_r"]),
            Paragraph(_eur(gesamtpreis), s["tbl_r"]),
        ])

    tbl = Table(tbl_data, colWidths=col_ws, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",   (0, 0), (-1, 0), _TBLHDR),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("TOPPADDING",   (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 5),
        ("LEFTPADDING",  (0, 0), (-1, 0), 5),
        ("RIGHTPADDING", (0, 0), (-1, 0), 5),
        # Body rows
        ("BACKGROUND",   (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("TOPPADDING",   (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 5),
        ("LEFTPADDING",  (0, 1), (-1, -1), 5),
        ("RIGHTPADDING", (0, 1), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        # Borders
        ("LINEBELOW",    (0, 0), (-1, 0), 0.5, _HEAD),
        ("LINEBELOW",    (0, 1), (-1, -1), 0.3, _RULE),
        ("BOX",          (0, 0), (-1, -1), 0.5, _RULE),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Totals block ──────────────────────────────────────────────────────────
    netto = sum(p.menge * p.einzelpreis for p in req.positionen)
    mwst  = netto * req.mwst_prozent / 100
    brutto = netto + mwst

    tot_col_w = [BODY_W - 50 * mm, 50 * mm]
    tot_data = [
        [Paragraph("Gesamtbetrag netto",         s["tot_lbl"]), Paragraph(_eur(netto),  s["tot_val"])],
        [Paragraph(f"Umsatzsteuer {req.mwst_prozent:.0f}%", s["tot_lbl"]), Paragraph(_eur(mwst),   s["tot_val"])],
        [Paragraph("Gesamtbetrag brutto",        s["tot_bold"]),Paragraph(_eur(brutto), s["tot_bold"])],
    ]
    tot_tbl = Table(tot_data, colWidths=tot_col_w)
    tot_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEABOVE",     (0, 2), (-1, 2), 0.8, _HEAD),
        ("LINEBELOW",     (0, 2), (-1, 2), 0.8, _HEAD),
    ]))
    story.append(tot_tbl)
    story.append(Spacer(1, 10 * mm))

    # ── Closing ───────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Für Rückfragen stehen wir Ihnen jederzeit gerne zur Verfügung.<br/>"
        "Wir bedanken uns sehr für Ihr Vertrauen.",
        s["closing"],
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Mit freundlichen Grüßen", s["closing"]))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(req.ansprechpartner, s["bold"]))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _eur(amount: float) -> str:
    """Format as German-style EUR string: 1.234,56 EUR"""
    return f"{amount:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")
