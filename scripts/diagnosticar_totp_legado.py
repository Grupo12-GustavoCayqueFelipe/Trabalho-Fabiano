"""Diagnostico e conversao opcional controlada de segredos TOTP legados.

Nao imprima segredos; so converte valores legados quando --corrigir e --backup-confirmado forem informados.
Uso: python scripts/diagnosticar_totp_legado.py
     python scripts/diagnosticar_totp_legado.py --corrigir --backup-confirmado
"""
import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from cryptography.fernet import InvalidToken
from django.db import connection, transaction
from encrypted_model_fields.fields import decrypt_str, encrypt_str


def diagnosticar(corrigir=False):
  total = 0
  protegidos = 0
  legados = 0
  invalidos = 0
  pendentes = []
  with connection.cursor() as cursor:
    cursor.execute('SELECT id, otp_secret FROM usuarios WHERE otp_secret IS NOT NULL')
    for pk, bruto in cursor.fetchall():
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
        pendentes.append((pk, texto))
  print('Segredos TOTP preenchidos:', total)
  print('Segredos criptografados e legiveis:', protegidos)
  print('Segredos em formato legado / nao Fernet:', legados)
  print('Segredos Fernet invalidos:', invalidos)
  if invalidos:
    print('ATENCAO: existem tokens Fernet invalidos. Verifique FIELD_ENCRYPTION_KEY.')
    return 1
  if not corrigir:
    print('Consulta somente leitura; nenhum segredo foi exibido e nenhum registro alterado.')
    if legados:
      print('ATENCAO: investigar em copia restaurada antes de qualquer conversao.')
      return 1
    return 0

  with transaction.atomic():
    with connection.cursor() as cursor:
      for pk, original in pendentes:
        cifrado_bruto = encrypt_str(original)
        cifrado = cifrado_bruto.decode('utf-8') if isinstance(cifrado_bruto, bytes) else str(cifrado_bruto)
        if decrypt_str(cifrado) != original:
          raise RuntimeError('Falha ao validar leitura Fernet do segredo convertido.')
        cursor.execute(
          'UPDATE usuarios SET otp_secret = %s WHERE id = %s AND otp_secret = %s',
          [cifrado, pk, original],
        )
        if cursor.rowcount != 1:
          raise RuntimeError('Registro alterado durante a conversao. Transacao revertida.')
  print('Segredos legados convertidos com Fernet:', len(pendentes))
  return 0


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Diagnostica ou converte segredos TOTP legados.')
  parser.add_argument('--corrigir', action='store_true', help='Converte segredos em texto puro para Fernet.')
  parser.add_argument('--backup-confirmado', action='store_true', help='Confirma backup validado antes da escrita.')
  args = parser.parse_args()
  if args.corrigir and not args.backup_confirmado:
    parser.error('Informe --backup-confirmado junto com --corrigir.')
  raise SystemExit(diagnosticar(corrigir=args.corrigir))
