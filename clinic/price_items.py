from decimal import Decimal

PRICE_SLUG_PREFIX = 'prajs-'

PRICE_ITEMS = [
    ('lor-konsultaciya-pervynna', 'Консультація первинна', 'otolaryngologiya', Decimal('1000')),
    ('lor-konsultaciya-povtorna', 'Консультація повторна', 'otolaryngologiya', Decimal('600')),
    ('lor-konsultaciya-onlayn', 'Онлайн консультація', 'otolaryngologiya', Decimal('1000')),
    ('lor-audiometriya-dorosla', 'Аудіометрія доросла', 'otolaryngologiya', Decimal('500')),
    ('lor-audiometriya-dytacha', 'Аудіометрія дитяча (до 6 років)', 'otolaryngologiya', Decimal('700')),
    ('lor-timpanometriya', 'Тимпанометрія', 'otolaryngologiya', Decimal('400')),
    ('lor-fibroendoskopiya', 'Фіброендоскопія', 'otolaryngologiya', Decimal('600')),
    ('lor-vydalennya-probky', 'Видалення сірчаної пробки', 'otolaryngologiya', Decimal('400')),
    ('lor-promyvannya-nosa', 'Промивання носу методом переміщення', 'otolaryngologiya', Decimal('500')),
    ('lor-promyvannya-migdalikiv', 'Промивання лакун мигдаликів', 'otolaryngologiya', Decimal('1000')),
    ('lor-pidbir-aparatu', 'Підбір слухового апарату', 'otolaryngologiya', Decimal('1000')),
    ('lor-perenastuvannya-aparatu', 'Переналаштування слухового апарату', 'otolaryngologiya', Decimal('600')),
    ('lor-oae', 'Реєстрація отоакустичної емісії', 'otolaryngologiya', Decimal('500')),
    ('lor-ksvp', 'Реєстрація КСВП уві сні', 'otolaryngologiya', Decimal('3500')),
    ('shlh-konsultaciya-pervynna', 'Консультація первинна', 'shchelepno-lytseva-hirurgiya', Decimal('1200')),
    ('shlh-konsultaciya-povtorna', 'Консультація повторна', 'shchelepno-lytseva-hirurgiya', Decimal('600')),
    ('anest-konsultaciya', 'Консультація', 'anesteziologiya', Decimal('1000')),
    ('anest-peredoperacijna-ekg', 'Передопераційна ЕКГ', 'anesteziologiya', Decimal('600')),
]


def price_item_slug(suffix):
    return f'{PRICE_SLUG_PREFIX}{suffix}'


def is_price_item_slug(slug):
    return slug.startswith(PRICE_SLUG_PREFIX)


def catalog_services_filter(prefix=''):
    key = f'{prefix}slug__startswith' if prefix else 'slug__startswith'
    return {f'{key}': PRICE_SLUG_PREFIX}


def directions_with_price_items():
    from clinic.models import Direction

    return Direction.objects.filter(
        is_active=True,
        services__slug__startswith=PRICE_SLUG_PREFIX,
        services__is_active=True,
    ).distinct()


def direction_has_price_items(direction_slug):
    if not direction_slug:
        return False
    return directions_with_price_items().filter(slug=direction_slug).exists()


def public_services_queryset(*, direction_slug=''):
    from clinic.models import Service

    services = (
        Service.objects.filter(is_active=True)
        .exclude(slug__startswith=PRICE_SLUG_PREFIX)
        .select_related('direction')
        .order_by('direction__order', 'direction__name', 'order', 'name')
    )
    if direction_slug:
        services = services.filter(direction__slug=direction_slug)
    return services


def seed_price_items(*, directions_by_slug):
    from clinic.models import Service

    for order, (suffix, name, direction_slug, price) in enumerate(PRICE_ITEMS):
        direction = directions_by_slug.get(direction_slug)
        if direction is None:
            continue
        Service.objects.update_or_create(
            slug=price_item_slug(suffix),
            defaults={
                'name': name,
                'direction': direction,
                'description': '',
                'short_description': '',
                'price': price,
                'order': order,
                'is_active': True,
            },
        )
