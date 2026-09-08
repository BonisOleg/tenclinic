from unittest.mock import patch
from urllib.error import URLError

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from clinic.forms import AppointmentForm
from clinic.models import Appointment, Direction
from clinic.services.keycrm import (
    build_card_payload,
    create_pipeline_card,
    is_configured,
    site_status_for_keycrm,
)
from clinic.services.keycrm_sync import sync_appointment_created, sync_appointment_status
from clinic.utils.map_embed import is_allowed_map_embed_url, normalize_map_embed, resolve_map_embed_src
from clinic.utils.phone_validation import is_valid_ua_phone, normalize_ua_phone, phone_e164


class PhoneValidationUtilsTests(SimpleTestCase):
    def test_valid_mobile_compact(self):
        self.assertTrue(is_valid_ua_phone('0671234567'))
        self.assertEqual(normalize_ua_phone('0671234567'), '+38 (067) 123-45-67')

    def test_valid_mobile_international(self):
        self.assertTrue(is_valid_ua_phone('+380671234567'))
        self.assertEqual(normalize_ua_phone('+380671234567'), '+38 (067) 123-45-67')

    def test_valid_formatted(self):
        self.assertEqual(
            normalize_ua_phone('+38 (067) 123-45-67'),
            '+38 (067) 123-45-67',
        )

    def test_valid_landline(self):
        self.assertTrue(is_valid_ua_phone('0441234567'))
        self.assertEqual(normalize_ua_phone('0441234567'), '+38 (044) 123-45-67')

    def test_invalid_short_number(self):
        self.assertFalse(is_valid_ua_phone('06712345'))

    def test_invalid_operator_prefix(self):
        self.assertFalse(is_valid_ua_phone('0171234567'))

    def test_e164(self):
        self.assertEqual(phone_e164('+38 (067) 123-45-67'), '+380671234567')


class AppointmentFormPhoneTests(TestCase):
    def test_form_normalizes_phone(self):
        form = AppointmentForm()
        form.cleaned_data = {'phone': '0671234567'}
        self.assertEqual(form.clean_phone(), '+38 (067) 123-45-67')

    def test_form_rejects_invalid_phone(self):
        form = AppointmentForm()
        form.cleaned_data = {'phone': '123'}
        with self.assertRaises(ValidationError):
            form.clean_phone()


class MapEmbedUtilsTests(SimpleTestCase):
    IFRAME = (
        '<iframe src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d2540.35'
        '!2d30.51162307654055!3d50.4531663871682!2m3!1f0!2f0!3f0!3m2!1i1024!2i768'
        '!4f13.1!3m2!1m1!2s!5e0!3m2!1sru!2sua!4v1783347305093!5m2!1sru!2sua" '
        'width="600" height="450" style="border:0;" allowfullscreen="" '
        'loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe>'
    )
    SRC = (
        'https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d2540.35'
        '!2d30.51162307654055!3d50.4531663871682!2m3!1f0!2f0!3f0!3m2!1i1024!2i768'
        '!4f13.1!3m2!1m1!2s!5e0!3m2!1sru!2sua!4v1783347305093!5m2!1sru!2sua'
    )

    def test_extracts_src_from_iframe(self):
        self.assertEqual(normalize_map_embed(self.IFRAME), self.SRC)

    def test_passes_through_embed_url(self):
        self.assertEqual(normalize_map_embed(self.SRC), self.SRC)

    def test_empty_value(self):
        self.assertEqual(normalize_map_embed(''), '')
        self.assertEqual(normalize_map_embed('   '), '')

    def test_invalid_iframe_without_src(self):
        self.assertEqual(normalize_map_embed('<iframe width="600"></iframe>'), '')

    def test_allowed_google_embed_url(self):
        self.assertTrue(is_allowed_map_embed_url(self.SRC))

    def test_rejects_non_google_url(self):
        self.assertFalse(is_allowed_map_embed_url('https://example.com/maps/embed'))

    def test_resolve_prefers_embed_over_coordinates(self):
        src = resolve_map_embed_src(self.IFRAME, lat='50.1', lng='30.2', address='Київ')
        self.assertEqual(src, self.SRC)


KEYCRM_SETTINGS = {
    'KEYCRM_API_KEY': 'test-key',
    'KEYCRM_PIPELINE_ID': '94',
    'KEYCRM_STATUS_NEW': '1001',
    'KEYCRM_STATUS_PROCESSING': '1002',
    'KEYCRM_STATUS_CONFIRMED': '1003',
    'KEYCRM_STATUS_REJECTED': '1004',
    'KEYCRM_SOURCE_ID': '10',
    'KEYCRM_WEBHOOK_SECRET': 'hook-secret',
    'KEYCRM_FIELD_DIRECTION': 'LD_1001',
    'KEYCRM_FIELD_DOCTOR': 'LD_1002',
    'KEYCRM_FIELD_COMMENT': 'LD_1004',
    'KEYCRM_FIELD_CONTACT': 'LD_1005',
}


@override_settings(**KEYCRM_SETTINGS)
class KeyCrmServiceTests(TestCase):
    def setUp(self):
        self.direction = Direction.objects.create(
            name='Отоларингологія',
            slug='lor',
            description='desc',
        )
        self.appointment = Appointment.objects.create(
            name='Іван Тест',
            phone='+38 (067) 123-45-67',
            email='ivan@example.com',
            direction=self.direction,
            contact_method='viber',
            comment='Після 18:00',
            status='new',
        )

    def test_is_configured(self):
        self.assertTrue(is_configured())

    def test_payload_maps_custom_fields(self):
        payload = build_card_payload(self.appointment)
        self.assertEqual(payload['pipeline_id'], 94)
        self.assertEqual(payload['status_id'], 1001)
        self.assertEqual(payload['source_id'], 10)
        self.assertEqual(payload['contact']['phone'], '+380671234567')
        uuids = {item['uuid']: item['value'] for item in payload['custom_fields']}
        self.assertEqual(uuids['LD_1001'], 'Отоларингологія')
        self.assertEqual(uuids['LD_1005'], ['Viber'])
        self.assertEqual(uuids['LD_1004'], 'Після 18:00')

    def test_undecided_direction_label(self):
        self.appointment.direction = None
        self.appointment.is_direction_undecided = True
        payload = build_card_payload(self.appointment)
        uuids = {item['uuid']: item['value'] for item in payload['custom_fields']}
        self.assertEqual(uuids['LD_1001'], 'Не можу визначитися')

    def test_status_reverse_map(self):
        self.assertEqual(site_status_for_keycrm(1003), 'confirmed')
        self.assertIsNone(site_status_for_keycrm(9999))

    @patch('clinic.services.keycrm.urlopen', side_effect=URLError('down'))
    def test_create_failure_does_not_store_id(self, _urlopen):
        self.assertIsNone(create_pipeline_card(self.appointment))

    @patch('clinic.services.keycrm_sync.create_pipeline_card', return_value=13898)
    def test_sync_created_stores_card_id_once(self, create_mock):
        self.appointment.keycrm_card_id = None
        self.appointment.save(update_fields=['keycrm_card_id'])
        Appointment.objects.filter(pk=self.appointment.pk).update(keycrm_card_id=None)
        sync_appointment_created(self.appointment.pk)
        sync_appointment_created(self.appointment.pk)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.keycrm_card_id, 13898)
        self.assertEqual(create_mock.call_count, 1)

    @patch('clinic.services.keycrm_sync.update_pipeline_card_status')
    def test_sync_status_skips_without_card(self, update_mock):
        sync_appointment_status(self.appointment.pk, 'processing')
        update_mock.assert_not_called()


@override_settings(**KEYCRM_SETTINGS)
class KeyCrmWebhookTests(TestCase):
    def setUp(self):
        self.appointment = Appointment.objects.create(
            name='Іван Тест',
            phone='+38 (067) 123-45-67',
            status='new',
            keycrm_card_id=13898,
        )

    def test_rejects_bad_secret(self):
        url = reverse('clinic:keycrm_webhook', kwargs={'token': 'wrong'})
        response = self.client.post(url, data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_updates_status_without_loop(self):
        url = reverse('clinic:keycrm_webhook', kwargs={'token': 'hook-secret'})
        with patch('clinic.services.keycrm_sync.update_pipeline_card_status') as update_mock:
            response = self.client.post(
                url,
                data=(
                    '{"event":"lead.change_lead_status",'
                    '"context":{"id":13898,"status_id":1002}}'
                ),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'processing')
        update_mock.assert_not_called()

    def test_same_status_is_noop(self):
        url = reverse('clinic:keycrm_webhook', kwargs={'token': 'hook-secret'})
        response = self.client.post(
            url,
            data=(
                '{"event":"lead.change_lead_status",'
                '"context":{"id":13898,"status_id":1001}}'
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'new')
