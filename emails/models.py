
from django.db import models
from django.contrib.auth import get_user_model
from catalog.models import Platform
import uuid
User = get_user_model()

class EmailTemplate(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="templates")
    template_id = models.CharField(
        max_length=12, 
        unique=True, 
        editable=False, 
        db_index=True, 
        help_text="Unique ID for searching this template."
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True)
    from_name = models.CharField(max_length=100, blank=True, help_text="Enter Form Name")
    body_html = models.TextField(help_text="Use {{placeholders}} for personalized fields.")
    body_text = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    snapshot = models.ImageField(
        upload_to="snapshots/", 
        null=True, blank=True,
        help_text="Upload a thumbnail/preview image for the template."
    )
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.template_id:
            # Generate short unique ID (first 8 chars of UUID4, can be tuned)
            self.template_id = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.template_id})"
        
class TemplateUsage(models.Model):
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name="usages"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="template_usages"
    )
    used_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("template", "user")
        ordering = ["-last_used_at"]

    def increment_usage(self):
        self.used_count += 1
        self.save(update_fields=["used_count", "last_used_at"])

    def __str__(self):
        return f"{self.user} used {self.template} ({self.used_count}x)"