from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from applications.models import Application
from core.models import Notification
from institutions.models import Institution
from .forms import AcademicGradeForm, CommentForm, EducationEntryForm, StudentProfileForm, TestScoreForm
from .models import AcademicGrade, Comment, CommentVote, EducationEntry, InstitutionFollow, StudentFriendship, StudentProfile, TestScore


def _profile_comments(profile, viewer):
    votes = CommentVote.objects.filter(user=viewer) if viewer.is_authenticated else CommentVote.objects.none()
    return Comment.objects.filter(profile=profile, is_removed=False).select_related(
        'author', 'author__student_profile',
    ).annotate(
        like_count=Count('votes', filter=Q(votes__value='like')),
        dislike_count=Count('votes', filter=Q(votes__value='dislike')),
    ).prefetch_related(Prefetch('votes', queryset=votes, to_attr='viewer_votes'))


def _comment_threads(profile, viewer):
    comments = _profile_comments(profile, viewer)
    replies = _profile_comments(profile, viewer).filter(parent__isnull=False).order_by('created_at', 'pk')
    return comments.filter(parent__isnull=True).order_by('created_at', 'pk').prefetch_related(
        Prefetch('replies', queryset=replies, to_attr='visible_replies'),
    )


def _subject_grade_wheels(grades):
    grade_cards = []
    normalized_scores = []
    for grade in grades:
        raw_value = grade.grade.strip().replace(',', '.')
        parts = raw_value.split('/', maxsplit=1)
        try:
            score = Decimal(parts[0].strip())
            maximum = Decimal(parts[1].strip()) if len(parts) == 2 else Decimal('5')
            if not score.is_finite() or not maximum.is_finite() or maximum <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            grade_cards.append({
                'subject': grade.subject,
                'value': grade.grade,
                'progress': 0,
            })
            continue

        normalized_score = max(Decimal('0'), min(Decimal('5'), score / maximum * Decimal('5')))
        progress = max(Decimal('0'), min(Decimal('100'), score / maximum * Decimal('100')))
        score_label = format(score.normalize(), 'f')
        maximum_label = format(maximum.normalize(), 'f')
        grade_cards.append({
            'subject': grade.subject,
            'value': f'{score_label}/{maximum_label}',
            'progress': int(progress),
        })
        normalized_scores.append(normalized_score)

    gpa = None
    if normalized_scores:
        average = sum(normalized_scores) / len(normalized_scores)
        gpa = f'{average.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)}/5'
    return grade_cards, gpa


def student_list(request):
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    institution = request.GET.get('institution', '').strip()
    qs = StudentProfile.objects.select_related('user').prefetch_related('education', 'comments')
    if query:
        qs = qs.filter(
            Q(full_name__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(city__icontains=query)
            | Q(education__institution_name__icontains=query)
        )
    if city:
        qs = qs.filter(city=city)
    if institution:
        qs = qs.filter(education__institution_name__icontains=institution)
    page_obj = Paginator(qs.distinct().order_by('pk'), 10).get_page(request.GET.get('page'))
    query_parameters = request.GET.copy()
    query_parameters.pop('page', None)
    cities = StudentProfile.objects.exclude(city='').order_by('city').values_list('city', flat=True).distinct()
    return render(request, 'students/list.html', {
        'students': page_obj.object_list,
        'page_obj': page_obj,
        'query_parameters': query_parameters.urlencode(),
        'cities': cities,
        'selected_city': city,
        'institution_query': institution,
    })


def student_detail(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    preview_as_guest = request.GET.get('view') == 'guest'
    is_owner = request.user.is_authenticated and profile.user_id == request.user.pk
    is_admin = request.user.is_authenticated and request.user.role == 'admin'
    has_application = request.user.is_authenticated and request.user.role == 'institution' and Application.objects.filter(
        student=profile.user,
        institution__owner=request.user,
    ).exists()
    can_view_full = not preview_as_guest and (is_owner or is_admin or has_application)
    subject_grade_wheels, overall_gpa = _subject_grade_wheels(profile.grades.all()) if can_view_full else ([], None)
    friendship_state = None
    can_interact_comments = (
        request.user.is_authenticated
        and request.user.role in {'student', 'institution'}
        and not is_owner
        and not preview_as_guest
    )
    if request.user.is_authenticated and request.user.role == 'student' and not is_owner:
        outgoing = StudentFriendship.objects.filter(from_student=request.user, to_student=profile.user).first()
        incoming = StudentFriendship.objects.filter(from_student=profile.user, to_student=request.user).first()
        if any(relation and relation.status == 'accepted' for relation in (outgoing, incoming)):
            friendship_state = 'friends'
        elif incoming and incoming.status == 'pending':
            friendship_state = 'received'
        elif outgoing and outgoing.status == 'pending':
            friendship_state = 'sent'
    return render(request, 'students/detail.html', {
        'profile': profile,
        'is_owner': is_owner,
        'can_view_full': can_view_full,
        'subject_grade_wheels': subject_grade_wheels,
        'overall_gpa': overall_gpa,
        'preview_as_guest': preview_as_guest,
        'display_name': profile.full_name or profile.user.get_full_name(),
        'comments': _comment_threads(profile, request.user),
        'comment_count': profile.comments.filter(is_removed=False).count(),
        'comment_form': CommentForm(),
        'can_interact_comments': can_interact_comments,
        'education': profile.education.all(),
        'friendship_state': friendship_state,
    })


@login_required
def profile(request):
    if request.user.role != 'student':
        raise PermissionDenied
    profile_obj, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name()},
    )
    education_form = EducationEntryForm()
    test_score_form = TestScoreForm()
    grade_form = AcademicGradeForm()
    open_form = ''
    if request.method == 'POST':
        open_form = request.POST.get('profile_action', '')
        form_configs = {
            'education': (EducationEntryForm, EducationEntry, 'Запись об образовании добавлена.'),
            'test_score': (TestScoreForm, TestScore, 'Результат добавлен.'),
            'grade': (AcademicGradeForm, AcademicGrade, 'Оценка добавлена.'),
        }
        if open_form in form_configs:
            form_class, model_class, success_message = form_configs[open_form]
            bound_form = form_class(request.POST)
            if bound_form.is_valid():
                entry = bound_form.save(commit=False)
                entry.profile = profile_obj
                entry.save()
                messages.success(request, success_message)
                return redirect('student-profile')
            if open_form == 'education':
                education_form = bound_form
            elif open_form == 'test_score':
                test_score_form = bound_form
            else:
                grade_form = bound_form

    completion_checks = (
        bool(profile_obj.full_name),
        bool(profile_obj.avatar),
        bool(profile_obj.date_of_birth),
        bool(profile_obj.city),
        bool(profile_obj.nationality),
        bool(profile_obj.citizenship),
        bool(profile_obj.bio),
        bool(profile_obj.interests),
        bool(profile_obj.languages),
        profile_obj.education.exists(),
        profile_obj.test_scores.exists(),
        profile_obj.grades.exists(),
    )
    subject_grade_wheels, overall_gpa = _subject_grade_wheels(profile_obj.grades.all())
    friendships = StudentFriendship.objects.filter(
        Q(from_student=request.user) | Q(to_student=request.user),
    ).select_related('from_student', 'to_student')
    friends = []
    incoming_friend_requests = []
    outgoing_friend_requests = []
    for friendship in friendships:
        other_user = friendship.to_student if friendship.from_student_id == request.user.pk else friendship.from_student
        other_profile = StudentProfile.objects.filter(user=other_user).first()
        entry = {'user': other_user, 'profile': other_profile}
        if friendship.status == 'accepted':
            friends.append(entry)
        elif friendship.to_student_id == request.user.pk:
            incoming_friend_requests.append(entry)
        else:
            outgoing_friend_requests.append(entry)
    return render(request, 'students/profile.html', {
        'profile': profile_obj,
        'display_name': profile_obj.full_name or request.user.get_full_name(),
        'education': profile_obj.education.all(),
        'test_scores': profile_obj.test_scores.all(),
        'grades': profile_obj.grades.all(),
        'subject_grade_wheels': subject_grade_wheels,
        'overall_gpa': overall_gpa,
        'applications': request.user.applications.select_related('institution', 'program').all(),
        'friends': friends,
        'incoming_friend_requests': incoming_friend_requests,
        'outgoing_friend_requests': outgoing_friend_requests,
        'followed_institutions': request.user.institution_follows.select_related('institution').all(),
        'comments': _comment_threads(profile_obj, request.user),
        'comment_count': profile_obj.comments.filter(is_removed=False).count(),
        'can_interact_comments': False,
        'education_form': education_form,
        'test_score_form': test_score_form,
        'grade_form': grade_form,
        'open_form': open_form,
        'profile_completion': round(sum(completion_checks) * 100 / len(completion_checks)),
    })


@login_required
@require_POST
def manage_friend(request, pk):
    if request.user.role != 'student':
        raise PermissionDenied
    target = get_object_or_404(
        StudentProfile.objects.select_related('user'),
        user_id=pk,
    )
    if target.user_id == request.user.pk:
        raise PermissionDenied

    action = request.POST.get('action')
    if action == 'request':
        reverse_request = StudentFriendship.objects.filter(
            from_student=target.user,
            to_student=request.user,
            status='pending',
        ).first()
        outgoing, created = StudentFriendship.objects.get_or_create(
            from_student=request.user,
            to_student=target.user,
            defaults={'status': 'accepted' if reverse_request else 'pending'},
        )
        if reverse_request:
            reverse_request.status = 'accepted'
            reverse_request.save(update_fields=['status'])
            Notification.objects.filter(user=request.user, friendship=reverse_request).update(is_read=True)
            if not created and outgoing.status != 'accepted':
                outgoing.status = 'accepted'
                outgoing.save(update_fields=['status'])
            messages.success(request, 'Теперь вы друзья.')
        elif created:
            sender_profile, _ = StudentProfile.objects.get_or_create(
                user=request.user,
                defaults={'full_name': request.user.get_full_name()},
            )
            sender_name = (
                sender_profile.full_name if sender_profile.full_name
                else request.user.get_full_name()
                or 'Абитуриент'
            )
            Notification.objects.create(
                user=target.user,
                actor=request.user,
                friendship=outgoing,
                kind='friend_request',
                title='Запрос дружбы',
                body=f'{sender_name} хочет добавить вас в друзья.',
            )
            messages.success(request, 'Запрос дружбы отправлен.')
        else:
            messages.info(request, 'Запрос дружбы уже отправлен.')
    elif action == 'accept':
        with transaction.atomic():
            incoming = StudentFriendship.objects.select_for_update().filter(
                from_student=target.user,
                to_student=request.user,
                status='pending',
            ).first()
            if incoming:
                incoming.status = 'accepted'
                incoming.save(update_fields=['status'])
                Notification.objects.filter(user=request.user, friendship=incoming).update(is_read=True)
                outgoing, created = StudentFriendship.objects.get_or_create(
                    from_student=request.user,
                    to_student=target.user,
                    defaults={'status': 'accepted'},
                )
                if not created and outgoing.status != 'accepted':
                    outgoing.status = 'accepted'
                    outgoing.save(update_fields=['status'])
        if incoming:
            messages.success(request, 'Запрос принят. Теперь вы друзья.')
        elif StudentFriendship.objects.filter(
            Q(from_student=request.user, to_student=target.user)
            | Q(from_student=target.user, to_student=request.user),
            status='accepted',
        ).exists():
            messages.info(request, 'Вы уже друзья.')
        else:
            messages.info(request, 'Запрос уже обработан или отменён. Обновите страницу.')
    elif action == 'remove':
        StudentFriendship.objects.filter(
            Q(from_student=request.user, to_student=target.user)
            | Q(from_student=target.user, to_student=request.user),
        ).delete()
        messages.success(request, 'Связь удалена из списка друзей.')
    else:
        raise PermissionDenied
    return redirect('student-detail', pk=target.pk)


@login_required
def edit_profile(request):
    if request.user.role != 'student':
        raise PermissionDenied
    profile_obj = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            profile_obj = form.save()
            name_parts = profile_obj.full_name.strip().split(maxsplit=1)
            request.user.first_name = name_parts[0] if name_parts else ''
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            request.user.save(update_fields=['first_name', 'last_name'])
            return redirect('dashboard')
    else:
        form = StudentProfileForm(instance=profile_obj)
    return render(request, 'students/edit_profile.html', {'form': form})


@login_required
@require_POST
def add_comment(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.user.role not in {'student', 'institution'} or request.user.pk == profile.user_id:
        raise PermissionDenied
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.profile = profile
        comment.author = request.user
        parent_id = request.POST.get('parent_id')
        if parent_id:
            comment.parent = get_object_or_404(
                Comment,
                pk=parent_id,
                profile=profile,
                parent__isnull=True,
                is_removed=False,
            )
        comment.save()
        Notification.objects.create(
            user=profile.user,
            kind='comment',
            title='Комментарий к вашей странице',
            body=f'{request.user.get_full_name() or request.user.email or "Пользователь"} оставил комментарий: {comment.text[:180]}',
            comment=comment,
            actor=request.user,
        )
    else:
        messages.error(request, 'Комментарий не отправлен. Проверьте текст (до 500 символов).')
    return redirect(f'{reverse("student-detail", args=[pk])}#comments')


@login_required
@require_POST
def vote_comment(request, comment_pk):
    if request.user.role not in {'student', 'institution'}:
        raise PermissionDenied
    comment = get_object_or_404(Comment.objects.select_related('profile'), pk=comment_pk, is_removed=False)
    if request.user.pk == comment.profile.user_id:
        raise PermissionDenied
    value = request.POST.get('value')
    if value not in dict(CommentVote.VALUE_CHOICES):
        return HttpResponseBadRequest('Invalid reaction')
    vote = CommentVote.objects.filter(comment=comment, user=request.user).first()
    selected_value = value
    if vote is None:
        CommentVote.objects.create(comment=comment, user=request.user, value=value)
    elif vote.value == value:
        vote.delete()
        selected_value = None
    else:
        vote.value = value
        vote.save(update_fields=['value'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        counts = comment.votes.aggregate(
            likes=Count('id', filter=Q(value='like')),
            dislikes=Count('id', filter=Q(value='dislike')),
        )
        return JsonResponse({
            'like_count': counts['likes'],
            'dislike_count': counts['dislikes'],
            'selected': selected_value,
        })
    return redirect(f'{reverse("student-detail", args=[comment.profile_id])}#comments')
