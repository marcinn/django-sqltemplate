from django.template.utils import get_app_template_dirs
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.core.exceptions import SuspiciousFileOperation
from django.utils._os import safe_join


class Loader(FilesystemLoader):
    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name", when appended to each
        directory in "template_dirs". Any paths that don't lie inside one of the
        template dirs are excluded from the result set, for security reasons.
        """
        if not template_dirs:
            template_dirs = self.get_dirs()
        for template_dir in template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except SuspiciousFileOperation:
                # The joined path was located outside of this template_dir
                # (it might be inside another one, so this isn't fatal).
                pass

    def get_dirs(self):
        return get_app_template_dirs('sqltemplates')
