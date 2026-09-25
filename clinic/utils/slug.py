from django.utils.text import slugify

_LETTERS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye',
    'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k', 'л': 'l',
    'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu',
    'я': 'ya', 'ъ': '', 'ы': 'y', 'э': 'e', 'ё': 'yo',
}


def latin_slug(value, fallback):
    text = ''.join(_LETTERS.get(char, char) for char in (value or '').lower())
    return slugify(text) or fallback


def unique_slug(base, *, prefix='', exclude_pk=None):
    from clinic.models import Service

    for index in range(1, 100):
        suffix = base if index == 1 else f'{base}-{index}'
        candidate = f'{prefix}{suffix}'
        matches = Service.objects.filter(slug=candidate)
        if exclude_pk:
            matches = matches.exclude(pk=exclude_pk)
        if not matches.exists():
            return candidate
    raise ValueError('Не вдалося згенерувати унікальний slug.')
