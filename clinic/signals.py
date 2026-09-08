from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from clinic.models import Appointment, SiteBlock
from clinic.services.keycrm_sync import sync_appointment_created, sync_appointment_status
from clinic.services.notifications import notify_new_appointment


@receiver(pre_save, sender=Appointment)
def appointment_remember_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._keycrm_old_status = None
        return
    instance._keycrm_old_status = (
        Appointment.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    )


@receiver(post_save, sender=Appointment)
def appointment_created(sender, instance, created, **kwargs):
    if created:
        notify_new_appointment(instance)
        appointment_id = instance.pk
        transaction.on_commit(lambda: sync_appointment_created(appointment_id))
        return
    if getattr(instance, '_skip_keycrm_sync', False):
        return
    old_status = getattr(instance, '_keycrm_old_status', None)
    if old_status != instance.status:
        appointment_id = instance.pk
        site_status = instance.status
        transaction.on_commit(lambda: sync_appointment_status(appointment_id, site_status))


@receiver(post_save, sender=SiteBlock)
@receiver(post_delete, sender=SiteBlock)
def invalidate_site_blocks_cache(sender, **kwargs):
    cache.delete(settings.SITE_BLOCKS_CACHE_KEY)
