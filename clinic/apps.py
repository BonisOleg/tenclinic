from django.apps import AppConfig


class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'
    verbose_name = 'TEN clinic'

    def ready(self):
        import clinic.signals  # noqa: F401
        self._configure_unfold_sidebar()

    def _configure_unfold_sidebar(self):
        from django.conf import settings
        from django.urls import reverse_lazy
        from clinic.site_content_registry import build_content_sidebar_items

        settings.UNFOLD['SIDEBAR']['navigation'] = [
            {
                'title': 'Налаштування',
                'items': [
                    {
                        'title': 'Сайт',
                        'icon': 'settings',
                        'link': reverse_lazy('admin:clinic_sitesettings_changelist'),
                    },
                ],
            },
            {
                'title': 'Контент сторінок',
                'separator': True,
                'items': build_content_sidebar_items(),
            },
            {
                'title': 'Каталог',
                'separator': True,
                'items': [
                    {'title': 'Напрямки', 'icon': 'medical_services', 'link': reverse_lazy('admin:clinic_direction_changelist')},
                    {'title': 'Лікарі', 'icon': 'person', 'link': reverse_lazy('admin:clinic_doctor_changelist')},
                    {'title': 'Послуги', 'icon': 'healing', 'link': reverse_lazy('admin:clinic_catalogservice_changelist')},
                    {'title': 'Прайс', 'icon': 'payments', 'link': reverse_lazy('admin:clinic_pricelistitem_changelist')},
                    {'title': 'Слухові апарати', 'icon': 'hearing', 'link': reverse_lazy('admin:clinic_hearingaid_changelist')},
                ],
            },
            {
                'title': 'Заявки',
                'separator': True,
                'items': [
                    {'title': 'Записи', 'icon': 'event', 'link': reverse_lazy('admin:clinic_appointment_changelist')},
                    {'title': 'Графік', 'icon': 'schedule', 'link': reverse_lazy('admin:clinic_workinghours_changelist')},
                ],
            },
        ]
