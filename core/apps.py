from django.contrib.admin.apps import AdminConfig


# Substitui o admin padrão pelo admin que exige o segundo fator (TOTP).
class EduAdminConfig(AdminConfig):
    default_site = 'core.admin_site.EduAdminSite'