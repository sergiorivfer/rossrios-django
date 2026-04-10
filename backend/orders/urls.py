# backend/orders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("make-order/", views.make_order, name="make_order"),
    path("order-status/", views.order_status, name="order_status"),  # listado
    path("order-status/<uuid:public_id>/", views.order_detail, name="order_detail"),  # detalle
]

urlpatterns += [
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/orders/", views.staff_orders, name="staff_orders"),
    path("staff/calendar/", views.staff_calendar, name="staff_calendar"),
    path("staff/orders/<uuid:public_id>/", views.staff_order_detail, name="staff_order_detail"),
]
