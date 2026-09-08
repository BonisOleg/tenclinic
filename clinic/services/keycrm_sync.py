import logging

from clinic.models import Appointment
from clinic.services.keycrm import create_pipeline_card, update_pipeline_card_status

logger = logging.getLogger('clinic.keycrm')


def sync_appointment_created(appointment_id):
    appointment = (
        Appointment.objects.filter(pk=appointment_id, keycrm_card_id__isnull=True)
        .select_related('direction', 'doctor')
        .first()
    )
    if not appointment:
        return
    card_id = create_pipeline_card(appointment)
    if not card_id:
        return
    updated = Appointment.objects.filter(
        pk=appointment_id,
        keycrm_card_id__isnull=True,
    ).update(keycrm_card_id=card_id)
    if updated:
        logger.info('KeyCRM card %s for appointment %s', card_id, appointment_id)


def sync_appointment_status(appointment_id, site_status):
    appointment = Appointment.objects.filter(pk=appointment_id).only(
        'id', 'keycrm_card_id', 'status',
    ).first()
    if not appointment or not appointment.keycrm_card_id:
        return
    update_pipeline_card_status(appointment.keycrm_card_id, site_status)
