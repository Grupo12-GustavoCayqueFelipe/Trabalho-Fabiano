# Configuração usada SÓ para rodar os testes: banco SQLite em memória, nunca toca no Supabase.
# Uso: python manage.py test --settings=core.settings_test
from .settings import *

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

# Hash de senha rápido, só para os testes não demorarem (em produção continua PBKDF2)
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Os testes usam http://testserver, então não pode redirecionar para https nem exigir cookie seguro
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Nos testes, não exige o manifesto do collectstatic.
# Mantém a configuração de produção inalterada.
# Nunca usa o armazenamento S3 da escola durante os testes.
MEDIA_ROOT = BASE_DIR / '.test-media'
STORAGES = {
    **STORAGES,
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
# Impede que a suíte use Redis ou SMTP externos definidos no .env da máquina.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'educontroll-testes-isolados',
    },
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
