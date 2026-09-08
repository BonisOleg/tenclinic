import re

from django.core.exceptions import ValidationError

UA_NATIONAL_PHONE_RE = re.compile(r'^0[3-9]\d{8}$')


def extract_national_digits(phone: str) -> str:
    digits = re.sub(r'\D', '', phone or '')
    if digits.startswith('380'):
        digits = digits[3:]
    elif digits.startswith('38'):
        digits = digits[2:]
    if digits and digits[0] != '0':
        digits = f'0{digits}'
    return digits[:10]


def is_valid_ua_phone(phone: str) -> bool:
    return bool(UA_NATIONAL_PHONE_RE.match(extract_national_digits(phone)))


def normalize_ua_phone(phone: str) -> str:
    national = extract_national_digits(phone)
    if not UA_NATIONAL_PHONE_RE.match(national):
        raise ValidationError('Введіть коректний номер телефону', code='invalid_phone')
    return (
        f'+38 ({national[:3]}) {national[3:6]}-'
        f'{national[6:8]}-{national[8:10]}'
    )


def phone_e164(phone: str) -> str:
    national = extract_national_digits(phone)
    if UA_NATIONAL_PHONE_RE.match(national):
        return f'+38{national}'
    return (phone or '').strip()


def phone_tel_uri(phone: str) -> str:
    national = extract_national_digits(phone)
    if UA_NATIONAL_PHONE_RE.match(national):
        return f'tel:+380{national[1:]}'
    digits = re.sub(r'\D', '', phone or '')
    if not digits:
        return ''
    if digits.startswith('380'):
        return f'tel:+{digits}'
    if digits.startswith('38'):
        return f'tel:+{digits}'
    if digits.startswith('0'):
        return f'tel:+38{digits[1:]}'
    return f'tel:+{digits}'
