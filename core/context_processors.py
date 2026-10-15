from .models import Notification


def inbox(request):
    if not request.user.is_authenticated:
        return {'inbox_notifications': (), 'inbox_unread_count': 0}

    notifications = list(
        Notification.objects.filter(user=request.user)
        .select_related(
            'application__institution',
            'application__program',
            'comment',
            'actor__student_profile',
            'actor__institution_profile',
            'friendship__from_student__student_profile',
            'follow__student__student_profile',
            'follow__institution',
        )
        .order_by('-created_at', '-pk')[:30]
    )
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {
        'inbox_notifications': notifications,
        'inbox_unread_count': unread_count,
    }
