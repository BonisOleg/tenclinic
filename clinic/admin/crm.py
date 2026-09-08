from unfold.admin import ModelAdmin

from clinic.admin.filters import HasPriceFilter
from clinic.admin.hearing_aid_form import HearingAidAdminForm
from clinic.admin.mixins import DoctorImagePreviewMixin, ImagePreviewMixin, OrderOnCreateMixin, ReadableUnfoldFieldsMixin
from clinic.admin.price_list_form import PriceListItemForm
from clinic.models import Appointment, CatalogService, Direction, Doctor, HearingAid, PriceListItem, Service, WorkingHours
from clinic.price_items import PRICE_SLUG_PREFIX, catalog_services_filter


class DirectionAdmin(OrderOnCreateMixin, ImagePreviewMixin, ModelAdmin):
    ordering_field = 'order'
    hide_ordering_field = True
    list_display = ('name', 'image_thumb', 'is_active')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'short_description', 'description', 'image', 'get_image_preview', 'is_active'),
            'description': 'Короткий опис — для картки. Повний опис — на детальній сторінці.',
        }),
        ('Детальна сторінка', {
            'fields': ('when_to_visit', 'services_overview'),
            'description': 'Кожен пункт — з нового рядка. «Наші послуги» показується списком на сторінці напрямку.',
        }),
    )

    def image_thumb(self, obj):
        return self.get_image_preview(obj)

    image_thumb.short_description = 'Фото'


class DoctorAdmin(OrderOnCreateMixin, DoctorImagePreviewMixin, ModelAdmin):
    ordering_field = 'order'
    hide_ordering_field = True
    list_display = ('full_name', 'photo_thumb', 'specialization', 'directions_display', 'is_active')
    list_filter = ('directions', 'is_active')
    prepopulated_fields = {'slug': ('full_name',)}
    search_fields = ('full_name', 'specialization')
    filter_horizontal = ('directions', 'services')
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        (None, {
            'fields': (
                'full_name', 'slug', 'photo', 'get_image_preview',
                'specialization', 'directions', 'is_active',
            ),
        }),
        ('Профіль', {
            'fields': ('bio', 'education', 'experience_years', 'services'),
        }),
    )

    def directions_display(self, obj):
        return ', '.join(obj.directions.values_list('name', flat=True))

    directions_display.short_description = 'Напрямки'

    def photo_thumb(self, obj):
        return self.get_image_preview(obj)

    photo_thumb.short_description = 'Фото'


class HearingAidAdmin(OrderOnCreateMixin, ReadableUnfoldFieldsMixin, ImagePreviewMixin, ModelAdmin):
    form = HearingAidAdminForm
    ordering_field = 'order'
    hide_ordering_field = True
    list_display = ('name', 'image_thumb', 'caption_preview', 'is_active')
    list_display_links = ('name',)
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'short_description')
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'is_active'),
        }),
        ('Картка на сайті', {
            'fields': ('image', 'get_image_preview', 'short_description'),
            'description': (
                'Формат фото: JPG або PNG, рекомендований розмір 400×400 px (1:1). '
                'Фото та підпис відображаються на сторінці «Слухові апарати».'
            ),
        }),
    )

    def image_thumb(self, obj):
        return self.get_image_preview(obj)

    image_thumb.short_description = 'Фото'

    def caption_preview(self, obj):
        if not obj.short_description:
            return '—'
        if len(obj.short_description) <= 60:
            return obj.short_description
        return f'{obj.short_description[:57]}…'

    caption_preview.short_description = 'Підпис'


class ServiceAutocompleteAdmin(ModelAdmin):
    search_fields = ('name',)

    def has_module_permission(self, request):
        return False

    def get_model_perms(self, request):
        return {}


class CatalogServiceAdmin(OrderOnCreateMixin, ModelAdmin):
    ordering_field = 'order'
    hide_ordering_field = True
    list_display = ('name', 'direction', 'price', 'price_on_site', 'is_active')
    list_editable = ('price', 'is_active')
    list_filter = ('direction', 'is_active', HasPriceFilter)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    autocomplete_fields = ('direction',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'direction', 'short_description', 'description', 'is_active'),
        }),
        ('Ціна та тривалість', {
            'fields': ('price', 'price_note', 'duration_minutes'),
            'description': (
                'Ціна показується на «Послуги та ціни» для напрямків без окремого прайсу '
                '(наприклад, дитяча ЛОР, сурдологія). Для отоларингології, щелепно-лицевої '
                'хірургії та анестезії редагуйте ціни в розділі «Прайс».'
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(**catalog_services_filter())

    def price_on_site(self, obj):
        return obj.price_display

    price_on_site.short_description = 'На сайті'


class PriceListItemAdmin(OrderOnCreateMixin, ModelAdmin):
    form = PriceListItemForm
    ordering_field = 'order'
    hide_ordering_field = True
    list_display = ('name', 'direction', 'price', 'price_on_site', 'is_active')
    list_editable = ('price', 'is_active')
    list_filter = ('direction', 'is_active', HasPriceFilter)
    search_fields = ('name',)
    autocomplete_fields = ('direction',)
    readonly_fields = ('slug',)
    fieldsets = (
        (None, {
            'fields': ('name', 'direction', 'price', 'price_note', 'duration_minutes', 'is_active'),
            'description': (
                'Позиції прайсу відображаються на «Послуги та ціни» та /price/ '
                'для обраного напрямку. Slug генерується автоматично.'
            ),
        }),
        ('Системне', {
            'fields': ('slug',),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(slug__startswith=PRICE_SLUG_PREFIX)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ('slug',)

    def price_on_site(self, obj):
        return obj.price_display

    price_on_site.short_description = 'На сайті'


class ServiceAdmin(CatalogServiceAdmin):
    """Залишено для зворотної сумісності імпортів."""


class WorkingHoursAdmin(ModelAdmin):
    list_display = ('day_of_week', 'open_time', 'close_time', 'is_closed')


class AppointmentAdmin(ModelAdmin):
    list_display = ('name', 'phone', 'direction', 'contact_method', 'status', 'keycrm_card_id', 'created_at')
    list_filter = ('status', 'direction', 'contact_method', 'created_at')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'ip_address', 'keycrm_card_id')
    autocomplete_fields = ('direction', 'service', 'doctor')
