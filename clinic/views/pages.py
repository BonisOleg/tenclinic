from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from clinic.forms import AppointmentForm, increment_rate_limit, is_rate_limited
from clinic.models import Direction, Doctor, HearingAid, PriceListSettings, Service, WorkingHours
from clinic.price_items import (
    PRICE_SLUG_PREFIX,
    catalog_services_filter,
    direction_has_price_items,
    public_services_queryset,
)
from clinic.utils.block_render import get_block_text


def home(request):
    directions = Direction.objects.filter(is_active=True)
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related('directions')
        .order_by('order', 'full_name')[:4]
    )
    today_hours = _today_hours()
    return render(request, 'pages/home.html', {
        'directions': directions,
        'doctors': doctors,
        'today_hours': today_hours,
    })


def directions_list(request):
    directions = (
        Direction.objects.filter(is_active=True)
        .annotate(
            services_count=Count(
                'services',
                filter=Q(services__is_active=True) & ~Q(services__slug__startswith=PRICE_SLUG_PREFIX),
                distinct=True,
            ),
            doctors_count=Count(
                'doctors',
                filter=Q(doctors__is_active=True),
                distinct=True,
            ),
        )
    )
    return render(request, 'pages/directions/list.html', {
        'directions': directions,
        'breadcrumbs': [{'title': 'Напрямки'}],
    })


def direction_detail(request, slug):
    direction = get_object_or_404(Direction, slug=slug, is_active=True)
    services = direction.services.filter(is_active=True).exclude(**catalog_services_filter())
    doctors = (
        direction.doctors.filter(is_active=True)
        .prefetch_related('directions')
        .distinct()
        .order_by('order', 'full_name')
    )
    return render(request, 'pages/directions/detail.html', {
        'direction': direction,
        'services': services,
        'doctors': doctors,
        'breadcrumbs': [
            {'title': 'Напрямки', 'url': '/directions/'},
            {'title': direction.name},
        ],
    })


def doctors_list(request):
    direction_slug = request.GET.get('direction', '')
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related('directions')
        .order_by('order', 'full_name')
    )
    if direction_slug:
        doctors = doctors.filter(directions__slug=direction_slug).distinct()
    directions = Direction.objects.filter(is_active=True)
    if request.htmx:
        return render(request, 'partials/doctors_grid.html', {
            'doctors': doctors,
        })
    return render(request, 'pages/doctors/list.html', {
        'doctors': doctors,
        'directions': directions,
        'current_direction': direction_slug,
    })


def doctor_detail(request, slug):
    doctor = get_object_or_404(
        Doctor.objects.prefetch_related('directions'),
        slug=slug,
        is_active=True,
    )
    services = doctor.services.filter(is_active=True)
    return render(request, 'pages/doctors/detail.html', {
        'doctor': doctor,
        'services': services,
        'breadcrumbs': [
            {'title': 'Лікарі', 'url': '/doctors/'},
            {'title': doctor.full_name},
        ],
    })


def _services_list_context(direction_slug):
    services = public_services_queryset(direction_slug=direction_slug)
    has_price = bool(direction_slug) and direction_has_price_items(direction_slug)
    price_direction_slug = direction_slug if has_price and not services.exists() else ''
    return {
        'services': services,
        'current_direction': direction_slug,
        'price_direction_slug': price_direction_slug,
        'price_section_slug': direction_slug if has_price else '',
    }


def services_list(request):
    direction_slug = request.GET.get('direction', '')
    context = _services_list_context(direction_slug)
    if request.htmx:
        return render(request, 'partials/services_grid.html', context)
    directions = Direction.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'pages/services/list.html', {
        **context,
        'directions': directions,
    })


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    doctors = service.doctors.filter(is_active=True)
    return render(request, 'pages/services/detail.html', {
        'service': service,
        'doctors': doctors,
        'show_direction_price': direction_has_price_items(service.direction.slug),
        'breadcrumbs': [
            {'title': 'Послуги та ціни', 'url': '/services/'},
            {'title': service.name},
        ],
    })


def price_list(request):
    price_services = Service.objects.filter(
        is_active=True,
        slug__startswith=PRICE_SLUG_PREFIX,
    ).order_by('order', 'name')
    directions = (
        Direction.objects.filter(is_active=True)
        .filter(services__in=price_services)
        .distinct()
        .prefetch_related(
            Prefetch('services', queryset=price_services),
        )
        .order_by('order', 'name')
    )
    return render(request, 'pages/price.html', {
        'directions': directions,
        'price_updated_on': PriceListSettings.get_solo().updated_on,
        'breadcrumbs': [
            {'title': 'Послуги та ціни', 'url': '/services/'},
            {'title': 'Прайс'},
        ],
    })


SURDOLOGY_SLUG = 'surdologiya'
HEARING_AIDS_PER_PAGE = 10


def surgical_operations_list(request):
    direction_slug = request.GET.get('direction', '')
    directions = Direction.objects.filter(is_active=True)
    current_direction = None
    if direction_slug:
        current_direction = directions.filter(slug=direction_slug).first()
    return render(request, 'pages/surgical_operations/list.html', {
        'directions': directions,
        'current_direction': current_direction,
        'current_direction_slug': direction_slug,
        'breadcrumbs': [{'title': 'Хірургічні операції'}],
    })


def about_us(request):
    return render(request, 'pages/about_us.html', {
        'breadcrumbs': [{'title': 'Про нас'}],
    })


def hearing_aids_list(request):
    surdology = Direction.objects.filter(slug=SURDOLOGY_SLUG, is_active=True).first()
    queryset = HearingAid.objects.filter(is_active=True)
    paginator = Paginator(queryset, HEARING_AIDS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'pages/hearing_aids/list.html', {
        'page_obj': page_obj,
        'has_hearing_aids': paginator.count > 0,
        'surdology': surdology,
        'breadcrumbs': [
            {'title': 'Напрямки', 'url': '/directions/'},
            *(
                [{'title': surdology.name, 'url': f'/directions/{surdology.slug}/'}]
                if surdology else []
            ),
            {'title': 'Слухові апарати'},
        ],
    })


def contacts(request):
    hours = WorkingHours.objects.all()
    today_hours = _today_hours()
    return render(request, 'pages/contacts.html', {
        'hours': hours,
        'today_hours': today_hours,
        'today_weekday': datetime.now().weekday(),
    })


def privacy(request):
    return render(request, 'pages/privacy.html')


@require_http_methods(['GET', 'POST'])
def booking(request):
    initial = {}
    doctor_slug = request.GET.get('doctor')
    service_slug = request.GET.get('service')
    direction_slug = request.GET.get('direction')

    if doctor_slug:
        doctor = Doctor.objects.filter(slug=doctor_slug, is_active=True).first()
        if doctor:
            initial['doctor'] = doctor
            primary_direction = doctor.primary_direction
            if primary_direction:
                initial['direction'] = primary_direction
    if service_slug:
        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service:
            initial['direction'] = service.direction
    if direction_slug and 'direction' not in initial:
        direction = Direction.objects.filter(slug=direction_slug, is_active=True).first()
        if direction:
            initial['direction'] = direction

    success = False
    form = AppointmentForm(request.POST or None, initial=initial)

    if request.method == 'POST':
        if is_rate_limited(_client_ip(request)):
            form.add_error(None, 'Забагато заявок. Спробуйте пізніше.')
        elif form.is_valid():
            appointment = form.save(commit=False)
            appointment.ip_address = _client_ip(request)
            appointment.save()
            increment_rate_limit(_client_ip(request))
            success = True
            if request.htmx:
                return render(request, 'partials/booking_success.html', {
                    'success_message': _success_message(request),
                })
            form = AppointmentForm(initial=initial)

    if request.htmx and request.method == 'POST' and not success:
        return render(request, 'partials/booking_form.html', {'form': form})

    return render(request, 'pages/booking.html', {
        'form': form,
        'success': success,
        'success_message': _success_message(request) if success else '',
    })


@require_GET
def booking_services(request):
    direction_id = request.GET.get('direction')
    services = Service.objects.filter(direction_id=direction_id, is_active=True).exclude(
        **catalog_services_filter(),
    ) if direction_id else Service.objects.none()
    return render(request, 'partials/service_options.html', {'services': services})


@require_GET
def booking_doctors(request):
    service_id = request.GET.get('service')
    direction_id = request.GET.get('direction')
    doctors = Doctor.objects.none()
    if service_id:
        doctors = Doctor.objects.filter(services__id=service_id, is_active=True).distinct()
    elif direction_id:
        doctors = Doctor.objects.filter(
            directions__id=direction_id,
            is_active=True,
        ).distinct()
    return render(request, 'partials/doctor_options.html', {'doctors': doctors})


def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    return render(request, 'errors/500.html', status=500)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _today_hours():
    weekday = datetime.now().weekday()
    return WorkingHours.objects.filter(day_of_week=weekday).first()


def _success_message(request):
    from clinic.context_processors import site_context
    site_blocks = site_context(request)['site_blocks']
    return get_block_text('booking', 'success_message', site_blocks=site_blocks, fallback=(
        'Дякуємо! Вашу заявку отримано. Адміністратор звʼяжеться з вами найближчим часом.'
    ))
