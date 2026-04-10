# backend/orders/tasks.py
import logging

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage

from .models import Order
from .pdf_utils import render_order_pdf

logger = logging.getLogger(__name__)


@shared_task
def ping():
    print("✅ Celery ping OK")
    return "pong"


def _dedupe_emails(*emails):
    out = []
    for e in emails:
        e = (e or "").strip()
        if e and e not in out:
            out.append(e)
    return out


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_order_emails(self, order_id: int):
    """
    Envía:
      - email al cliente (1–4 si existen) con client.pdf
      - email al admin (lista de settings.ADMIN_ORDER_EMAILS) con admin.pdf
    Reintenta si hay fallo real (SMTP, storage, etc.)
    """
    order = Order.objects.get(pk=order_id)

    # recipients cliente (1–4)
    client_recipients = _dedupe_emails(
        order.primary_email,
        order.secondary_email,
        order.tertiary_email,
        order.quaternary_email,
    )

    # recipients admin (desde settings)
    admin_recipients = list(getattr(settings, "ADMIN_ORDER_EMAILS", []) or [])
    admin_recipients = [e.strip() for e in admin_recipients if e.strip()]

    # paths (los mismos que usaste al guardar)
    base = f"order_pdfs/{order.public_id}/"
    client_path = base + "client.pdf"
    admin_path = base + "admin.pdf"

    # --- Cliente ---
    if client_recipients:
        if not default_storage.exists(client_path):
            raise FileNotFoundError(f"Client PDF not found in storage: {client_path}")

        subject = f"Order received: {order.order_name}"
        body = (
            f"Hi {order.client_name},\n\n"
            f"We received your order.\n"
            f"Order: {order.order_name}\n"
            f"Due date: {order.due_date}\n"
            f"Status: {order.get_status_display()}\n"
            f"Public ID: {order.public_id}\n\n"
            f"Thanks!"
        )

        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "orders@rossrios.local"),
            to=client_recipients,
        )

        with default_storage.open(client_path, "rb") as f:
            msg.attach("client.pdf", f.read(), "application/pdf")

        msg.send(fail_silently=False)
        logger.info("✅ Client email sent | order=%s | to=%s", order.public_id, client_recipients)
    else:
        logger.warning("Client email skipped (no recipients) | order=%s", order.public_id)

    # --- Admin ---
    if admin_recipients:
        if not default_storage.exists(admin_path):
            raise FileNotFoundError(f"Admin PDF not found in storage: {admin_path}")

        subject = f"[ADMIN] New order: {order.order_name}"
        body = (
            f"New order created.\n\n"
            f"Client: {order.client_name}\n"
            f"Primary email: {order.primary_email}\n"
            f"Order: {order.order_name}\n"
            f"Due date: {order.due_date}\n"
            f"Rush: {order.get_rush_order_display()}\n"
            f"Region: {order.get_region_display()}\n"
            f"Public ID: {order.public_id}\n"
        )

        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "orders@rossrios.local"),
            to=admin_recipients,
        )

        with default_storage.open(admin_path, "rb") as f:
            msg.attach("admin.pdf", f.read(), "application/pdf")

        msg.send(fail_silently=False)
        logger.info("✅ Admin email sent | order=%s | to=%s", order.public_id, admin_recipients)
    else:
        logger.warning("Admin email skipped (ADMIN_ORDER_EMAILS empty) | order=%s", order.public_id)

    return {"client": client_recipients, "admin": admin_recipients}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def generate_order_pdfs(self, order_id: int):
    order = Order.objects.get(pk=order_id)

    client_pdf = render_order_pdf(order, kind="client")
    admin_pdf = render_order_pdf(order, kind="admin")

    base = f"order_pdfs/{order.public_id}/"
    client_path = base + "client.pdf"
    admin_path = base + "admin.pdf"

    # overwrite limpio
    if default_storage.exists(client_path):
        default_storage.delete(client_path)
    if default_storage.exists(admin_path):
        default_storage.delete(admin_path)

    default_storage.save(client_path, ContentFile(client_pdf))
    default_storage.save(admin_path, ContentFile(admin_pdf))

    order.client_pdf_url = default_storage.url(client_path)
    order.admin_pdf_url = default_storage.url(admin_path)
    order.save(update_fields=["client_pdf_url", "admin_pdf_url", "updated_at"])

    # 🔥 NUEVO: cuando los PDFs ya existen, mandamos emails
    send_order_emails.delay(order.id)

    return {"client_pdf_url": order.client_pdf_url, "admin_pdf_url": order.admin_pdf_url}
