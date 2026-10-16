from django.contrib.admin.apps import AdminConfig


# Usa o Django Admin protegido pelo segundo fator do EduControll.
class EduAdminConfig(AdminConfig):
    default_site = 'core.admin_site.EduAdminSite'
