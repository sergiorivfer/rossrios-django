import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ---------- Validadores de archivos ----------
ALLOWED_EXTENSIONS = {
    ".pdf", ".svg", ".png", ".jpg", ".jpeg", ".eps", ".psd",
    ".zip", ".doc", ".dst", ".vp3", ".jef", ".pes"
}
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 3MB


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Extension '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

def supplier_pickup_labels(self):
    m = dict(self.Supplier.choices)
    return [m.get(v, v) for v in (self.supplier_pickup or [])]


def validate_file_size(value):
    if value.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError("File too large. Max size is 3MB per file.")


def order_file_upload_to(instance, filename: str) -> str:
    # Carpeta por orden (más limpio para después PDF/email)
    return f"order_files/{instance.order.public_id}/{filename}"


class Order(models.Model):
    class Region(models.TextChoices):
        CANADA = "CA", "Canada"
        UNITED_STATES = "US", "United States"

    class RushType(models.TextChoices):
        STANDARD = "standard", "Standard"
        RUSH = "rush", "Rush"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        ON_HOLD = "on_hold", "On hold"
        IN_PRODUCTION = "in_production", "In production"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class DeliveryLocation(models.TextChoices):
        PRIMARY = "primary", "Use Primary Location"
        OTHER = "other", "Other (specify)"

    class Supplier(models.TextChoices):
        SANMAR = "sanmar", "Sanmar"
        S_AND_S = "s_and_s", "S&S"
        DEBCO = "debco", "Debco"
        NONE = "none", "None"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # quién crea la orden (cliente)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    # CA/US (selector inicial)
    region = models.CharField(max_length=2, choices=Region.choices)

    # Datos cliente (form)
    client_name = models.CharField(max_length=255)  # *
    primary_email = models.EmailField()  # *
    secondary_email = models.EmailField(blank=True, null=True)
    tertiary_email = models.EmailField(blank=True, null=True)
    quaternary_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50)  # *

    # Datos pedido (form)
    order_name = models.CharField(max_length=255)  # *
    tax_number = models.CharField(max_length=100, blank=True, null=True)

    address_line1 = models.CharField(max_length=255)  # *
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    state_province = models.CharField(max_length=120, blank=True, null=True)
    postal_code = models.CharField(max_length=30, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)

    order_name_if_applicable = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=100, blank=True, null=True)

    # Suppliers pickup (checkbox list) *
    # Guardamos lista: ["sanmar", "debco"] etc.
    supplier_pickup = models.JSONField(default=list, blank=True)

    # Rush/Standard (select) *
    rush_order = models.CharField(
        max_length=20,
        choices=RushType.choices,
        default=RushType.STANDARD,
    )

    # Due date *
    due_date = models.DateField()

    # Delivery Location *
    delivery_location = models.CharField(
        max_length=20,
        choices=DeliveryLocation.choices,
        default=DeliveryLocation.PRIMARY,
    )
    delivery_location_other = models.TextField(blank=True, null=True)

    additional_notes = models.TextField(blank=True, null=True)

    # Interno (admin)
    internal_notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PROCESSING,
    )

    client_pdf_url = models.URLField(blank=True, null=True)
    admin_pdf_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        errors = {}

        # due_date no puede ser pasado
        if self.due_date and self.due_date < timezone.localdate():
            errors["due_date"] = "Due date cannot be in the past."

        # Delivery Location: si es OTHER, exigir texto
        if self.delivery_location == self.DeliveryLocation.OTHER:
            if not self.delivery_location_other or not self.delivery_location_other.strip():
                errors["delivery_location_other"] = "Required when Delivery Location is 'Other'."

        # Supplier pickup: debe ser lista con al menos 1
        if not isinstance(self.supplier_pickup, list) or len(self.supplier_pickup) == 0:
            errors["supplier_pickup"] = "Select at least one supplier (or None)."
        else:
            allowed = {c.value for c in self.Supplier}
            invalid = [v for v in self.supplier_pickup if v not in allowed]
            if invalid:
                errors["supplier_pickup"] = f"Invalid supplier value(s): {', '.join(invalid)}"

            if self.Supplier.NONE in self.supplier_pickup and len(self.supplier_pickup) > 1:
                errors["supplier_pickup"] = "'None' cannot be combined with other suppliers."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.order_name} ({self.public_id})"


class OrderFile(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(
        upload_to=order_file_upload_to,
        validators=[validate_file_extension, validate_file_size],
    )

    # estos 2 los autocompletamos para no llenarlos manual
    original_name = models.CharField(max_length=255, blank=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_order_files",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # máximo 6 archivos por orden (como el form real)
        if self.order_id and not self.pk:
            existing = self.__class__.objects.filter(order_id=self.order_id).count()
            if existing >= 6:
                raise ValidationError({"file": "Max 6 files per order."})

    def save(self, *args, **kwargs):
        if self.file:
            if not self.original_name:
                self.original_name = os.path.basename(self.file.name)
            try:
                self.size_bytes = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or str(self.pk)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=30, choices=Order.Status.choices)
    new_status = models.CharField(max_length=30, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
    )
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_name}: {self.old_status} -> {self.new_status}"
