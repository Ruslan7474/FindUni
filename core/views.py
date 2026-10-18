import logging

from django.conf import settings
from django.db.models import Avg, Count, Min, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .models import Notification
from institutions.models import Institution, Program

logger = logging.getLogger('django.request')

ERROR_COPY = {
    'ru': {
        400: ('Не удалось обработать запрос', 'Проверьте данные и попробуйте ещё раз.'),
        401: ('Требуется авторизация', 'Войдите в аккаунт, чтобы получить доступ к этой странице.'),
        403: ('Доступ закрыт', 'У вас нет прав для просмотра этой страницы.'),
        404: ('Страница не найдена', 'Возможно, адрес изменился или страница больше не существует.'),
        500: ('Временная неполадка', 'На сервере возникла ошибка. Администраторы уже в курсе и работают над восстановлением.'),
        502: ('Ошибка шлюза', 'Сервер получил некорректный ответ. Администраторы уже в курсе и работают над восстановлением.'),
        503: ('Сервис временно недоступен', 'Мы проводим технические работы. Администраторы уже в курсе и скоро восстановят работу.'),
    },
    'en': {
        400: ('We could not process that request', 'Check the details and try again.'),
        401: ('Authentication required', 'Log in to access this page.'),
        403: ('Access denied', 'You do not have permission to view this page.'),
        404: ('Page not found', 'The address may have changed or the page may no longer exist.'),
        500: ('A temporary problem occurred', 'The server encountered an error. Our administrators are aware and are working to restore service.'),
        502: ('Bad gateway', 'The server received an invalid response. Our administrators are aware and are working to restore service.'),
        503: ('Service temporarily unavailable', 'We are performing maintenance. Our administrators are aware and will restore service shortly.'),
    },
    'ky': {
        400: ('Сурамды иштетүү мүмкүн болгон жок', 'Маалыматты текшерип, кайра аракет кылыңыз.'),
        401: ('Авторизация талап кылынат', 'Бул баракка кирүү үчүн аккаунтуңузга кириңиз.'),
        403: ('Кирүүгө уруксат жок', 'Бул баракты көрүүгө уруксатыңыз жок.'),
        404: ('Баракча табылган жок', 'Дарек өзгөргөн же баракча өчүрүлгөн болушу мүмкүн.'),
        500: ('Убактылуу ката чыкты', 'Серверде ката пайда болду. Администраторлор кабардар жана кызматты калыбына келтирүүдө.'),
        502: ('Шлюз катасы', 'Сервер туура эмес жооп алды. Администраторлор кабардар жана маселени чечүүдө.'),
        503: ('Кызмат убактылуу жеткиликсиз', 'Техникалык иштер жүрүп жатат. Администраторлор кабардар жана кызматты жакында калыбына келтирет.'),
    },
}


def _error_response(request, status_code):
    language = request.LANGUAGE_CODE if request.LANGUAGE_CODE in ERROR_COPY else 'ru'
    title, message = ERROR_COPY[language][status_code]
    html = render_to_string('core/error.html', {
        'status_code': status_code,
        'title': title,
        'message': message,
        'is_server_error': status_code >= 500,
        'language': language,
    })
    return HttpResponse(html, status=status_code)


def bad_request(request, exception=None):
    return _error_response(request, 400)


def forbidden(request, exception=None):
    return _error_response(request, 403)


def unauthorized(request):
    return _error_response(request, 401)


def page_not_found(request, exception=None):
    return _error_response(request, 404)


def server_error(request):
    logger.error('FindUni returned a server error for %s', request.path)
    return _error_response(request, 500)


def bad_gateway(request):
    logger.error('FindUni bad gateway page requested for %s', request.path)
    return _error_response(request, 502)


def service_unavailable(request):
    logger.warning('FindUni service unavailable page requested for %s', request.path)
    return _error_response(request, 503)


def home(request):
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    institutions = Institution.objects.filter(approved=True).annotate(
        direction_count=Count('programs__direction', filter=~Q(programs__direction=''), distinct=True),
        review_count=Count('reviews', filter=Q(reviews__is_removed=False), distinct=True),
        review_rating=Avg('reviews__rating', filter=Q(reviews__is_removed=False)),
        starting_price=Min('programs__price'),
    ).prefetch_related('photos').order_by('-review_rating', 'name')
    if query:
        institutions = institutions.filter(Q(name__icontains=query) | Q(city__icontains=query))
    if city and city != 'Все города':
        institutions = institutions.filter(city=city)

    result_count = institutions.count() if query or city else None
    featured = []
    for institution in institutions[:3]:
        price = f'{int(institution.starting_price):,}'.replace(',', ' ') if institution.starting_price else 'уточняйте'
        photos = institution.photos.all()
        photo = None
        if photos:
            photo = photos[0].image_url or (photos[0].image.url if photos[0].image else None)
        photo = photo or institution.logo_url or (institution.logo.url if institution.logo else None)
        featured.append({
            'name': institution.name,
            'city': institution.city,
            'type': institution.get_institution_type_display(),
            'rating': institution.review_rating,
            'reviews': institution.review_count,
            'directions': institution.direction_count,
            'price': f'от ${price}' if institution.starting_price else price,
            'mark': institution.name[:1].upper(),
            'photo': photo,
            'url': reverse('institution-detail', args=[institution.pk]),
            'tone': len(featured) % 3,
        })

    cities = list(Institution.objects.filter(approved=True).order_by('city').values_list('city', flat=True).distinct())

    return render(request, 'core/home.html', {
        'featured_institutions': featured,
        'cities': cities,
        'query': query,
        'selected_city': city or {
            'en': 'All countries',
            'ky': 'Бардык өлкөлөр',
        }.get(request.LANGUAGE_CODE, 'Все страны'),
        'search_performed': bool(query or city),
        'result_count': result_count,
    })


def about(request):
    return render(request, 'core/about.html', {
        'institution_count': Institution.objects.exclude(name='').count(),
        'program_count': Program.objects.count(),
    })


def how_to_apply(request):
    return render(request, 'core/how_to_apply.html')


def language_switch(request, language):
    if language not in dict(settings.LANGUAGES):
        return HttpResponseRedirect(reverse('home'))
    redirect_to = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    if not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_to = reverse('home')

    response = HttpResponseRedirect(redirect_to)
    response.set_cookie('language', language, max_age=60 * 60 * 24 * 365, path='/', samesite='Lax', secure=request.is_secure())
    return response


def theme_switch(request, theme):
    if theme not in {'light', 'dark'}:
        return HttpResponseRedirect(reverse('home'))
    redirect_to = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    if not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_to = reverse('home')

    response = HttpResponseRedirect(redirect_to)
    response.set_cookie('theme', theme, max_age=60 * 60 * 24 * 365, path='/', httponly=True, samesite='Lax', secure=request.is_secure())
    return response


def large_text_switch(request):
    redirect_to = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    if not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_to = reverse('home')

    response = HttpResponseRedirect(redirect_to)
    if request.COOKIES.get('large_text') == '1':
        response.delete_cookie('large_text', path='/', samesite='Lax')
    else:
        response.set_cookie('large_text', '1', max_age=60 * 60 * 24 * 365, path='/', httponly=True, samesite='Lax', secure=request.is_secure())
    return response


def accessibility_switch(request, setting, value):
    allowed_values = {
        'font-size': {'normal', 'large', 'larger'},
        'contrast': {'normal', 'high'},
    }
    if value not in allowed_values.get(setting, set()):
        return HttpResponseRedirect(reverse('home'))

    redirect_to = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')
    if not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_to = reverse('home')

    response = HttpResponseRedirect(redirect_to)
    cookie_name = 'font_size' if setting == 'font-size' else 'high_contrast'
    default_value = 'normal'
    if value == default_value:
        response.delete_cookie(cookie_name, path='/', samesite='Lax')
    else:
        response.set_cookie(cookie_name, value, max_age=60 * 60 * 24 * 365, path='/', httponly=True, samesite='Lax', secure=request.is_secure())
    return response


def _inbox_return_url(request):
    redirect_to = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return reverse('home')
    return redirect_to


@login_required
@require_POST
def mark_inbox_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(_inbox_return_url(request))


@login_required
@require_POST
def mark_notification_read(request, pk):
    Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
    return redirect(_inbox_return_url(request))


@login_required
@require_POST
def delete_inbox(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect(_inbox_return_url(request))


@login_required
@require_POST
def delete_notification(request, pk):
    Notification.objects.filter(user=request.user, pk=pk).delete()
    return redirect(_inbox_return_url(request))
