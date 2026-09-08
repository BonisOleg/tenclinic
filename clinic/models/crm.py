from django.db import models

from clinic.image_specs import DIRECTION_IMAGE, DOCTOR_PHOTO, HEARING_AID_IMAGE


class Direction(models.Model):
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField('Опис')
    short_description = models.CharField('Короткий опис', max_length=250, blank=True)
    when_to_visit = models.TextField(
        'Коли звернутися',
        blank=True,
        help_text='Один пункт на рядок.',
    )
    services_overview = models.TextField(
        'Наші послуги',
        blank=True,
        help_text='Один пункт на рядок.',
    )
    image = models.ImageField(
        'Зображення',
        upload_to='directions/',
        blank=True,
        help_text=DIRECTION_IMAGE.help_text,
    )
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Напрямок'
        verbose_name_plural = 'Напрямки'

    def __str__(self):
        return self.name

    @staticmethod
    def _lines_to_items(text):
        return [line.strip() for line in text.splitlines() if line.strip()]

    @property
    def when_to_visit_items(self):
        return self._lines_to_items(self.when_to_visit)

    @property
    def services_overview_items(self):
        return self._lines_to_items(self.services_overview)


class Doctor(models.Model):
    full_name = models.CharField('ПІБ', max_length=200)
    slug = models.SlugField(unique=True)
    photo = models.ImageField(
        'Фото',
        upload_to='doctors/',
        blank=True,
        help_text=DOCTOR_PHOTO.help_text,
    )
    specialization = models.CharField('Спеціалізація', max_length=200)
    directions = models.ManyToManyField(
        Direction,
        related_name='doctors',
        verbose_name='Напрямки',
    )
    bio = models.TextField('Біографія')
    education = models.TextField('Освіта', blank=True)
    experience_years = models.PositiveIntegerField('Стаж (років)', default=0)
    services = models.ManyToManyField('Service', blank=True, related_name='doctors', verbose_name='Послуги')
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['order', 'full_name']
        verbose_name = 'Лікар'
        verbose_name_plural = 'Лікарі'

    def __str__(self):
        return self.full_name

    @property
    def primary_direction(self):
        return self.directions.order_by('order', 'name').first()


class HearingAid(models.Model):
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField(unique=True)
    image = models.ImageField(
        'Фото',
        upload_to='hearing-aids/',
        blank=True,
        help_text=HEARING_AID_IMAGE.help_text,
    )
    short_description = models.CharField('Підпис', max_length=300, help_text='Короткий текст під фото на картці.')
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Слуховий апарат'
        verbose_name_plural = 'Слухові апарати'

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField('Назва', max_length=300)
    slug = models.SlugField(unique=True)
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Напрямок',
    )
    description = models.TextField('Опис')
    short_description = models.CharField('Короткий опис', max_length=200, blank=True)
    duration_minutes = models.PositiveIntegerField('Тривалість (хв)', null=True, blank=True)
    price = models.DecimalField('Ціна', max_digits=10, decimal_places=2, null=True, blank=True)
    price_note = models.CharField('Примітка до ціни', max_length=200, blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Послуга'
        verbose_name_plural = 'Послуги'

    def __str__(self):
        return self.name

    @property
    def is_price_item(self):
        from clinic.price_items import is_price_item_slug

        return is_price_item_slug(self.slug)

    @property
    def price_display(self):
        if self.price is not None:
            prefix = f'{self.price_note} ' if self.price_note else ''
            amount = f'{int(self.price):,}'.replace(',', '\u00a0')
            return f'{prefix}{amount} ₴'
        return self.price_note or 'За прайсом'


class CatalogService(Service):
    class Meta:
        proxy = True
        verbose_name = 'Послуга каталогу'
        verbose_name_plural = 'Послуги каталогу'


class PriceListItem(Service):
    class Meta:
        proxy = True
        verbose_name = 'Позиція прайсу'
        verbose_name_plural = 'Прайс'


class WorkingHours(models.Model):
    DAYS = [
        (0, 'Понеділок'),
        (1, 'Вівторок'),
        (2, 'Середа'),
        (3, 'Четвер'),
        (4, 'Пʼятниця'),
        (5, 'Субота'),
        (6, 'Неділя'),
    ]
    day_of_week = models.IntegerField('День тижня', choices=DAYS, unique=True)
    open_time = models.TimeField('Відкриття', null=True, blank=True)
    close_time = models.TimeField('Закриття', null=True, blank=True)
    is_closed = models.BooleanField('Вихідний', default=False)

    class Meta:
        ordering = ['day_of_week']
        verbose_name = 'Графік роботи'
        verbose_name_plural = 'Графік роботи'

    def __str__(self):
        if self.is_closed:
            return f'{self.get_day_of_week_display()}: вихідний'
        return f'{self.get_day_of_week_display()}: {self.open_time:%H:%M}–{self.close_time:%H:%M}'


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нова'),
        ('processing', 'В обробці'),
        ('confirmed', 'Підтверджена'),
        ('rejected', 'Відхилена'),
    ]
    CONTACT_METHOD_CHOICES = [
        ('call', 'Дзвінок'),
        ('sms', 'SMS'),
        ('viber', 'Viber'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
    ]
    name = models.CharField('ПІБ', max_length=200)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    direction = models.ForeignKey(
        Direction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='Напрямок',
    )
    is_direction_undecided = models.BooleanField('Напрямок не визначено', default=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments',
        verbose_name='Послуга',
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='Лікар',
    )
    preferred_date = models.DateField('Бажана дата', null=True, blank=True)
    preferred_time = models.CharField('Бажаний час', max_length=50, blank=True)
    contact_method = models.CharField(
        'Спосіб звʼязку',
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        blank=True,
    )
    comment = models.TextField('Коментар', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    keycrm_card_id = models.PositiveIntegerField(
        'KeyCRM картка',
        null=True,
        blank=True,
        unique=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на запис'
        verbose_name_plural = 'Заявки на запис'

    def __str__(self):
        return f'{self.name} — {self.created_at:%d.%m.%Y}'
