from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import EmailTemplate
from .snapshot import render_html_to_snapshot_content
from django.core.files.base import ContentFile

import os
import logging

def _needs_snapshot(instance: EmailTemplate, old_html: str | None) -> bool:
    # Generate if missing OR body changed
    if not instance.snapshot:
        return True
    if old_html is None:
        return False
    return (instance.body_html or "").strip() != (old_html or "").strip()

@receiver(pre_save, sender=EmailTemplate)
def _cache_old_html(sender, instance: EmailTemplate, **kwargs):
    # Cache previous HTML and snapshot file
    if instance.pk:
        try:
            prev = EmailTemplate.objects.only("body_html", "snapshot").get(pk=instance.pk)
            instance._old_body_html = prev.body_html
            instance._old_snapshot = prev.snapshot
        except EmailTemplate.DoesNotExist:
            instance._old_body_html = None
            instance._old_snapshot = None
    else:
        instance._old_body_html = None
        instance._old_snapshot = None

@receiver(post_save, sender=EmailTemplate)
def generate_snapshot_after_save(sender, instance: EmailTemplate, created, **kwargs):
    try:
        old_html = getattr(instance, "_old_body_html", None)
        old_snapshot = getattr(instance, "_old_snapshot", None)

        if _needs_snapshot(instance, old_html):
            content: ContentFile = render_html_to_snapshot_content(instance.body_html or "")
            filename = f"template_{instance.pk}.png"

            # Delete old snapshot file if it exists and is different
            if old_snapshot and old_snapshot != instance.snapshot:
                try:
                    if os.path.isfile(old_snapshot.path):
                        os.remove(old_snapshot.path)
                    print(f"Deleted old snapshot file: {old_snapshot.path}")
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Failed to delete old snapshot file %s", old_snapshot.path
                    )

            # Save new snapshot
            instance.snapshot.save(filename, content, save=True)
    except Exception as e:
        # Don’t crash the request if snapshot fails; log it
        logging.getLogger(__name__).exception("Snapshot generation failed: %s", e)
