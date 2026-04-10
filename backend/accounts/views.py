from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from .forms import SignUpForm

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # por defecto: cliente NO staff
            user.is_staff = False
            user.is_superuser = False
            user.save()

            login(request, user)
            return redirect("/make-order/")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

@require_POST
def set_region(request):
    region = request.POST.get("region")
    if region in ("CA", "US"):
        request.session["region"] = region

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)