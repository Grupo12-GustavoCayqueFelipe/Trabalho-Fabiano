"""
Configuração EXCLUSIVA da instância descartável de DAST no GitHub Actions.

Não usar em Render/produção. Usa SQLite local, caches em memória, sem Supabase,
Redis, SMTP real ou dados pessoais. A varredura acessa apenas HTTP/localhost.

O settings.py original exige integrações de produção quando DEBUG=False. A
variável é definida somente durante o import inicial para carregar as opções
de teste isoladas. Depois o Django atende requisições com DEBUG=False.
"""

import os

os.environ.setdefault('DEBUG', 'True')

from .settings_test import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

# SQLite e arquivos estáticos/mídia em /tmp para compatibilidade com container não-privilegiado (appuser).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(os.getenv('SQLITE_PATH', '/tmp/edudast-inicial.sqlite3')),
    },
}

STATIC_ROOT = Path(os.getenv('STATIC_ROOT', '/tmp/staticfiles'))
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', '/tmp/media'))

# Segredos efêmeros gerados no workflow; nunca são os valores de produção.
SECRET_KEY = os.environ['SECRET_KEY']
FIELD_ENCRYPTION_KEY = os.environ['FIELD_ENCRYPTION_KEY']

# HTTP estritamente local. Esses overrides não valem para o Render.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Usa PBKDF2 (produção) em vez do MD5 otimizado para testes unitários.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.PBKDF2PasswordHasher']
