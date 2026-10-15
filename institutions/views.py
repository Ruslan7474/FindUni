from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Min
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from core.models import Notification
from .forms import InstitutionForm, ProgramDocumentRequirementFormSet, ProgramFormSet, ReviewForm
from .models import Institution, Program, Review
from students.models import InstitutionFollow, StudentProfile


def institution_list(request):
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '')
    institution_type = request.GET.get('type', '')
    direction = request.GET.get('direction', '')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', 'rating')
    allowed_sort = {'rating': 'rating', 'name': 'name', 'price': 'price'}
    qs = Institution.objects.filter(approved=True).select_related('owner').prefetch_related('programs', 'photos')
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(city__icontains=query))
    if city:
        qs = qs.filter(city__icontains=city)
    if institution_type:
        qs = qs.filter(institution_type=institution_type)
    if direction:
        qs = qs.filter(Q(programs__direction__icontains=direction) | Q(programs__name__icontains=direction))
    if max_price:
        qs = qs.filter(programs__price__lte=max_price)
    if sort == 'price':
        qs = qs.annotate(minimum_price=Min('programs__price')).order_by('minimum_price', 'pk')
    else:
        qs = qs.order_by('-' + allowed_sort.get(sort, 'rating'), 'pk')
    page_obj = Paginator(qs.distinct(), 10).get_page(request.GET.get('page'))
    query_parameters = request.GET.copy()
    query_parameters.pop('page', None)
    return render(request, 'institutions/list.html', {
        'institutions': page_obj.object_list,
        'page_obj': page_obj,
        'query_parameters': query_parameters.urlencode(),
        'cities': Institution.objects.values_list('city', flat=True).distinct(),
        'types': Institution.TYPE_CHOICES,
        'sort': sort,
    })


def institution_detail(request, pk):
    institution = get_object_or_404(Institution, pk=pk, approved=True)
    is_owner = request.user.is_authenticated and institution.owner_id == request.user.pk
    return render(request, 'institutions/detail.html', {
        'institution': institution,
        'programs': institution.programs.all(),
        'reviews': institution.reviews.filter(is_removed=False).select_related('author'),
        'is_owner': is_owner,
        'program_formset': ProgramFormSet(instance=institution, prefix='programs') if is_owner else None,
        'is_following': request.user.is_authenticated and request.user.role == 'student' and InstitutionFollow.objects.filter(student=request.user, institution=institution).exists(),
        'review_form': ReviewForm(),
    })


@login_required
@require_POST
def toggle_institution_follow(request, pk):
    if request.user.role != 'student':
        raise PermissionDenied
    institution = get_object_or_404(Institution, pk=pk, approved=True)
    follow, created = InstitutionFollow.objects.get_or_create(student=request.user, institution=institution)
    if created:
        follower_profile, _ = StudentProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name()},
        )
        follower_name = (
            follower_profile.full_name if follower_profile.full_name
            else request.user.get_full_name()
            or 'Абитуриент'
        )
        Notification.objects.create(
            user=institution.owner,
            actor=request.user,
            follow=follow,
            kind='institution_follow',
            title='Новая подписка',
            body=f'{follower_name} подписался на ваше учебное заведение.',
        )
        messages.success(request, 'Заведение добавлено в подписки.')
    else:
        follow.delete()
        messages.success(request, 'Заведение удалено из подписок.')
    return redirect('institution-detail', pk=institution.pk)


@login_required
def institution_profile(request):
    if request.user.role != 'institution':
        raise PermissionDenied
    institution = get_object_or_404(Institution, owner=request.user)
    if request.method == 'POST':
        program_formset = ProgramFormSet(request.POST, instance=institution, prefix='programs')
        if program_formset.is_valid():
            new_program_forms = [
                form for form in program_formset.forms
                if not form.instance.pk and form.has_changed() and not form.cleaned_data.get('DELETE')
            ]
            with transaction.atomic():
                program_formset.save()
            if new_program_forms:
                return redirect('program-document-requirements', pk=new_program_forms[0].instance.pk)
            messages.success(request, 'Направления и программы сохранены.')
            return redirect('institution-profile')
    else:
        program_formset = ProgramFormSet(instance=institution, prefix='programs')
    return render(request, 'institutions/detail.html', {
        'institution': institution,
        'programs': institution.programs.all(),
        'reviews': institution.reviews.filter(is_removed=False).select_related('author'),
        'is_owner': True,
        'program_formset': program_formset,
        'review_form': ReviewForm(),
    })


@login_required
def program_document_requirements(request, pk):
    if request.user.role != 'institution':
        raise PermissionDenied
    program = get_object_or_404(Program, pk=pk, institution__owner=request.user)
    if request.method == 'POST':
        formset = ProgramDocumentRequirementFormSet(request.POST, instance=program, prefix='requirements')
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            messages.success(request, 'Требования к документам сохранены.')
            return redirect('institution-profile')
    else:
        formset = ProgramDocumentRequirementFormSet(instance=program, prefix='requirements')
    return render(request, 'institutions/program_documents.html', {
        'program': program,
        'formset': formset,
    })


@login_required
def add_review(request, pk):
    institution = get_object_or_404(Institution, pk=pk, approved=True)
    if request.user.role != 'student':
        raise PermissionDenied
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.institution = institution
            review.author = request.user
            review.save()
            return redirect('institution-detail', pk=pk)
    else:
        form = ReviewForm()
    return render(request, 'institutions/review_form.html', {'form': form, 'institution': institution})


@login_required
def edit_institution(request, pk):
    if request.user.role != 'institution':
        raise PermissionDenied
    institution = get_object_or_404(Institution, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = InstitutionForm(request.POST, request.FILES, instance=institution)
        if form.is_valid():
            institution = form.save()
            return redirect('dashboard')
    else:
        form = InstitutionForm(instance=institution)
    return render(request, 'institutions/edit.html', {'form': form})
