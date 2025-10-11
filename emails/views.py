
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import EmailTemplate, TemplateUsage
from django.utils import timezone
from .forms import EmailTemplateForm, UseTemplateForm
from .utils import detect_placeholders, fill_placeholders, append_query_params
from catalog.models import PersonalizedTag, Platform, TrackingParamSet, OfferLink
from django import forms
from django.core.cache import cache
from django.core.paginator import Paginator
from django_select2.views import AutoResponseView

def home(request):
    q = request.GET.get("q", "")
    templates = EmailTemplate.objects.filter(is_public=True)

    if q:
        templates = templates.filter(
            Q(title__icontains=q) |
            Q(subject__icontains=q) |
            Q(from_name__icontains=q) |
            Q(template_id__icontains=q)   # ✅ allow search by template id
        )

    templates = templates.select_related("owner").order_by("-updated_at")

    # ✅ Pagination added (show 12 per page, no change in logic)
    paginator = Paginator(templates, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get all template IDs the current user has used
    if request.user.is_authenticated:
        used_template_ids = TemplateUsage.objects.filter(
            user=request.user,
            template__in=page_obj  # ✅ paginate-aware query
        ).values_list('template_id', flat=True)
    else:
        used_template_ids = []  # empty list for anonymous users

    return render(
        request,
        "emails/home.html",
        {
            "templates": page_obj,              # ✅ paginated queryset
            "q": q,
            "used_template_ids": used_template_ids,
            "page_obj": page_obj,               # ✅ added for pagination UI
        },
    )

@login_required
def my_templates(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "").lower()
    templates = EmailTemplate.objects.filter(owner=request.user).order_by("-updated_at")
    if q:
        templates = templates.filter(
        Q(title__icontains=q) |
        Q(subject__icontains=q) |
        Q(from_name__icontains=q) |
        Q(template_id__icontains=q)   # ✅ allow search by template id
    )
    if status:
        if status == "active":
            templates = templates.filter(is_public=True)
        elif status == "inactive":
            templates = templates.filter(is_public=False)
    # ✅ Pagination added (10 per pag)
    paginator = Paginator(templates, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "emails/my_templates.html", {"templates": page_obj, "page_obj": page_obj, "q": q,
        "status": status})

@login_required
def template_create(request):
    if request.method == "POST":
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            messages.success(request, "Template created.")
            return redirect("emails:my_templates")
    else:
        form = EmailTemplateForm()
    return render(request, "emails/template_form.html", {"form": form})

@login_required
def template_edit(request, pk):
    obj = get_object_or_404(EmailTemplate, pk=pk, owner=request.user)
    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Template updated.")
            return redirect("emails:my_templates")
    else:
        form = EmailTemplateForm(instance=obj)
    return render(request, "emails/template_form.html", {"form": form, "edit": True})

@login_required
def template_delete(request, pk):
    obj = get_object_or_404(EmailTemplate, pk=pk, owner=request.user)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Template deleted.")
        return redirect("emails:my_templates")
    return render(request, "emails/confirm_delete.html", {"object": obj})

def normalize_tag_name(tag_name: str) -> str:
    return tag_name.strip().replace("-", "_").replace(" ", "_").lower()

def record_template_usage(user, template):
    """
    Increment usage count for a user-template combination.
    """
    usage, created = TemplateUsage.objects.get_or_create(
        user=user,
        template=template,
        defaults={"used_count": 1, "last_used_at": timezone.now()}
    )

    if not created:
        # Only increment if record already exists
        usage.used_count += 1
        usage.last_used_at = timezone.now()
        usage.save(update_fields=["used_count", "last_used_at"])

class OfferLinkAutocomplete(AutoResponseView):
    def get_queryset(self):
        qs = OfferLink.objects.filter(is_active=True)
        term = self.request.GET.get("term", "")
        if term:
            # Search in the related Offer's name
            qs = qs.filter(offer__name__icontains=term)
        return qs

@login_required
def template_use(request, pk):
    tpl = get_object_or_404(EmailTemplate, pk=pk)
    detected_placeholders = detect_placeholders(tpl.body_html) + detect_placeholders(tpl.body_text)
    detected_placeholders = sorted(set(detected_placeholders))
  
    
    if not tpl.is_public and tpl.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have access to use this template.")
        return redirect("emails:home")

    form = UseTemplateForm(user=request.user, data=request.POST or None)


    if request.method == "POST" and form.is_valid():

        cleaned = form.cleaned_data.copy()
        platform = cleaned.pop("platform", None)
        offer_link = cleaned.pop("offer_link", None)
        cta_fallback_url = cleaned.pop("cta_fallback_url", "")


        try:
            tags = PersonalizedTag.objects.get(user=request.user, platform=platform, is_active=True)
        except PersonalizedTag.DoesNotExist:
            tags = None


        # Build CTA URL

        cta_url = offer_link.url if offer_link else cta_fallback_url or ""
        tracking = TrackingParamSet.objects.filter(platform=platform, is_active=True).first()
        if tracking and cta_url:
            cta_url = append_query_params(cta_url, tracking.params)


        # Map template placeholders
        tag_map = {
            "FIRST_NAME": tags.first_name_tag if tags else "{{FIRST_NAME}}",
            "LAST_NAME": tags.last_name_tag if tags else "{{LAST_NAME}}",
            "EMAIL": tags.email_tag if tags else "{{EMAIL}}",
            "DATE": tags.date_tag if tags else "{{DATE}}",
            "FOOTER1": tags.footer1_code if tags else "{{FOOTER1}}",
            "FOOTER2": tags.footer2_code if tags else "{{FOOTER2}}",
            "CTA_URL": cta_url or "{{CTA_URL}}",
        }

        filled_html = fill_placeholders(tpl.body_html, tag_map)
        filled_text = fill_placeholders(tpl.body_text, tag_map)
        usage, created = TemplateUsage.objects.get_or_create(user=request.user, template=tpl)
        usage.increment_usage()
        return render(request, "emails/use_result.html", {
            "template": tpl,
            "filled_html": filled_html,
            "filled_text": filled_text,
            "cta_url": cta_url,
            "platform": platform,
            "tracking": tracking.params if tracking else {},
            "offer_link": offer_link,
        })

    return render(request, "emails/use_form.html", {
        "template": tpl,
        "form": form,
        "detected" : detected_placeholders,
    })


def template_preview(request, pk):
    """
    Returns a safe HTML fragment for the preview modal.
    Shows subject + HTML body as stored (not processed as a Django template).
    """
    tpl = get_object_or_404(EmailTemplate, pk=pk, is_public=True)
    return render(request, "emails/preview_fragment.html", {"template": tpl})
