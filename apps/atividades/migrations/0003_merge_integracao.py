from django.db import migrations


# Concilia anexos e pontuação com o histórico de correções e atrasos.
class Migration(migrations.Migration):
    dependencies = [
        ('atividades', '0002_historico_de_correcoes_e_atraso'),
        ('atividades', '0002_atividade_valor_nota_entrega_arquivo'),
    ]

    # Não desfaz nem repete migrations já aplicadas no Supabase.
    operations = []
