from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateApplicationStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.PRIVATE_MEDIA_ROOT)
        kwargs.setdefault('base_url', None)
        kwargs.setdefault('file_permissions_mode', 0o600)
        kwargs.setdefault('directory_permissions_mode', 0o700)
        super().__init__(*args, **kwargs)

    def url(self, name):
        raise NotImplementedError('Private application documents have no public URL.')