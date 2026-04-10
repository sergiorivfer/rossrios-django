# backend/orders/views.py
import calendar
from datetime import date
from celery import chain

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.db import transaction

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Order, OrderFile
from .forms import OrderCreateForm


@login_required
def make_order(request):
    # si es staff, fuera de la vista de cliente
    if request.user.is_staff:
        return redirect("/admin/")

    if request.method == "POST":
        form = OrderCreateForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.customer = request.user

                # ✅ ESTA es la línea clave de Fase 6.1:
                # siempre guardamos la región seleccionada (session/dominio)
                order.region = getattr(request, "region", order.region) or "CA"

                order.save()  # ✅ SOLO UNA VEZ (crea la orden)

                # guardar archivos
                for f in form.cleaned_data.get("files", []):
                    of = OrderFile(
                        order=order,
                        file=f,
                        original_name=f.name,
                        size_bytes=f.size,
                        uploaded_by=request.user,
                    )
                    of.full_clean()  # valida extensión/tamaño
                    of.save()

            # ✅ Encolar tasks SOLO cuando ya se guardó todo en DB
            def enqueue_jobs():
                # Si ya tienes las dos tasks (fase 4 completa)
                chain(
                    generate_order_pdfs.s(order.id),
                    send_order_emails.s(order.id),
                ).delay()

                # Si por ahora solo quieres PDFs, usa esto:
                # generate_order_pdfs.delay(order.id)

            transaction.on_commit(enqueue_jobs)

            return redirect("order_detail", public_id=order.public_id)

    else:
        # ✅ pre-llenar region por selector/session
        form = OrderCreateForm(initial={"region": getattr(request, "region", "CA")})

    return render(request, "orders/make_order.html", {"form": form})


@login_required
def order_status(request):
    # cliente ve solo lo suyo
    qs = Order.objects.filter(customer=request.user).order_by("-created_at")
    return render(request, "orders/order_status.html", {"orders": qs})


@login_required
def order_detail(request, public_id):
    order = get_object_or_404(Order, public_id=public_id, customer=request.user)
    return render(request, "orders/order_detail.html", {"order": order})

@staff_member_required
def staff_dashboard(request):
    return render(
        request,
        "orders/staff/dashboard.html",
        {
            "admin_orders_url": reverse("admin:orders_order_changelist"),
        },
    )


@staff_member_required
def staff_orders(request):
    qs = (
        Order.objects.all()
        .order_by("-created_at")
    )

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    region = (request.GET.get("region") or "").strip()

    if q:
        qs = qs.filter(
            Q(order_name__icontains=q)
            | Q(client_name__icontains=q)
            | Q(primary_email__icontains=q)
            | Q(public_id__icontains=q)
            | Q(order_number__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    if region:
        qs = qs.filter(region=region)

    return render(
        request,
        "orders/staff/orders_list.html",
        {
            "orders": qs,
            "q": q,
            "status": status,
            "region": region,
            "status_choices": Order.Status.choices,
            "region_choices": Order.Region.choices,
        },
    )


@staff_member_required
def staff_calendar(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    orders = (
        Order.objects.filter(due_date__range=(first_day, last_day))
        .order_by("due_date", "created_at")
    )

    by_day = {}
    for o in orders:
        by_day.setdefault(o.due_date.day, []).append(o)

    weeks = calendar.monthcalendar(year, month)

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    return render(
        request,
        "orders/staff/calendar.html",
        {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "weeks": weeks,
            "by_day": by_day,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
        },
    )


@staff_member_required
def staff_order_detail(request, public_id):
    order = get_object_or_404(Order, public_id=public_id)
    admin_change_url = reverse("admin:orders_order_change", args=[order.pk])

    return render(
        request,
        "orders/staff/order_detail.html",
        {
            "order": order,
            "admin_change_url": admin_change_url,
        },
    )

