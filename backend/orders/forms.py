# backend/orders/forms.py
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Order, validate_file_extension, validate_file_size


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [super().clean(d, initial) for d in data]
        return [super().clean(data, initial)]


class OrderCreateForm(forms.ModelForm):
    supplier_pickup = forms.MultipleChoiceField(
        choices=Order.Supplier.choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Supplier pickup",
    )

    files = MultipleFileField(required=False, label="Files")

    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )

    class Meta:
        model = Order
        fields = [
            "region",
            "client_name",
            "primary_email",
            "secondary_email",
            "tertiary_email",
            "quaternary_email",
            "phone",
            "order_name",
            "tax_number",
            "address_line1",
            "address_line2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "order_name_if_applicable",
            "order_number",
            "supplier_pickup",
            "rush_order",
            "due_date",
            "delivery_location",
            "delivery_location_other",
            "additional_notes",
        ]

    def clean_due_date(self):
        d = self.cleaned_data["due_date"]
        today = timezone.localdate()
        if d < today:
            raise forms.ValidationError("Due date cannot be in the past.")
        return d

    def clean_supplier_pickup(self):
        values = self.cleaned_data.get("supplier_pickup") or []
        if not values:
            raise forms.ValidationError("Select at least one supplier (or None).")
        if Order.Supplier.NONE in values and len(values) > 1:
            raise forms.ValidationError("'None' cannot be combined with other suppliers.")
        return values

    def clean_files(self):
        files = self.cleaned_data.get("files") or []

        # opcional: límite de cantidad
        if len(files) > 10:
            raise forms.ValidationError("Max 10 files per order.")

        for f in files:
            try:
                validate_file_extension(f)
                validate_file_size(f)
            except DjangoValidationError as e:
                raise forms.ValidationError(e.messages)

        return files

    def clean(self):
        cleaned = super().clean()
        delivery_location = cleaned.get("delivery_location")
        other = (cleaned.get("delivery_location_other") or "").strip()

        if delivery_location == Order.DeliveryLocation.OTHER and not other:
            self.add_error("delivery_location_other", "Required when Delivery Location is 'Other'.")
        return cleaned
