from django.contrib import admin
from django.utils.html import format_html
from .models import Profile

# -------------------------
# Profile Admin
# -------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'company', 'avatar_preview')
    search_fields = ('user__username', 'display_name', 'company')
    readonly_fields = ('avatar_preview',)
    fieldsets = (
        (None, {
            'fields': ('user', 'display_name', 'company')
        }),
        ('Avatar', {
            'fields': ('avatar', 'avatar_preview'),
            'classes': ('collapse',),  # collapsible section
        }),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="100" style="border-radius:50%;" />', obj.avatar.url)
        return "No Avatar"
    avatar_preview.short_description = "Avatar Preview"

