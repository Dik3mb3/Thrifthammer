import rcssmin
from django.core.files.base import ContentFile
from whitenoise.storage import CompressedManifestStaticFilesStorage


class _MinifyingStorageWrapper:
    """Wraps a staticfiles source storage to return minified CSS on read."""

    def __init__(self, wrapped):
        self._wrapped = wrapped

    def open(self, name, mode='rb'):
        f = self._wrapped.open(name, mode)
        if name.endswith('.css'):
            raw = f.read()
            f.close()
            return ContentFile(rcssmin.cssmin(raw.decode('utf-8')).encode('utf-8'), name=name)
        return f

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)


class MinifiedCompressedStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """WhiteNoise storage that minifies CSS files before hashing and compression."""

    def post_process(self, paths, dry_run=False, **options):
        minifying_paths = {
            name: (_MinifyingStorageWrapper(storage), path)
            for name, (storage, path) in paths.items()
        }
        yield from super().post_process(minifying_paths, dry_run, **options)
