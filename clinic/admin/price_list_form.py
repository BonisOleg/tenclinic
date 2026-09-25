from django import forms

from clinic.models import PriceListItem, PriceListSettings
from clinic.price_items import PRICE_SLUG_PREFIX, price_item_slug
from clinic.utils.slug import latin_slug, unique_slug


class PriceListItemForm(forms.ModelForm):
    class Meta:
        model = PriceListItem
        fields = (
            'name',
            'direction',
            'price',
            'price_note',
            'duration_minutes',
            'is_active',
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.description:
            obj.description = ''
        if not obj.short_description:
            obj.short_description = ''
        if not obj.slug:
            base = latin_slug(obj.name, 'posytsiya')
            obj.slug = unique_slug(base, prefix=PRICE_SLUG_PREFIX)
        elif not obj.slug.startswith(PRICE_SLUG_PREFIX):
            obj.slug = price_item_slug(obj.slug.removeprefix(PRICE_SLUG_PREFIX))
        if commit:
            obj.save()
        return obj


class PriceListDateForm(forms.ModelForm):
    class Meta:
        model = PriceListSettings
        fields = ('updated_on',)
        widgets = {
            'updated_on': forms.DateInput(attrs={'type': 'date'}),
        }
