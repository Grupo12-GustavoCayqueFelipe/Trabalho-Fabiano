"""
Confere os campos pessoais alterados para Fernet na migration 0010.
Não exibe dados pessoais nem modifica o banco sem uma confirmação explícita.
Uso: python scripts/verificar_criptografia_legada.py
     python scripts/verificar_criptografia_legada.py --corrigir --backup-confirmado
"""
import argparse
import os
import sys
from pathlib import Path

# Executando como arquivo direto, também localiza a pasta core do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

# Permite executar este script diretamente a partir da raiz do projeto.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from cryptography.fernet import InvalidToken
from django.db import connection, transaction
from encrypted_model_fields.fields import decrypt_str
from apps.usuarios.models import Aluno, Professor, Responsavel


# Somente estas colunas foram convertidas pela migration 0010.
CAMPOS = [
  (Aluno, ('data_nascimento', 'telefone', 'endereco')),
  (Professor, ('telefone',)),
  (Responsavel, ('telefone',)),
]


def verificar(corrigir=False):
  pendentes = []
  protegidos = 0

  # Primeiro confere todos os registros; só depois permite escrita.
  for Modelo, campos in CAMPOS:
    tabela = connection.ops.quote_name(Modelo._meta.db_table)
    nomes = ['id', *campos]
    consulta = ', '.join(connection.ops.quote_name(nome) for nome in nomes)

    with connection.cursor() as cursor:
      cursor.execute(f'SELECT {consulta} FROM {tabela}')
      registros = cursor.fetchall()

    for registro in registros:
      pk = registro[0]
      for nome, bruto in zip(campos, registro[1:]):
        if bruto is None:
          continue
        valor = bruto.isoformat() if hasattr(bruto, 'isoformat') else str(bruto)

        # Tokens Fernet válidos não devem ser criptografados novamente.
        if valor.startswith('gAAAA'):
          try:
            decrypt_str(valor)
          except InvalidToken as erro:
            raise RuntimeError(
              f'Valor criptografado ilegível em {Modelo.__name__}.{nome}. '
              'Confira FIELD_ENCRYPTION_KEY antes de continuar.'
            ) from erro
          protegidos += 1
          continue

        campo = Modelo._meta.get_field(nome)
        # A validação do tipo impede converter uma data corrompida silenciosamente.
        try:
          campo.to_python(valor)
        except (ValueError, TypeError) as erro:
          raise RuntimeError(
            f'Valor legado inválido em {Modelo.__name__}.{nome}. '
            'Interrompido sem aplicar alterações.'
          ) from erro
        pendentes.append((Modelo, pk, nome, valor))

  print(f'Valores já criptografados: {protegidos}')
  print(f'Valores legados sem criptografia: {len(pendentes)}')
  if not corrigir:
    print('Somente verificação. Nenhum dado foi alterado.')
    return len(pendentes)

  # Cada registro só é alterado se continuar igual ao valor inspecionado.
  with transaction.atomic():
    for Modelo, pk, nome, valor in pendentes:
      campo = Modelo._meta.get_field(nome)
      cifrado = campo.get_db_prep_save(campo.to_python(valor), connection)
      tabela = connection.ops.quote_name(Modelo._meta.db_table)
      coluna = connection.ops.quote_name(nome)
      with connection.cursor() as cursor:
        cursor.execute(
          f'UPDATE {tabela} SET {coluna} = %s WHERE id = %s AND {coluna} = %s',
          [cifrado, pk, valor]
        )
        if cursor.rowcount != 1:
          raise RuntimeError('Registro alterado durante a conferência. Transação revertida.')
  print(f'Valores legados regravados com Fernet: {len(pendentes)}')
  return 0


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Verifica criptografia dos dados anteriores à migration 0010.')
  parser.add_argument('--corrigir', action='store_true', help='Regrava valores legados após backup.')
  parser.add_argument('--backup-confirmado', action='store_true', help='Confirma que existe backup testado.')
  args = parser.parse_args()

  if args.corrigir and not args.backup_confirmado:
    parser.error('Antes de --corrigir, faça backup validado e informe --backup-confirmado.')
  verificar(corrigir=args.corrigir)
