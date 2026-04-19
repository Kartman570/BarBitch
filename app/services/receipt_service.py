from pathlib import Path
from fpdf import FPDF
from models.models import Table, Order, Item

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
    pdf.cell(W * 0.6, 5, text=f"Стол: {table.table_name}", new_x="RIGHT", new_y="TOP")
    pdf.cell(W * 0.4, 5, text=f"# {table.id}", align="R", new_x="LMARGIN", new_y="NEXT")

    line(f"Открыт: {table.created_at.strftime('%d.%m.%Y  %H:%M')}", size=8, h=5)
    if table.closed_at:
        line(f"Закрыт: {table.closed_at.strftime('%d.%m.%Y  %H:%M')}", size=8, h=5)

    separator()

    # ── Column headers ────────────────────────────────────────────────────────
    C = [W * 0.50, W * 0.10, W * 0.20, W * 0.20]
    pdf.set_font("dv", style="B", size=8)
    for text, w, align in [("Наименование", C[0], "L"), ("Кол", C[1], "C"),
                            ("Цена", C[2], "R"), ("Итого", C[3], "R")]:
        pdf.cell(w, 5, text=text, align=align, new_x="RIGHT", new_y="TOP")
    pdf.ln(5)
    separator()

    # ── Order rows ────────────────────────────────────────────────────────────
    total = 0.0
    pdf.set_font("dv", size=9)
    for order in orders:
        item = items.get(order.item_id)
        name = (item.name if item else f"Позиция #{order.item_id}")[:26]
        subtotal = order.quantity * order.price
        total += subtotal

        pdf.cell(C[0], 6, text=name, new_x="RIGHT", new_y="TOP")
        pdf.cell(C[1], 6, text=f"{order.quantity:g}", align="C", new_x="RIGHT", new_y="TOP")
        pdf.cell(C[2], 6, text=f"{order.price:.2f}", align="R", new_x="RIGHT", new_y="TOP")
        pdf.cell(C[3], 6, text=f"{subtotal:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    separator()

    # ── Total ─────────────────────────────────────────────────────────────────
    pdf.set_font("dv", style="B", size=11)
    pdf.cell(W - C[3], 7, text="ИТОГО:", new_x="RIGHT", new_y="TOP")
    pdf.cell(C[3], 7, text=f"{total:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    separator()

    # ── Footer ────────────────────────────────────────────────────────────────
    status = "Закрыт ✓" if table.status == "Closed" else "Активный (не закрыт)"
    line(f"Статус: {status}", size=8, h=5)
    pdf.ln(2)
    line("Спасибо за визит!", size=8, align="C", h=5)

    return bytes(pdf.output())
