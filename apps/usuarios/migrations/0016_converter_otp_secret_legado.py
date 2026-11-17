from cryptography.fernet import InvalidToken
from django.db import migrations, transaction
from encrypted_model_fields.fields import decrypt_str, encrypt_str


# Converte segredos TOTP legados em texto puro para Fernet de forma idempotente, sem dupla cifragem.
def converter_otp_secret_legado(apps, schema_editor):
  conexao = schema_editor.connection
  tabela = conexao.ops.quote_name('usuarios')
  coluna = conexao.ops.quote_name('otp_secret')

  with conexao.cursor() as cursor:
    cursor.execute(f'SELECT id, {coluna} FROM {tabela} WHERE {coluna} IS NOT NULL')
    registros = cursor.fetchall()

  pendentes = []
  for pk, bruto in registros:
    texto = str(bruto or '')
    if not texto:
      continue
    if texto.startswith('gAAAA'):
      # Valida que o token Fernet existente é legível e nunca o cifra uma segunda vez.
      try:
        decrypt_str(texto)
      except InvalidToken as erro:
        raise RuntimeError(
          'Token Fernet ilegível em usuarios.otp_secret. Confira FIELD_ENCRYPTION_KEY.'
        ) from erro
      continue
    cifrado_bruto = encrypt_str(texto)
    cifrado = cifrado_bruto.decode('utf-8') if isinstance(cifrado_bruto, bytes) else str(cifrado_bruto)
    if decrypt_str(cifrado) != texto:
      raise RuntimeError('Falha ao validar leitura Fernet do otp_secret convertido.')
    pendentes.append((cifrado, pk, texto))

  if not pendentes:
    return

  with transaction.atomic(using=conexao.alias):
    with conexao.cursor() as cursor:
      for cifrado, pk, original in pendentes:
        cursor.execute(
          f'UPDATE {tabela} SET {coluna} = %s WHERE id = %s AND {coluna} = %s',
          [cifrado, pk, original],
        )


class Migration(migrations.Migration):
  dependencies = [
    ('usuarios', '0015_proteger_consentimentos'),
  ]

  operations = [
    migrations.RunPython(converter_otp_secret_legado, migrations.RunPython.noop),
  ]
