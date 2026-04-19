import io
from pathlib import Path
import qrcode
from fpdf import FPDF
from models.models import Table, Order, Item
from core.config import settings

_FONTS_DIR = Path(__file__).parent.parent / "fonts"
_FONT = str(_FONTS_DIR / "DejaVuSans.ttf")
_FONT_BOLD = str(_FONTS_DIR / "DejaVuSans-Bold.ttf")
_LINE = "─" * 38


class _ReceiptPDF(FPDF):
    def __init__(self):
        super().__init__(format=(105, 148))  # A6 in mm
        self.add_font("dv", fname=_FONT)
        self.add_font("dv", style="B", fname=_FONT_BOLD)
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(auto=True, margin=10)


def build_receipt(table: Table, orders: list[Order], items: dict[int, Item]) -> bytes:
    pdf = _ReceiptPDF()
    pdf.add_page()
    W = pdf.w - 20  # usable width

    def line(text="", size=9, bold=False, align="L", h=5):
        pdf.set_font("dv", style="B" if bold else "", size=size)
        pdf.cell(W, h, text=text, align=align, new_x="LMARGIN", new_y="NEXT")

    def separator():
        line(_LINE, size=8, h=4)

    # ── Header ───────────────────────────────────────────────────────────────
    line("BAR POS", size=16, bold=True, align="C", h=9)
    separator()

    # Table info
    pdf.set_font("dv", size=9)

    # table name are given by barmen. might contain unapropriate name to print
    # pdf.cell(W * 0.6, 5, text=f"Table: {table.table_name}", new_x="RIGHT", new_y="TOP")
    # pdf.cell(W * 0.4, 5, text=f"# {table.id}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(W, 5, text=f"Table №{table.id}", align="L", new_x="LMARGIN", new_y="NEXT")

    line(f"Opened: {table.created_at.strftime('%d.%m.%Y  %H:%M')}", size=8, h=5)
    if table.closed_at:
        line(f"Closed: {table.closed_at.strftime('%d.%m.%Y  %H:%M')}", size=8, h=5)

    separator()

    # ── Column headers ────────────────────────────────────────────────────────
    C = [W * 0.50, W * 0.10, W * 0.20, W * 0.20]
    pdf.set_font("dv", style="B", size=8)
    for text, w, align in [("Name", C[0], "L"), ("Amount", C[1], "C"),
                            ("Price", C[2], "R"), ("Total", C[3], "R")]:
        pdf.cell(w, 5, text=text, align=align, new_x="RIGHT", new_y="TOP")
    pdf.ln(5)
    separator()

    # ── Order rows ────────────────────────────────────────────────────────────
    total = 0.0
    pdf.set_font("dv", size=9)
    for order in orders:
        item = items.get(order.item_id)
        name = (item.name if item else f"item #{order.item_id}")[:26]
        subtotal = order.quantity * order.price
        total += subtotal

        pdf.cell(C[0], 6, text=name, new_x="RIGHT", new_y="TOP")
        pdf.cell(C[1], 6, text=f"{order.quantity:g}", align="C", new_x="RIGHT", new_y="TOP")
        pdf.cell(C[2], 6, text=f"{order.price:.2f}", align="R", new_x="RIGHT", new_y="TOP")
        pdf.cell(C[3], 6, text=f"{subtotal:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    separator()

    # ── Total ─────────────────────────────────────────────────────────────────
    pdf.set_font("dv", style="B", size=11)
    pdf.cell(W - C[3], 7, text="Total:", new_x="RIGHT", new_y="TOP")
    pdf.cell(C[3], 7, text=f"{total:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    separator()

    # ── Footer ────────────────────────────────────────────────────────────────
    status = "Closed ✓" if table.status == "Closed" else "Active (opened)"
    line(f"Status: {status}", size=8, h=5)
    pdf.ln(2)
    line("Thanks for visit!", size=8, align="C", h=5)

    receipt_qr = settings.receipt_qr
    receipt_qr_title = settings.receipt_qr_title
    if receipt_qr:
        pdf.ln(3)
        qr = qrcode.make(receipt_qr)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        qr_size = 25
        pdf.image(buf, x=(pdf.w - qr_size) / 2, w=qr_size)
        if receipt_qr_title:
            line(receipt_qr_title, size=7, align="C", h=4)

    return bytes(pdf.output())
