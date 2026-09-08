import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from clinic.models import Appointment
from clinic.services.keycrm import site_status_for_keycrm

logger = logging.getLogger('clinic.keycrm')


def _secret_ok(token):
    expected = getattr(settings, 'KEYCRM_WEBHOOK_SECRET', '')
    if not expected or not token:
        return False
    try:
        return hmac.compare_digest(str(token), str(expected))
    except (TypeError, ValueError):
        return False


@csrf_exempt
@require_POST
def keycrm_webhook(request, token):
    if not _secret_ok(token):
        return HttpResponseForbidden('forbidden')
    try:
        payload = json.loads(request.body.decode() or '{}')
    except json.JSONDecodeError:
        return HttpResponse('ok', content_type='text/plain')
    if payload.get('event') != 'lead.change_lead_status':
        return HttpResponse('ok', content_type='text/plain')
    context = payload.get('context') or {}
    card_id = context.get('id')
    site_status = site_status_for_keycrm(context.get('status_id'))
    if not card_id or not site_status:
        return HttpResponse('ok', content_type='text/plain')
    appointment = Appointment.objects.filter(keycrm_card_id=card_id).first()
    if not appointment or appointment.status == site_status:
        return HttpResponse('ok', content_type='text/plain')
    appointment._skip_keycrm_sync = True
    appointment.status = site_status
    appointment.save(update_fields=['status'])
    logger.info('KeyCRM webhook status %s for appointment %s', site_status, appointment.pk)
    return HttpResponse('ok', content_type='text/plain')
