import logging
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


# ----------------------
# Create / Update Profile
# ----------------------
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure a Profile exists for each User."""
    try:
        if created:
            Profile.objects.create(
                user=instance,
                display_name=(instance.get_full_name() or instance.username)
            )
        else:
            Profile.objects.get_or_create(
                user=instance,
                defaults={"display_name": (instance.get_full_name() or instance.username)}
            )
    except Exception as e:
        logging.getLogger(__name__).error("Error creating/updating profile: %s", e)


# ----------------------
# Avatar Handling
# ----------------------
@receiver(pre_save, sender=Profile)
def cache_old_avatar(sender, instance, **kwargs):
    """
    Cache the previous avatar before saving, to delete later if replaced.
    """
    if not instance.pk:
        instance._old_avatar = None
        return

    try:
        prev = Profile.objects.only("avatar").get(pk=instance.pk)
        # Ensure we only store FileField object if it exists
        instance._old_avatar = prev.avatar if prev.avatar else None
    except Profile.DoesNotExist:
        instance._old_avatar = None


@receiver(post_save, sender=Profile)
def delete_old_avatar_after_save(sender, instance, created, **kwargs):
    """
    Delete the old avatar if it exists and is different from the new one.
    Safe for Cloudinary or local storage.
    """
    try:
        old_avatar = getattr(instance, "_old_avatar", None)
        new_avatar = instance.avatar

        if old_avatar and old_avatar != new_avatar:
            old_avatar.delete(save=False)
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to delete old avatar: %s", e)


@receiver(post_delete, sender=Profile)
def delete_avatar_on_delete(sender, instance, **kwargs):
    """Delete avatar file when profile is deleted."""
    try:
        if instance.avatar:
            instance.avatar.delete(save=False)
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to delete avatar after profile delete: %s", e)
