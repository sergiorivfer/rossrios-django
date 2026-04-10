from django import forms
from django.contrib import admin
from django.forms import CheckboxSelectMultiple

from .models import Order, OrderFile, OrderStatusHistory


class OrderAdminForm(forms.ModelForm):
    supplier_pickup = forms.MultipleChoiceField(
        choices=Order.Supplier.choices,
        widget=CheckboxSelectMultiple,
        required=True,
        label="Supplier pickup",
        help_text="Select at least one supplier (or None).",
    )

    class Meta:
        model = Order
        fields = "__all__"

    def clean_supplier_pickup(self):
        values = self.cleaned_data.get("supplier_pickup") or []
        if not values:
            raise forms.ValidationError("Select at least one supplier (or None).")
        if Order.Supplier.NONE in values and len(values) > 1:
            raise forms.ValidationError("'None' cannot be combined with other suppliers.")
        return values


class OrderFileInline(admin.TabularInline):
    model = OrderFile
    extra = 1


class OrderStatusInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ("old_status", "new_status", "changed_by", "note", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    inlines = [OrderFileInline, OrderStatusInline]

    list_display = ("order_name", "client_name", "region", "rush_order", "due_date", "status", "created_at")
    list_filter = ("region", "rush_order", "status")
    search_fields = ("order_name", "client_name", "primary_email", "order_number")
    readonly_fields = ("public_id", "created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "due_date"

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_status = Order.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        if old_status and old_status != obj.status:
            OrderStatusHistory.objects.create(
                order=obj,
                old_status=old_status,
                new_status=obj.status,
                changed_by=request.user,
                note="Changed in admin",
            )


@admin.register(OrderFile)
class OrderFileAdmin(admin.ModelAdmin):
    list_display = ("order", "original_name", "size_bytes", "uploaded_by", "created_at")
    search_fields = ("original_name",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("old_status", "new_status")
