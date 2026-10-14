from django.utils import translation


class RussianAdminLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin/') and request.path != '/admin':
            return self.get_response(request)

        previous_language = translation.get_language()
        translation.activate('ru')
        request.LANGUAGE_CODE = 'ru'
        try:
            return self.get_response(request)
        finally:
            if previous_language:
                translation.activate(previous_language)
            else:
                translation.deactivate()
