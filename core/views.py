from django.conf import settings
from django.db.models import Avg, Count, Min, Q
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .models import Notification
from institutions.models import Institution, Program


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
        photo = photos[0].image.url if photos else institution.logo.url if institution.logo else None
        featured.append({
            'name': institution.name,
            'city': institution.city,
            'type': institution.get_institution_type_display(),
            'rating': institution.review_rating,
            'reviews': institution.review_count,
            'directions': institution.direction_count,
            'price': f'от {price} сом' if institution.starting_price else price,
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
        'selected_city': city or 'Все города',
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
    response = HttpResponseRedirect(reverse('home'))
    response.set_cookie('language', language)
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
