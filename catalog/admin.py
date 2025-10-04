from django.contrib import admin
from .models import Platform, TrackingParamSet, OfferNetwork, Offer, OfferLink, PersonalizedTag

# -------------------------
# TrackingParamSet Inline (Compact)
# -------------------------
class TrackingParamSetInline(admin.StackedInline):
    model = TrackingParamSet
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fields = ('params', 'is_active', 'created_by', 'created_at', 'updated_at')
    show_change_link = True
    can_delete = True
    verbose_name_plural = "Tracking Params"
    classes = ('collapse',)  # Optional: collapsible to reduce clutter

class PersonalizedTagInline(admin.StackedInline):
    model = PersonalizedTag
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'user')
    fields = ('user', 'first_name_tag', 'last_name_tag', 'date_tag', 'footer1_code', 'footer2_code', 'is_active', 'created_at', 'updated_at')
    show_change_link = True
    can_delete = True
    verbose_name_plural = "Personalized Tags"
    classes = ('collapse',)


# -------------------------
# Platform Admin (Interactive)
# -------------------------
@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by')
    list_display_links = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug', 'created_by__username')
    list_filter = ('created_by',)
    ordering = ('name',)
    inlines = [TrackingParamSetInline, PersonalizedTagInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# TrackingParamSet Admin (Interactive)
# -------------------------
@admin.register(TrackingParamSet)
class TrackingParamSetAdmin(admin.ModelAdmin):
    list_display = ('platform', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'platform', 'created_by')
    search_fields = ('platform__name', 'params')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    list_display_links = ('platform',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# PersonalizedTag Admin (Interactive)
# -------------------------
@admin.register(PersonalizedTag)
class PersonalizedTagAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'platform', 'user')
    search_fields = ('platform__name',)
    readonly_fields = ('created_at', 'updated_at', 'user')
    list_display_links = ('platform',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# OfferNetwork Admin
# -------------------------
@admin.register(OfferNetwork)
class OfferNetworkAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# -------------------------
# OfferLink Inline (Compact)
# -------------------------
class OfferLinkInline(admin.TabularInline):
    model = OfferLink
    extra = 0
    min_num = 0
    max_num = 1
    readonly_fields = ('updated_at', 'created_by')
    fields = ('url', 'is_active', 'created_by', 'updated_at')
    show_change_link = True
    classes = ('collapse',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)


# -------------------------
# Offer Admin (Interactive)
# -------------------------
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'network')
    search_fields = ('name', 'network__name')
    list_filter = ('network',)
    inlines = [OfferLinkInline]
    list_display_links = ('name', 'network')
