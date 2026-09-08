import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from clinic.utils.phone_validation import phone_e164

logger = logging.getLogger('clinic.keycrm')

CONTACT_METHOD_LABELS = {
    'call': 'Дзвінок',
    'sms': 'SMS',
    'viber': 'Viber',
    'telegram': 'Telegram',
    'whatsapp': 'WhatsApp',
}

STATUS_SETTING_NAMES = {
    'new': 'KEYCRM_STATUS_NEW',
    'processing': 'KEYCRM_STATUS_PROCESSING',
    'confirmed': 'KEYCRM_STATUS_CONFIRMED',
    'rejected': 'KEYCRM_STATUS_REJECTED',
}


def _optional_int(value):
    if value is None or str(value).strip() == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_configured():
    return bool(
        getattr(settings, 'KEYCRM_API_KEY', '')
        and _optional_int(getattr(settings, 'KEYCRM_PIPELINE_ID', None))
        and all(_status_id(code) for code in STATUS_SETTING_NAMES)
    )


def _status_id(site_status):
    name = STATUS_SETTING_NAMES.get(site_status)
    if not name:
        return None
    return _optional_int(getattr(settings, name, None))


def site_status_for_keycrm(status_id):
    target = _optional_int(status_id)
    if target is None:
        return None
    for code in STATUS_SETTING_NAMES:
        if _status_id(code) == target:
            return code
    return None


def _direction_label(appointment):
    if appointment.is_direction_undecided:
        return 'Не можу визначитися'
    if appointment.direction_id:
        return appointment.direction.name
    return ''


def _custom_fields(appointment):
    fields = []
    direction = _direction_label(appointment)
    if direction:
        fields.append({
            'uuid': settings.KEYCRM_FIELD_DIRECTION,
            'value': direction,
        })
    if appointment.doctor_id:
        fields.append({
            'uuid': settings.KEYCRM_FIELD_DOCTOR,
            'value': appointment.doctor.full_name,
        })
    contact_label = CONTACT_METHOD_LABELS.get(appointment.contact_method)
    if contact_label:
        fields.append({
            'uuid': settings.KEYCRM_FIELD_CONTACT,
            'value': [contact_label],
        })
    if appointment.comment:
        fields.append({
            'uuid': settings.KEYCRM_FIELD_COMMENT,
            'value': appointment.comment,
        })
    return fields


def build_card_payload(appointment):
    contact = {
        'full_name': appointment.name,
        'phone': phone_e164(appointment.phone),
    }
    if appointment.email:
        contact['email'] = appointment.email
    payload = {
        'title': f'{appointment.name} — запис',
        'pipeline_id': _optional_int(settings.KEYCRM_PIPELINE_ID),
        'status_id': _status_id(appointment.status) or _status_id('new'),
        'contact': contact,
        'custom_fields': _custom_fields(appointment),
    }
    source_id = _optional_int(getattr(settings, 'KEYCRM_SOURCE_ID', None))
    if source_id:
        payload['source_id'] = source_id
    return payload


def _request(method, path, payload=None):
    api_key = getattr(settings, 'KEYCRM_API_KEY', '')
    base = getattr(settings, 'KEYCRM_API_URL', 'https://openapi.keycrm.app/v1')
    url = f'{base.rstrip("/")}/{path.lstrip("/")}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(
        url,
        data=data,
        method=method,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except HTTPError as exc:
        logger.warning('KeyCRM HTTP %s %s: %s', method, path, exc.code)
        return None
    except (URLError, TimeoutError, json.JSONDecodeError, OSError):
        logger.warning('KeyCRM request failed: %s %s', method, path)
        return None


def create_pipeline_card(appointment):
    if not is_configured():
        return None
    response = _request('POST', 'pipelines/cards', build_card_payload(appointment))
    if not response:
        return None
    card_id = _optional_int(response.get('id'))
    if not card_id:
        logger.warning('KeyCRM create: no card id in response')
        return None
    return card_id


def update_pipeline_card_status(card_id, site_status):
    if not is_configured() or not card_id:
        return False
    status_id = _status_id(site_status)
    if not status_id:
        logger.warning('KeyCRM update: unknown status %s', site_status)
        return False
    response = _request('PUT', f'pipelines/cards/{card_id}', {'status_id': status_id})
    return response is not None
