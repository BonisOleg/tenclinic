from django import forms
from django.core.exceptions import ValidationError

from clinic.models import CatalogService
from clinic.price_items import PRICE_SLUG_PREFIX
from clinic.utils.slug import latin_slug, unique_slug


class CatalogServiceForm(forms.ModelForm):
    class Meta:
        model = CatalogService
        fields = (
            'name',
            'slug',
            'direction',
            'short_description',
            'description',
            'is_active',
            'price',
            'price_note',
            'duration_minutes',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        if slug.startswith(PRICE_SLUG_PREFIX):
            raise ValidationError('Slug послуги каталогу не може починатися з prajs-.')
        return slug

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            base = latin_slug(obj.name, 'posluha')
            obj.slug = unique_slug(base, exclude_pk=obj.pk)
        if commit:
            obj.save()
        return obj
