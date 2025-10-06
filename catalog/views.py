
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Platform, TrackingParamSet, OfferNetwork, Offer, OfferLink, OfferNetwork as Network
from .forms import PlatformForm, TrackingParamSetForm , OfferLinkWithOfferForm
from django import forms
from django.db.models import Prefetch
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib import messages
from .models import PersonalizedTag, Platform
from .forms import PersonalizedTagForm
import pandas as pd




def staff_only(user):
    return user.is_staff

@login_required
def platform_list(request):
    platforms = Platform.objects.filter(created_by=request.user).order_by("name")
    return render(request, "catalog/platform_list.html", {"platforms": platforms})

@login_required
def platform_create(request):
    if request.method == "POST":
        form = PlatformForm(request.POST)
        if form.is_valid():
            platform = form.save(commit=False)
            platform.created_by = request.user  # assign current user
            platform.save()
            messages.success(request, "Platform added successfully.")
            return redirect("catalog:platform_list")
    else:
        form = PlatformForm()
    
    return render(request, "catalog/platform_form.html", {"form": form, "edit": False})

@login_required
def platform_edit(request, pk):
    obj = get_object_or_404(Platform, pk=pk, created_by=request.user)  # user-specific
    if request.method == "POST":
        form = PlatformForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Platform updated successfully.")
            return redirect("catalog:platform_list")
    else:
        form = PlatformForm(instance=obj)
    
    return render(request, "catalog/platform_form.html", {"form": form, "edit": True, "obj": obj})

@login_required
def platform_delete(request, pk):
    obj = get_object_or_404(Platform, pk=pk, created_by=request.user)

    if request.method == "POST":
        if "confirm" in request.POST:
            obj.delete()
            messages.success(request, f"Platform '{obj.name}' deleted successfully.")
            return redirect("catalog:platform_list")
        else:
            messages.info(request, "Deletion canceled.")
            return redirect("catalog:platform_list")

    return render(
        request,
        "catalog/confirm_delete.html",
        {
            "object": obj.name,
            "cancel_url": reverse("catalog:platform_list"),
            "extra_message": "This will remove the platform and all related tags & params also.",
        },
    )


# ---------- Admin-only OfferLink CRUD ----------
@login_required
@user_passes_test(staff_only)
def upload_offer_links(request):
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]

        try:
            import pandas as pd

            df = pd.read_excel(excel_file)
            df = df.dropna(subset=['network', 'offer', 'url'])

            # Fetch existing items
            existing_networks = {n.name: n for n in OfferNetwork.objects.all()}
            existing_offers = {(o.network.name, o.name): o for o in Offer.objects.select_related('network')}
            existing_links = {(l.offer.network.name, l.offer.name): l for l in OfferLink.objects.select_related('offer__network')}

            new_networks = []
            new_offers = []
            new_links = []

            created_networks = 0
            created_offers = 0
            created_links = 0
            updated_links = 0
            skipped_rows = 0

            # 1️⃣ Create in-memory lists
            for _, row in df.iterrows():
                network_name = str(row['network']).strip()
                offer_name = str(row['offer']).strip()
                url = str(row['url']).strip()
                is_active = bool(row.get('is_active', True))

                if not all([network_name, offer_name, url]):
                    skipped_rows += 1
                    continue

                # --- NETWORK ---
                network_obj = existing_networks.get(network_name)
                if not network_obj:
                    network_obj = OfferNetwork(name=network_name)
                    new_networks.append(network_obj)
                    existing_networks[network_name] = network_obj

                # --- OFFER ---
                offer_key = (network_name, offer_name)
                offer_obj = existing_offers.get(offer_key)
                if not offer_obj:
                    offer_obj = Offer(network=network_obj, name=offer_name)
                    new_offers.append(offer_obj)
                    existing_offers[offer_key] = offer_obj

                # --- LINK ---
                link_key = (network_name, offer_name)
                link_obj = existing_links.get(link_key)

                if link_obj:
                    if link_obj.url != url or link_obj.is_active != is_active:
                        link_obj.url = url
                        link_obj.is_active = is_active
                        link_obj.save(update_fields=['url', 'is_active'])
                        updated_links += 1
                else:
                    link_obj = OfferLink(offer=offer_obj, url=url, is_active=is_active, created_by=request.user)
                    new_links.append(link_obj)
                    existing_links[link_key] = link_obj

            # 2️⃣ Save new networks first
            if new_networks:
                OfferNetwork.objects.bulk_create(new_networks, ignore_conflicts=True)
                created_networks = len(new_networks)

                # refresh from DB (to get IDs)
                saved_networks = OfferNetwork.objects.filter(
                    name__in=[n.name for n in new_networks]
                )
                for n in saved_networks:
                    existing_networks[n.name] = n

            # 3️⃣ Save new offers next
            if new_offers:
                for o in new_offers:
                    o.network = existing_networks[o.network.name]  # now has ID
                Offer.objects.bulk_create(new_offers, ignore_conflicts=True)
                created_offers = len(new_offers)

                # refresh offers with IDs
                saved_offers = Offer.objects.select_related('network').filter(
                    name__in=[o.name for o in new_offers]
                )
                for o in saved_offers:
                    existing_offers[(o.network.name, o.name)] = o

            # 4️⃣ Finally, save new links
            if new_links:
                for l in new_links:
                    l.offer = existing_offers[(l.offer.network.name, l.offer.name)]
                OfferLink.objects.bulk_create(new_links, ignore_conflicts=True)
                created_links = len(new_links)

            messages.success(request, f"✅ Excel processed successfully! "
                                      f"{created_networks} networks, "
                                      f"{created_offers} offers, "
                                      f"{created_links} new links, "
                                      f"{updated_links} updated, "
                                      f"{skipped_rows} skipped.")

        except Exception as e:
            messages.error(request, f"❌ Error processing Excel: {e}")

        return redirect('catalog:offer_index')

    return render(request, "catalog/offer_index.html", {
        "all_networks": OfferNetwork.objects.all()
    })

from django.db.models import Q, Prefetch

@login_required
@user_passes_test(staff_only)
def offer_index(request):
    net_id = request.GET.get("network") or ""
    offer_q = request.GET.get("offer") or ""
    status = request.GET.get("status") or ""  # "", "active", "inactive"

    # Base link filter
    link_filter = Q()
    if status == "active":
        link_filter = Q(is_active=True)
    elif status == "inactive":
        link_filter = Q(is_active=False)

    # Prefetch links with filter
    prefetch_links = Prefetch(
        'links',
        queryset=OfferLink.objects.filter(link_filter).select_related('offer'),
        to_attr='filtered_links'
    )

    # Base offer filter
    offers_qs = Offer.objects.all().select_related('network').prefetch_related(prefetch_links)
    if offer_q:
        offers_qs = offers_qs.filter(name__icontains=offer_q)

    # Only keep offers that have links if status filter is applied
    if status in ('active', 'inactive'):
        offers_qs = offers_qs.filter(links__is_active=(status == 'active'))

    # Prefetch offers per network
    networks_qs = OfferNetwork.objects.all().prefetch_related(
        Prefetch('offers', queryset=offers_qs, to_attr='filtered_offers')
    )

    # Optional network filter
    if net_id:
        networks_qs = networks_qs.filter(id=net_id)

    # If filters applied, remove networks with no filtered offers
    networks_qs = [net for net in networks_qs if getattr(net, 'filtered_offers', [])]

    # Order networks
    networks_qs.sort(key=lambda x: x.name)

    return render(request, "catalog/offer_index.html", {
        "networks": networks_qs,
        "all_networks": OfferNetwork.objects.order_by('name'),
    })

class OfferLinkForm(forms.ModelForm):
    class Meta:
        model = OfferLink
        fields = ["offer","url","is_active"]

@login_required
@user_passes_test(staff_only)
def offer_link_add(request):
    if request.method == "POST":
        form = OfferLinkWithOfferForm(request.POST)
        if form.is_valid():
            network = form.cleaned_data["network"]
            offer_name = form.cleaned_data["offer_name"]
            # find or create Offer
            offer, _ = Offer.objects.get_or_create(
                network=network, name=offer_name
            )
            # Check if an OfferLink for this offer already exists
            if OfferLink.objects.filter(offer=offer).exists():
                messages.error(request, "An offer link for this offer already exists.")
                return render(request, "catalog/offer_link_form.html", {"form": form})
            link = form.save(commit=False)
            link.offer = offer
            link.save()
            messages.success(request, "Offer & link saved.")
            return redirect("catalog:offer_index")
    else:
        form = OfferLinkWithOfferForm()
    return render(request, "catalog/offer_link_form.html", {"form": form})

@login_required
@user_passes_test(staff_only)
def offer_link_edit(request, pk):
    obj = get_object_or_404(OfferLink, pk=pk)
    if request.method == "POST":
        form = OfferLinkWithOfferForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer link updated.")
            return redirect("catalog:offer_index")
    else:
        form = OfferLinkWithOfferForm(instance=obj)
    return render(request, "catalog/offer_link_form.html", {"form": form, "edit": True})

@login_required
@user_passes_test(staff_only)
def offer_link_delete(request, pk):
    obj = get_object_or_404(OfferLink, pk=pk)

    if request.method == "POST":
        if "confirm" in request.POST:
            obj.delete()
            messages.success(request, f"Offer '{obj.url}' deleted successfully.")
            return redirect("catalog:offer_index")
        else:
            messages.info(request, "Deletion canceled.")
            return redirect("catalog:offer_index")

    return render(
        request,
        "catalog/confirm_delete.html",
        {
            "object": obj.url,
            "cancel_url": reverse("catalog:offer_index"),
            "extra_message": "Deleting this link will remove from its offer.",
        },
    )



# ---------- Admin-only Network CRUD ----------


class OfferNetworkForm(forms.ModelForm):
    class Meta:
        model = OfferNetwork
        fields = ["name"]

@login_required
@user_passes_test(staff_only)
def offer_network_add(request):
    if request.method == "POST":
        form = OfferNetworkForm(request.POST)
        if form.is_valid():
            ol = form.save(commit=False)
            ol.created_by = request.user
            ol.save()
            messages.success(request, "Network created.")
            return redirect("catalog:offer_index")
    else:
        form = OfferNetworkForm()
    return render(request, "catalog/offer_network_form.html", {"form": form})

@login_required
@user_passes_test(staff_only)
def offer_network_edit(request,pk):
    obj = get_object_or_404(Network, pk=pk)
    if request.method == "POST":
        form = OfferNetworkForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Network updated.")
            return redirect("catalog:offer_index")
    else:
        form = OfferNetworkForm(instance=obj)
    return render(request, "catalog/offer_network_form.html", {"form": form, "edit": True})

@login_required
@user_passes_test(staff_only)
def offer_network_delete(request, pk):
    obj = get_object_or_404(Network, pk=pk)

    if request.method == "POST":
        if "confirm" in request.POST:
            obj.delete()
            messages.success(request, f"Network '{obj.name}' deleted successfully.")
            return redirect("catalog:offer_index")
        else:
            messages.info(request, "Deletion canceled.")
            return redirect("catalog:offer_index")

    return render(
        request,
        "catalog/confirm_delete.html",
        {
            "object": obj.name,  # what to display in bold
            "cancel_url": reverse("catalog:offer_index"),
            "extra_message": "Deleting this network will also remove all its offers and links.",
        },
    )




# ---------- Admin-only Offer CRUD ----------


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["network","name"]

@login_required
@user_passes_test(staff_only)
def offer_add(request):
    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            ol = form.save(commit=False)
            ol.created_by = request.user
            ol.save()
            messages.success(request, "Offer created.")
            return redirect("catalog:offer_index")
    else:
        form = OfferForm()
    return render(request, "catalog/offer_form.html", {"form": form})

@login_required
@user_passes_test(staff_only)
def offer_edit(request,pk):
    obj = get_object_or_404(Offer, pk=pk)
    if request.method == "POST":
        form = OfferForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Network updated.")
            return redirect("catalog:offer_index")
    else:
        form = OfferForm(instance=obj)
    return render(request, "catalog/offer_form.html", {"form": form, "edit": True})


@login_required
@user_passes_test(staff_only)
def offer_delete(request, pk):
    obj = get_object_or_404(Offer, pk=pk)

    if request.method == "POST":
        if "confirm" in request.POST:
            obj.delete()
            messages.success(request, f"Offer '{obj.name}' deleted successfully.")
            return redirect("catalog:offer_index")
        else:
            messages.info(request, "Deletion canceled.")
            return redirect("catalog:offer_index")

    return render(
        request,
        "catalog/confirm_delete.html",
        {
            "object": obj.name,
            "cancel_url": reverse("catalog:offer_index"),
            "extra_message": "Deleting this offer will remove all its associated links.",
        },
    )
    
    
import json
from django.contrib import messages

@login_required
def param_index(request):
    params = TrackingParamSet.objects.filter(created_by=request.user).order_by('-created_at')
    form = TrackingParamSetForm(request.POST or None, user=request.user)

    if request.method == 'POST':
        platform_id = request.POST.get('platform')
        platform = None
        if platform_id:
            try:
                platform = Platform.objects.get(pk=platform_id, created_by=request.user)
            except Platform.DoesNotExist:
                messages.error(request, "Invalid platform selected.")
                return redirect('catalog:param_index')

        if platform:
            # Convert params string to dict
            try:
                param_data = json.loads(request.POST.get('params', '{}'))
            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format in parameters.")
                return redirect('catalog:param_index')

            # Convert checkbox value to boolean
            is_active = request.POST.get('is_active')
            is_active = True if is_active == 'on' else False

            # Check if already exists
            param_set, created = TrackingParamSet.objects.get_or_create(
                platform=platform,
                created_by=request.user,
                defaults={'params': param_data, 'is_active': is_active}
            )

            if not created:
                param_set.params = param_data
                param_set.is_active = is_active
                param_set.save()
                messages.success(request, f"Parameters for platform '{platform.name}' were updated.")
            else:
                messages.success(request, f"Parameters for platform '{platform.name}' were created.")

        return redirect('catalog:param_index')

    return render(request, 'catalog/param_index.html', {'form': form, 'params': params})


@login_required
def param_detail_json(request, pk):
    obj = get_object_or_404(TrackingParamSet, pk=pk, created_by=request.user)
    data = {
        'id': obj.pk,
        'platform': obj.platform.id if obj.platform else None,
        'params': obj.params,
        'is_active': obj.is_active,
    }
    return JsonResponse(data)

@login_required
def param_delete(request, pk):
    obj = get_object_or_404(TrackingParamSet, pk=pk, created_by=request.user)
    if request.method == 'POST':
        obj.delete()
    return redirect('catalog:param_index')


# --------------------------------- Personalized Tag---------------------------------------------------

@login_required
def personalized_tag_list(request):
    tags = PersonalizedTag.objects.filter(user=request.user).select_related("platform").order_by("platform__name")
    return render(request, "catalog/personalized_tag_list.html", {"tags": tags})

@login_required
def personalized_tag_create(request):
    if request.method == "POST":
        form = PersonalizedTagForm(request.POST,user=request.user)
        if form.is_valid():
            personalized_tag = form.save(commit=False)  # don’t save yet
            personalized_tag.user = request.user
            existing = PersonalizedTag.objects.filter(user=request.user, platform=form.cleaned_data["platform"])
            if existing.exists():
                messages.error(request, "You already have a personalized tag for this platform.")
            else:
                form.save()
                messages.success(request, "Personalized tags saved.")
            
            return redirect("catalog:personalized_tag_list")
    else:
        form = PersonalizedTagForm(user=request.user)
    return render(request, "catalog/personalized_tag_form.html", {"form": form, "edit": False})

@login_required
def personalized_tag_edit(request, pk):
    obj = get_object_or_404(PersonalizedTag, pk=pk, user=request.user)
    if request.method == "POST":
        form = PersonalizedTagForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Personalized tags updated.")
            return redirect("catalog:personalized_tag_list")
    else:
        form = PersonalizedTagForm(instance=obj, user=request.user)

    # Pass platform name directly to template
    platform_name = obj.platform.name if obj.platform else ""

    return render(
        request,
        "catalog/personalized_tag_form.html",
        {"form": form, "edit": True, "obj": obj, "platform_name": platform_name}
    )

# @login_required
# def personalized_tag_delete(request, pk):
#     obj = get_object_or_404(PersonalizedTag, pk=pk)
#     if request.method == "POST":
#         obj.delete()
#         messages.success(request, "Personalized tags deleted.")
#         return redirect("catalog:personalized_tag_list")
#     return render(request, "confirm_delete.html", {
#         "object": obj.platform.name,
#         "cancel_url": reverse("catalog:personalized_tag_list"),
#         "extra_message": "This will remove the personalized tags for this platform.",
#     })
    
@login_required
def personalized_tag_delete(request, pk):
    obj = get_object_or_404(PersonalizedTag, pk=pk, user=request.user)

    if request.method == "POST":
        if "confirm" in request.POST:
            obj.delete()
            messages.success(request, f"Personalized tag for '{obj.platform.name}' deleted successfully.")
            return redirect("catalog:personalized_tag_list")
        else:
            messages.info(request, "Deletion canceled.")
            return redirect("catalog:personalized_tag_list")

    return render(
        request,
        "catalog/confirm_delete.html",
        {
            "object": obj.platform.name,
            "cancel_url": reverse("catalog:personalized_tag_list"),
            "extra_message": "This will remove the personalized tags for this platform.",
        },
    )
    