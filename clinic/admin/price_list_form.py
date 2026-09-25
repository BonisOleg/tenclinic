from django import forms
from django.utils import timezone

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
    date_mode = forms.ChoiceField(
        label='Яку дату показувати',
        choices=(
            ('today', 'Сьогоднішня дата'),
            ('fixed', 'Конкретна дата'),
        ),
        widget=forms.Select(attrs={'class': 'price-date-bar__mode'}),
    )

    class Meta:
        model = PriceListSettings
        fields = ('updated_on',)
        widgets = {
            'updated_on': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['updated_on'].input_formats = ['%Y-%m-%d']
        self.fields['updated_on'].required = False
        stored = self.instance.updated_on if self.instance and self.instance.pk else None
        show_today = bool(self.instance and self.instance.pk and self.instance.use_today)
        self.fields['date_mode'].initial = 'today' if show_today else 'fixed'
        if stored:
            self.fields['updated_on'].widget.attrs['data-fixed-date'] = stored.isoformat()
        if show_today and not self.is_bound:
            self.initial['updated_on'] = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('date_mode') == 'fixed' and not cleaned.get('updated_on'):
            self.add_error('updated_on', 'Оберіть дату.')
        return cleaned

    def save(self, commit=True):
        use_today = self.cleaned_data.get('date_mode') == 'today'
        if use_today:
            self.cleaned_data['updated_on'] = self.instance.updated_on or timezone.localdate()
        obj = super().save(commit=False)
        obj.use_today = use_today
        if commit:
            obj.save()
        return obj
