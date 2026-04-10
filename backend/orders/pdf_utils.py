# backend/orders/pdf_utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def render_order_pdf(order, kind: str = "client") -> bytes:
    """
    kind: 'client' o 'admin' (admin puede incluir internal_notes)
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    y = height - 50
    line = 14

    def draw(label, value):
        nonlocal y
        if value is None or value == "":
            return
        c.drawString(50, y, f"{label}: {value}")
        y -= line

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "RossRios — Order Summary")
    y -= (line * 2)

    c.setFont("Helvetica", 11)
    draw("Order Name", order.order_name)
    draw("Public ID", str(order.public_id))
    draw("Client", order.client_name)
    draw("Primary Email", order.primary_email)
    draw("Phone", order.phone)
    draw("Region", order.get_region_display())
    draw("Rush", order.get_rush_order_display())
    draw("Due Date", str(order.due_date))

    # supplier_pickup es lista (JSON)
    suppliers = ", ".join(order.supplier_pickup or [])
    draw("Supplier pickup", suppliers)

    draw("Delivery location", order.get_delivery_location_display())
    if order.delivery_location == "other":
        draw("Delivery other", order.delivery_location_other)

    if order.order_number:
        draw("Order Number", order.order_number)

    if order.additional_notes:
        y -= line
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Additional notes:")
        y -= line
        c.setFont("Helvetica", 11)
        for chunk in str(order.additional_notes).splitlines():
            c.drawString(60, y, chunk[:120])
            y -= line

    if kind == "admin" and order.internal_notes:
        y -= line
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Internal notes:")
        y -= line
        c.setFont("Helvetica", 11)
        for chunk in str(order.internal_notes).splitlines():
            c.drawString(60, y, chunk[:120])
            y -= line

    c.showPage()
    c.save()
    return buf.getvalue()
