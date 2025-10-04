
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from .forms import ProfileForm
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("emails:home")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})
@login_required
def profile_modal(request):
    profile = getattr(request.user, "profile", None)
    form = ProfileForm(user=request.user, instance=profile)
    # Take return_to from GET (from base.html), fall back to referrer or home
    return_to = request.GET.get("return_to") or request.META.get("HTTP_REFERER") or reverse("emails:home")
    return render(request, "accounts/profile_fragment.html", {
        "form": form,
        "user_obj": request.user,
        "return_to": return_to,
    })

@login_required
def profile_update(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    profile = getattr(request.user, "profile", None)
    form = ProfileForm(request.POST, request.FILES, user=request.user, instance=profile)

    # compute safe return_to
    return_to = request.POST.get("return_to") or request.META.get("HTTP_REFERER") or reverse("emails:home")
    if not url_has_allowed_host_and_scheme(
        url=return_to, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return_to = reverse("emails:home")

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if form.is_valid():
        form.save()
        avatar_url = request.user.profile.avatar.url if getattr(request.user, "profile", None) and request.user.profile.avatar else ""
        if is_ajax:
            return JsonResponse({
                "ok": True,
                "redirect": return_to,
                "display_name": (request.user.profile.display_name if request.user.profile else request.user.get_full_name() or request.user.username),
                "email": request.user.email,
                "avatar_url": avatar_url,
            })
        # Non-AJAX fallback: redirect with a flash message
        messages.success(request, "Profile updated.")
        return redirect(return_to)

    # Invalid form
    if is_ajax:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    messages.error(request, "Please correct the errors.")
    return redirect(return_to)