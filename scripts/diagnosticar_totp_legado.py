"""Diagnostico somente leitura de segredos TOTP legados.

Nao imprima segredos; nao modifique valores nem rode migracoes automaticamente.
Uso: python scripts/diagnosticar_totp_legado.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from cryptography.fernet import InvalidToken
from django.db import connection
from encrypted_model_fields.fields import decrypt_str


def diagnosticar():
  total = 0
  protegidos = 0
  legados = 0
  invalidos = 0
  with connection.cursor() as cursor:
    cursor.execute('SELECT otp_secret FROM usuarios WHERE otp_secret IS NOT NULL')
    for (bruto,) in cursor.fetchall():
      total += 1
      texto = str(bruto)
      if texto.startswith('gAAAA'):
        try:
          decrypt_str(texto)
          protegidos += 1
        except (InvalidToken, ValueError, TypeError):
          invalidos += 1
      else:
        legados += 1
  print('Segredos TOTP preenchidos:', total)
  print('Segredos criptografados e legiveis:', protegidos)
  print('Segredos em formato legado / nao Fernet:', legados)
  print('Segredos Fernet invalidos:', invalidos)
  print('Consulta somente leitura; nenhum segredo foi exibido e nenhum registro alterado.')
  if legados or invalidos:
    print('ATENCAO: investigar em copia restaurada antes de qualquer conversao.')
    return 1
  return 0


if __name__ == '__main__':
  raise SystemExit(diagnosticar())
