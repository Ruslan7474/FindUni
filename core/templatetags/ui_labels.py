from django import template

register = template.Library()

LABELS = {
    'en': {
        'sent': 'Submitted', 'Отправлено': 'Submitted',
        'reviewing': 'Under review', 'На рассмотрении': 'Under review',
        'documents': 'Documents required', 'Нужны документы': 'Documents required',
        'accepted': 'Accepted', 'Принято': 'Accepted',
        'rejected': 'Rejected', 'Отклонено': 'Rejected',
        'withdrawn': 'Withdrawn', 'Отозвано': 'Withdrawn',
        'college9': 'College after grade 9',
        'college11': 'College/university after grade 11',
        'university': 'University',
        'Колледж после 9 класса': 'College after grade 9',
        'Колледж-вуз после 11 класса': 'College/university after grade 11',
        'Университет': 'University',
        'school': 'School', 'Школа': 'School', 'college': 'College', 'Колледж': 'College',
        'Вуз': 'University',
        'student': 'Applicant', 'Абитуриент': 'Applicant',
        'institution': 'Educational institution', 'Учебное заведение': 'Educational institution',
        'admin': 'Administrator', 'Администратор': 'Administrator',
        'announcement': 'Announcement', 'comment': 'Comment', 'application': 'New application',
        'application_status': 'Application status', 'friend_request': 'Friend request',
        'institution_follow': 'New follower',
    },
    'ky': {
        'sent': 'Жөнөтүлдү', 'Отправлено': 'Жөнөтүлдү',
        'reviewing': 'Каралууда', 'На рассмотрении': 'Каралууда',
        'documents': 'Документтер керек', 'Нужны документы': 'Документтер керек',
        'accepted': 'Кабыл алынды', 'Принято': 'Кабыл алынды',
        'rejected': 'Четке кагылды', 'Отклонено': 'Четке кагылды',
        'withdrawn': 'Кайтарылды', 'Отозвано': 'Кайтарылды',
        'college9': '9-класстан кийинки колледж',
        'college11': '11-класстан кийинки колледж/университет',
        'university': 'Университет',
        'Колледж после 9 класса': '9-класстан кийинки колледж',
        'Колледж-вуз после 11 класса': '11-класстан кийинки колледж/университет',
        'school': 'Мектеп', 'Школа': 'Мектеп', 'college': 'Колледж', 'Колледж': 'Колледж',
        'Вуз': 'Университет',
        'student': 'Абитуриент', 'institution': 'Окуу жай', 'admin': 'Администратор',
        'announcement': 'Жарыя', 'comment': 'Комментарий', 'application': 'Жаңы арыз',
        'application_status': 'Арыздын абалы', 'friend_request': 'Достук сурамы',
        'institution_follow': 'Жаңы жазылуучу',
    },
}


@register.filter
def translate_choice(value, language):
    return LABELS.get(language, {}).get(str(value), value)