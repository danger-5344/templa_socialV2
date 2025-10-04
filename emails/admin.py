from django.contrib import admin
from django.utils.html import format_html
from django.core.files.base import ContentFile
from .models import EmailTemplate, TemplateUsage
from .snapshot import render_html_to_snapshot_content


class TemplateUsageInline(admin.TabularInline):  # or StackedInline for vertical view
    model = TemplateUsage
    extra = 0
    readonly_fields = ("user", "used_count", "last_used_at")
    can_delete = False
    ordering = ("-last_used_at",)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("template_id", "title", "owner", "from_name", "is_public", "thumb", "updated_at")
    list_filter = ("is_public", "created_at", "updated_at")
    search_fields = ("template_id","id", "title", "subject", "from_name", "body_html", "body_text", "owner__username")
    readonly_fields = ("id", "created_at", "updated_at",)
    fields = (
        "id",
        "owner",
        "title",
        "subject",
        "from_name",
        "is_public",
        "snapshot",
        "body_html",
        "body_text",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    actions = ["regenerate_snapshot", "make_public", "make_private"]
    inlines = [TemplateUsageInline]

    def template_id(self, obj):
        """Custom Template ID column in admin"""
        return f"TEMP-{obj.id}"
    template_id.admin_order_field = "id"   # enables sorting by DB id
    template_id.short_description = "Template ID"

    def thumb(self, obj):
        if obj.snapshot:
            return format_html('<img src="{}" style="height:40px;border-radius:6px"/>', obj.snapshot.url)
        return "-"
    thumb.short_description = "Snapshot"

    @admin.action(description="Regenerate snapshot")
    def regenerate_snapshot(self, request, queryset):
        for obj in queryset:
            content: ContentFile = render_html_to_snapshot_content(obj.body_html or "")
            obj.snapshot.save(f"template_{obj.pk}.png", content, save=True)

    @admin.action(description="Mark selected templates as PUBLIC")
    def make_public(self, request, queryset):
        queryset.update(is_public=True)

    @admin.action(description="Mark selected templates as PRIVATE")
    def make_private(self, request, queryset):
        queryset.update(is_public=False)

@admin.register(TemplateUsage)
class TemplateUsageAdmin(admin.ModelAdmin):
    list_display = ("template", "user", "used_count", "last_used_at")
    list_filter = ("template", "user")
    search_fields = ("template__title", "user__username", "user__email")
    ordering = ("-last_used_at",)
