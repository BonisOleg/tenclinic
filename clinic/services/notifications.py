import html
import json
import logging
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

logger = logging.getLogger(__name__)

TELEGRAM_TIMEOUT_SECONDS = 5


def notify_new_appointment(appointment):
    """Schedule email + Telegram after the surrounding transaction commits.

    Runs in a daemon thread so SMTP/Telegram cannot block the booking request.
    Missing Telegram env is a silent no-op. Errors are logged and never raised.
    """
    snapshot = _appointment_snapshot(appointment)

    def _after_commit():
        thread = Thread(
            target=_notify_in_background,
            args=(snapshot,),
            daemon=True,
            name=f'tenclinic-lead-notify-{snapshot["id"]}',
        )
        thread.start()

    transaction.on_commit(_after_commit)


def _appointment_snapshot(appointment):
    if appointment.is_direction_undecided:
        direction_label = 'Не можу визначитися'
    else:
        direction_label = str(appointment.direction) if appointment.direction else '—'
    return {
        'id': appointment.pk,
        'name': appointment.name or '',
        'phone': appointment.phone or '',
        'email': appointment.email or '',
        'direction_label': direction_label,
        'doctor': str(appointment.doctor) if appointment.doctor else '—',
        'contact_method': appointment.get_contact_method_display() or '—',
        'comment': appointment.comment or '',
    }


def _plain_body(snapshot):
    return (
        f'ПІБ: {snapshot["name"]}\n'
        f'Телефон: {snapshot["phone"]}\n'
        f'Email: {snapshot["email"] or "—"}\n'
        f'Напрямок: {snapshot["direction_label"]}\n'
        f'Лікар: {snapshot["doctor"]}\n'
        f'Спосіб звʼязку: {snapshot["contact_method"]}\n'
        f'Коментар: {snapshot["comment"] or "—"}\n'
    )


def _html_body(snapshot):
    def esc(value):
        return html.escape(str(value), quote=True)

    return (
        f'ПІБ: {esc(snapshot["name"])}\n'
        f'Телефон: {esc(snapshot["phone"])}\n'
        f'Email: {esc(snapshot["email"] or "—")}\n'
        f'Напрямок: {esc(snapshot["direction_label"])}\n'
        f'Лікар: {esc(snapshot["doctor"])}\n'
        f'Спосіб звʼязку: {esc(snapshot["contact_method"])}\n'
        f'Коментар: {esc(snapshot["comment"] or "—")}\n'
    )


def _notify_in_background(snapshot):
    try:
        _send_email(snapshot)
    except Exception:
        logger.exception('Email lead notification failed, appointment_id=%s', snapshot.get('id'))
    try:
        _send_telegram(snapshot)
    except Exception:
        logger.exception(
            'Telegram lead notification failed, appointment_id=%s',
            snapshot.get('id'),
        )


def _send_email(snapshot):
    recipient = getattr(settings, 'NOTIFICATION_EMAIL', '') or ''
    if not recipient:
        return
    subject = f'[TEN clinic] Нова заявка на запис — {snapshot["name"]}'
    send_mail(
        subject,
        _plain_body(snapshot),
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )


def _send_telegram(snapshot):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or ''
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '') or ''
    if not token or not chat_id:
        return

    payload = json.dumps({
        'chat_id': chat_id,
        'text': f'<b>Нова заявка</b>\n{_html_body(snapshot)}',
        'parse_mode': 'HTML',
    }).encode()
    req = Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(req, timeout=TELEGRAM_TIMEOUT_SECONDS) as resp:
            logger.info(
                'Telegram lead notification sent, appointment_id=%s status=%s',
                snapshot.get('id'),
                getattr(resp, 'status', None),
            )
    except HTTPError as exc:
        logger.warning(
            'Telegram lead notification rejected, appointment_id=%s status=%s',
            snapshot.get('id'),
            exc.code,
        )
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning(
            'Telegram lead notification failed, appointment_id=%s error=%s',
            snapshot.get('id'),
            type(exc).__name__,
        )
