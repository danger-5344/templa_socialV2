
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings

User = get_user_model()

class Platform(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['created_by', 'name'], name='unique_user_platform')
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            while Platform.objects.filter(created_by=self.created_by, slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TrackingParamSet(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, null=True, blank=True)
    params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tracking_params'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Params for {self.platform.name if self.platform else 'No Platform'}"

class OfferNetwork(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Offer(models.Model):
    network = models.ForeignKey(OfferNetwork, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = ('network', 'name')

    def __str__(self):
        return f"{self.network.name} — {self.name}"

class OfferLink(models.Model):
    offer = models.OneToOneField(
        Offer,
        on_delete=models.CASCADE,
        related_name='links'
    )
    url = models.URLField(unique=True)   # each link URL is unique in system
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.offer} | {self.url[:50]}..."
    
class PersonalizedTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personalized_tags")
    platform = models.ForeignKey("Platform", on_delete=models.CASCADE, related_name="personalized_tags")
    first_name_tag = models.CharField(max_length=100, blank=True)
    last_name_tag = models.CharField(max_length=100, blank=True)
    date_tag = models.CharField(max_length=100, blank=True)
    email_tag = models.CharField(max_length=100, blank=True)
    footer1_code = models.TextField(blank=True)
    footer2_code = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "platform"], name="unique_user_platform_tag")
        ]
        verbose_name = "Personalized Tag Set"
        verbose_name_plural = "Personalized Tag Sets"

    def __str__(self):
        return f"Tags for {self.platform.name}"



