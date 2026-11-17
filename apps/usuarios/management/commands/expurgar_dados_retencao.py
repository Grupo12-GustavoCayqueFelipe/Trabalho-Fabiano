import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.atividades.models import Entrega
from apps.comunicacao.models import Mensagem
from apps.usuarios.models import Usuario, registrar_operacao

TEXTO_ANONIMIZADO = '[Conteúdo expurgado após prazo de retenção]'
ASSUNTO_ANONIMIZADO = '[Expurgado]'


class Command(BaseCommand):
  help = (
    'Anonimiza textos livres e remove anexos PDF de contas já desidentificadas '
    'após o prazo de retenção institucional (padrão: modo --dry-run).'
  )

  def add_arguments(self, parser):
    parser.add_argument(
      '--dias-retencao',
      type=int,
      default=365,
      help='Quantidade mínima de dias desde o registro para permitir o expurgo (padrão: 365).',
    )
    parser.add_argument(
      '--dry-run',
      action='store_true',
      dest='dry_run',
      default=None,
      help='Executa apenas simulação sem alterar banco nem arquivos (padrão).',
    )
    parser.add_argument(
      '--executar',
      action='store_true',
      default=False,
      help='Aplica efetivamente a anonimização e a remoção de anexos expirados.',
    )

  def handle(self, *args, **options):
    dias_retencao = options['dias_retencao']
    if dias_retencao < 0:
      raise CommandError('O parâmetro --dias-retencao não pode ser negativo.')

    # Por segurança, opera em dry-run por padrão a menos que --executar ou dry_run=False seja informado.
    if options.get('executar'):
      dry_run = False
    elif options.get('dry_run') is not None:
      dry_run = bool(options['dry_run'])
    else:
      dry_run = True

    limite = timezone.now() - datetime.timedelta(days=dias_retencao)
    contas_desidentificadas = Usuario.objects.filter(
      is_active=False,
      email__endswith='@example.invalid',
    )

    mensagens_qs = Mensagem.objects.filter(
      remetente__in=contas_desidentificadas,
      enviada_em__lte=limite,
    ).exclude(texto=TEXTO_ANONIMIZADO, assunto=ASSUNTO_ANONIMIZADO)

    entregas_qs = Entrega.objects.filter(
      aluno__usuario__in=contas_desidentificadas,
      entregue_em__lte=limite,
    ).filter(
      ~Q(resposta=TEXTO_ANONIMIZADO) | (Q(arquivo__isnull=False) & ~Q(arquivo=''))
    )

    total_mensagens = mensagens_qs.count()
    total_entregas = entregas_qs.count()

    if dry_run:
      self.stdout.write(
        f'[DRY-RUN] Mensagens elegíveis: {total_mensagens} | '
        f'Entregas elegíveis: {total_entregas} (nenhum dado alterado).'
      )
      return

    arquivos_para_remover = []
    with transaction.atomic():
      for msg in mensagens_qs.select_for_update():
        msg.assunto = ASSUNTO_ANONIMIZADO
        msg.texto = TEXTO_ANONIMIZADO
        msg.save(update_fields=['assunto', 'texto'])

      for entrega in entregas_qs.select_for_update():
        if entrega.arquivo and entrega.arquivo.name:
          arquivos_para_remover.append((entrega.arquivo.storage, entrega.arquivo.name))
          entrega.arquivo = None
        entrega.resposta = TEXTO_ANONIMIZADO
        entrega.save(update_fields=['resposta', 'arquivo'])

      registrar_operacao(None, 'EXPURGO_RETENCAO_LGPD', total_mensagens + total_entregas)

    for storage, nome_arquivo in arquivos_para_remover:
      try:
        storage.delete(nome_arquivo)
      except OSError:
        pass

    self.stdout.write(
      f'Expurgo concluído: {total_mensagens} mensagens e {total_entregas} entregas anonimizadas.'
    )
