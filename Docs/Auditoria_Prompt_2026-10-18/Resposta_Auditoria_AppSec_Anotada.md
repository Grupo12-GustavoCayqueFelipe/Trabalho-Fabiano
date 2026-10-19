# Auditoria AppSec — EduControll v1.0.0

Pendências identificadas

18/10/2026 · Revisão do ZIP enviado

A análise estática abrangeu os seis módulos do projeto, incluindo `usuarios`, `academico`, `atividades`, `comunicacao`, `avaliacoes` e `frequencia`, além de configurações, templates, migrations, scripts e testes.

**Resumo dos achados da auditoria original:** 4 altos, 8 médios, 0 baixos e 0 críticos.

Limitação de validação: foi possível examinar o código e executar verificações estáticas de sintaxe, URLs, templates e grafo de migrations. Não foi possível executar a suíte Django nem validar o estado efetivo do PostgreSQL, Redis ou Render. Os achados condicionados a dados legados ou ao ambiente de produção são identificados como tais.

## Vulnerabilidades e erros de severidade alta

### [Severidade: Alto] RBAC permite conservar privilégios de professor após mudança de perfil

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** Os pontos de autorização por relacionamento `professor` ainda não exigem uniformemente `perfil=PROF`. Não marcar como resolvido.

Vetor: Segurança

Localização: `apps/atividades/views.py`, linhas 43–52 e 86–92; `apps/avaliacoes/views.py`, linhas 39–44; `apps/frequencia/views.py`, linhas 24–30; `apps/comunicacao/views.py`, linhas 116–119.

Risco/Impacto: Diversas views utilizam `hasattr(request.user, 'professor')` como critério de autorização, sem exigir simultaneamente `request.user.perfil == 'PROF'`.

Se um administrador alterar o perfil de uma conta de `PROF` para `ALUNO`, mas preservar o registro relacionado em `Professor`, o usuário ainda poderá realizar operações docentes por requisições diretas. Isso inclui criar atividades, lançar notas, registrar frequência e enviar comunicados, desde que os demais vínculos consultados permaneçam válidos.

A alteração do perfil por si só não revoga os privilégios efetivos.

Remediação: Exigir cumulativamente o perfil `PROF`, conta ativa e relacionamento docente válido em todas as operações privilegiadas. A mudança de perfil também deve revogar ou desativar explicitamente os vínculos e permissões incompatíveis. Acrescentar um teste que altere o perfil de um professor existente e tente executar as rotas de escrita.

### [Severidade: Alto] Autorização docente não distingue atribuição de professor por turma

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** O vínculo entre disciplina e professor permanece independente da turma; a política de autorização precisa ser definida e implementada.

Vetor: Segurança / Estrutura

Localização: `apps/academico/models.py`, linhas 75–84; `apps/atividades/views.py`, linhas 29–31; `apps/avaliacoes/views.py`, linhas 38–44; `apps/comunicacao/views.py`, linhas 24–39.

Risco/Impacto: O modelo `Disciplina` mantém separadamente um relacionamento com professores e outro com turmas. Não existe, nesse relacionamento, a identificação de qual professor leciona aquela disciplina em cada turma.

Consequentemente, quando a disciplina Matemática estiver vinculada às turmas 7A e 7B, um professor associado à disciplina poderá ser considerado autorizado nas duas, mesmo que operacionalmente lecione apenas na 7A.

Essa combinação pode permitir consulta de informações escolares, lançamento de notas e envio de mensagens fora da turma realmente atribuída ao docente.

Remediação: Caso professores não devam atuar automaticamente em todas as turmas de uma disciplina, representar explicitamente a atribuição `professor + disciplina + turma`, por exemplo com uma tabela de vínculo. Utilizar esse vínculo nas consultas e nas ações de escrita. Criar teste com dois professores responsáveis pela mesma disciplina em turmas distintas, verificando que um não pode modificar dados da outra turma.

### [Severidade: Alto] Migrations antigas não convertem registros existentes para Fernet

**Situação conferida na `main` (`9c3cc66`): VERIFICAÇÃO FEITA NO BANCO.** O esquema novo declara campos cifrados e há diagnósticos, mas isso não comprova a conversão dos valores legados existentes no Supabase.

Vetor: Banco / LGPD / Segurança

Localização: `apps/usuarios/migrations/0010_alter_aluno_data_nascimento_alter_aluno_endereco_and_more.py`, linhas 13–39; `apps/usuarios/migrations/0013_alter_usuario_otp_secret.py`, linhas 13–18.

Risco/Impacto: As duas migrations alteram tipos de campo comuns para campos criptografados sem uma operação de migração dos valores preexistentes.

Isso não significa que registros novos estejam sem criptografia. O problema ocorre com registros gravados antes da conversão: eles podem permanecer em texto simples no banco, embora o model atual já declare um `EncryptedField`.

O impacto é particularmente relevante para `Usuario.otp_secret`, pois uma chave TOTP legada pode continuar exposta no armazenamento.

O projeto possui um script de verificação e correção para parte dos dados cadastrais em `scripts/verificar_criptografia_legada.py`. Porém, sua execução não faz parte da migration. O script `diagnosticar_totp_legado.py` verifica segredos TOTP antigos, mas não os converte.

Remediação: Em banco restaurado, executar os diagnósticos de criptografia legada. Se houver registros pendentes, criar uma migration incremental e idempotente que converta os valores usando a chave Fernet correta, com verificação antes e depois. Não modificar migrations já aplicadas no Supabase. Para TOTP, exigir também validação de leitura dos segredos após a conversão.

### [Severidade: Alto] Falhas HTTP 500 em produção documentadas e sem causa identificada

**Situação conferida: HISTÓRICO CONFIRMADO, REMEDIAÇÃO NÃO HOMOLOGADA.** Os logs do Render ainda registram erro em `/frequencia/` em 18/10/2026, às 20:55 e 20:58 UTC. Não há prova de funcionamento autenticado posterior; portanto não usar a marca de resolvido.

Vetor: Segurança — Disponibilidade

Localização: `Docs/Documentacoes_Tecnicas/Documentacao_Tecnica_v1.0.0.md`, linha 30; rotas correspondentes em `apps/academico/views.py`, linha 221, e `apps/frequencia/views.py`, linha 35.

Risco/Impacto: A documentação técnica do próprio projeto registra que, em 18/10/2026, foram observados erros HTTP 500 nas rotas `/academico/aulas/registrar/` e `/frequencia/`.

Esses erros representam indisponibilidade funcional das rotinas de aulas e frequência. Entretanto, a documentação não apresenta os tracebacks. A inspeção estática, isoladamente, não permite atribuir os erros a uma linha específica das views, a migrations ausentes ou a falhas de conexão.

Remediação: Recuperar os tracebacks correspondentes nos logs do Render, conferir o estado das migrations aplicadas no Supabase e executar `python manage.py check --deploy` e a suíte de regressão no ambiente apropriado. Corrigir a causa evidenciada pelo traceback e verificar as duas rotas autenticadas antes de considerar o release estável.

## Vulnerabilidades e erros de severidade média

### [Severidade: Médio] Encerramento de conta não garante desidentificação dos conteúdos relacionados

**Situação conferida na `main` (`9c3cc66`): PENDENTE DE POLÍTICA E ROTINA.** Desidentificação de cadastro existe, mas não foi implementado expurgo de textos/anexos após retenção.

Vetor: LGPD

Localização: `apps/usuarios/views.py`, linhas 579–640, função `excluir_dados_view`.

Risco/Impacto: A rotina desidentifica campos cadastrais, remove credenciais ativas e preserva históricos escolares. Entretanto, respostas de atividades, PDFs, mensagens e outros textos livres podem continuar contendo dados que identifiquem diretamente o titular.

A documentação LGPD já reconhece expressamente essa limitação em `Docs/Mapa_Dados_LGPD.md`, linhas 53–67.

Isso não torna toda retenção ilegal: históricos escolares podem exigir conservação. O problema é que a desidentificação cadastral não equivale à anonimização completa dos dados relacionados.

Remediação: Formalizar critérios de retenção por categoria, base legal, prazo e responsável institucional. Implementar procedimento controlado para expurgar ou anonimizar conteúdos e arquivos cujo prazo tenha expirado, preservando somente registros com justificativa de conservação. Validar a exclusão também no armazenamento Supabase.

### [Severidade: Médio] Exportação LGPD incompleta para alunos representados e consentimentos

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** Exportação de dados representados e consentimentos correspondentes não foi acrescentada à view.

Vetor: LGPD

Localização: `apps/usuarios/views.py`, linhas 508–576, especialmente 534–564.

Risco/Impacto: `exportar_dados_view` contempla notas, frequência, atividades e históricos quando o titular autenticado possui um registro `Aluno`.

Porém, quando o responsável exporta seus dados, recebe essencialmente os vínculos dos alunos representados, sem uma opção equivalente de exportação dos registros escolares desses alunos mediante representação legitimada.

Além disso, consentimentos concedidos por um responsável em nome de uma criança ficam associados ao usuário responsável. A exportação realizada pela conta da criança não reúne necessariamente esses consentimentos.

Remediação: Acrescentar exportação por aluno representado mediante validação explícita do vínculo e da legitimidade do responsável. Incluir os consentimentos em que o aluno aparece em `aluno_representado`, evitando dados de terceiros sem autorização. Cobrir essas situações em testes próprios de exportação.

### [Severidade: Médio] Rate limiting por IP depende de configuração de proxy não demonstrada

**Situação conferida: VALIDAÇÃO DE AMBIENTE PENDENTE.** A existência de Redis não demonstra que `REMOTE_ADDR` corresponda ao IP real atrás do proxy.

Vetor: Segurança — Disponibilidade

Localização: `apps/usuarios/views.py`, linhas 135–155 e 381–383; `core/settings.py`, linhas 37 e 255–265.

Risco/Impacto: As rotas públicas de login e recuperação utilizam `@ratelimit(key='ip')`. Por padrão, o django-ratelimit utiliza `REMOTE_ADDR`, cuja correspondência com o IP real do usuário depende da configuração do proxy.

Em um ambiente intermediado por reverse proxy, uma configuração inadequada pode agrupar usuários distintos no mesmo limite ou permitir que a identificação do cliente seja manipulada.

O Redis compartilhado já é exigido em produção, o que resolve a persistência dos contadores entre workers, mas não garante que o IP seja identificado corretamente.

Remediação: Verificar nos logs do Render o valor efetivo de `REMOTE_ADDR` para usuários distintos. Configurar a obtenção do IP real exclusivamente a partir de cabeçalhos confiáveis, controlados pelo proxy, sem aceitar livremente `X-Forwarded-For` enviado pelo cliente. Testar limites simultâneos de usuários diferentes.

### [Severidade: Médio] Rotas de escrita acadêmica não possuem limitação de frequência

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** `registrar_aula_view` e `entrega_corrigir_view` ainda não têm limitação específica por requisição POST.

Vetor: Segurança — Disponibilidade

Localização: `apps/academico/views.py`, linhas 220–257, função `registrar_aula_view`; `apps/atividades/views.py`, linhas 249–288, função `entrega_corrigir_view`.

Risco/Impacto: As duas rotas permitem operações repetidas autenticadas sem rate limiting específico. Um docente com conta comprometida ou cliente automatizado poderá produzir numerosas aulas, revisões de entrega e entradas de auditoria em sequência.

O risco é maior na correção de entregas, pois cada requisição válida pode adicionar uma linha em `HistoricoCorrecao` e outra em `LogOperacao`, além da atualização da entrega.

Remediação: Aplicar limites por usuário às requisições POST dessas rotas usando o Redis já configurado, mantendo GET disponível quando necessário. Acrescentar testes de excesso de requisições e verificar se operações bloqueadas não produzem registros no banco.

### [Severidade: Médio] Upload de arquivos não é transacional com o armazenamento S3

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** O arquivo remoto pode ser escrito antes do commit da transação do banco.

Vetor: LGPD / Banco

Localização: `apps/atividades/views.py`, linhas 194–215, função `entrega_salvar_view`.

Risco/Impacto: `entrega.save()` pode gravar o PDF no armazenamento remoto antes do commit da transação do PostgreSQL.

Se a transação falhar depois do upload, o objeto remoto poderá permanecer armazenado sem uma referência válida no banco. O código já trata a remoção do arquivo anterior após o commit, mas não implementa compensação para novos uploads quando a transação é revertida.

Isso pode produzir arquivos órfãos, consumo desnecessário de armazenamento e retenção de documentos pessoais sem rastreabilidade adequada.

Remediação: Implementar estratégia de gravação temporária com confirmação após commit, ou compensação segura para arquivos enviados em transações revertidas. Acrescentar reconciliação periódica entre objetos do bucket e registros de entregas, sem apagar arquivos legítimos antes de validar a política de retenção.

### [Severidade: Médio] Alteração de senha pelo Django Admin não utiliza a auditoria customizada

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** O fluxo específico de alteração de senha pelo `UserAdmin` ainda não registra explicitamente um evento em `LogOperacao`.

Vetor: Auditoria

Localização: `apps/usuarios/admin.py`, linhas 9–42; `core/admin_auditoria.py`, linhas 15–18.

Risco/Impacto: O projeto registra alterações administrativas por meio de `AdminComAuditoria.save_model()`.

Entretanto, a rota especial de alteração de senha herdada do `UserAdmin` utiliza `user_change_password()` e salva a alteração diretamente, sem passar por esse método. Assim, a mudança pode ser registrada no log nativo do Django Admin, mas não necessariamente no `LogOperacao` usado pela auditoria customizada.

Remediação: Tratar explicitamente o fluxo de mudança de senha do `UserAdmin` para registrar o evento no `LogOperacao`, sem copiar hashes ou senhas. Acrescentar teste que altere uma senha pela rota administrativa e confira a existência do evento esperado.

### [Severidade: Médio] Média acadêmica ignora pesos e escalas das avaliações

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** O dashboard ainda utiliza `Avg(valor)` sem pesos e normalização.

Vetor: Estrutura

Localização: `apps/usuarios/views.py`, linha 320, função `dashboard_view`; `apps/avaliacoes/models.py`, linhas 8–14.

Risco/Impacto: O modelo `Avaliacao` define `peso` e `nota_maxima`, mas o dashboard do aluno calcula `media_notas` utilizando diretamente `Avg('valor')`.

Se a instituição utilizar pesos diferentes ou avaliações com notas máximas diferentes, o indicador apresentado poderá não representar corretamente o desempenho acadêmico do estudante.

Remediação: Definir a regra de cálculo exigida pela instituição e implementar a média ponderada considerando `peso` e, quando aplicável, a normalização pela `nota_maxima`. Adicionar testes com avaliações de diferentes pesos e valores máximos para evitar resultados matematicamente incorretos.

### [Severidade: Médio] Cobertura de regressão não contempla mudanças de perfil e limites de atribuição docente

**Situação conferida na `main` (`9c3cc66`): PENDENTE.** Não foi identificado teste específico de revogação de privilégios após troca de `perfil` nem de atribuição por turma.

Vetor: Auditoria

Localização: `apps/usuarios/test_appsec_final.py`, linhas 9–86; `apps/avaliacoes/tests.py`, linhas 32–63; `apps/frequencia/tests.py`, linhas 28–57.

Risco/Impacto: Os testes existentes cobrem cenários importantes, incluindo acesso indevido de alunos, lançamento e histórico de notas, proteção do Admin e correções de frequência.

Porém, não foi identificado nesses arquivos um teste que valide a revogação efetiva das permissões quando um professor muda de perfil, nem um cenário que diferencie atribuições docentes para a mesma disciplina em turmas distintas.

Dessa forma, regressões envolvendo permissões inconsistentes podem não ser detectadas pela suíte atual.

Remediação: Incorporar testes negativos para alteração de perfil, revogação de vínculos docentes, professor não atribuído à turma e tentativa de modificar registros acadêmicos fora de sua atribuição. Também testar o fluxo administrativo de troca de senha e o resultado de exportações por responsáveis.

## Verificações sem problemas confirmados

Nas verificações estáticas executadas, obtive os seguintes resultados:

| Verificação                            | Resultado                            |
| ---------------------------------------- | ------------------------------------ |
| Sintaxe Python e marcadores de conflito  | Sem erros detectados                 |
| Referências de URLs e templates         | Sem referências ausentes detectadas |
| Folhas finais de migrations              | Uma folha por aplicação            |
| Duplicidade `0005` e `0002`          | Resolvida por migrations de merge    |
| SQL Injection nas views                  | Nenhuma ocorrência confirmada       |
| Segredos reais hardcoded                 | Nenhuma ocorrência confirmada       |
| Colisões de `related_name`            | Nenhuma colisão detectada           |
| Proteção do Django Admin por TOTP      | Controle implementado                |
| CSRF nos formulários POST inspecionados | Tokens presentes                     |

Esses resultados não substituem `manage.py check`, `makemigrations --check --dry-run`, execução dos testes ou validação do banco de produção.

## Ordem recomendada de correção

A prioridade técnica é corrigir primeiro a persistência de privilégios após mudança de perfil e a abrangência indevida das atribuições docentes. Em seguida, verificar os dados legados criptografados e diagnosticar os erros HTTP 500 documentados. Depois, concluir as pendências de LGPD, reforçar os limites operacionais e fechar as lacunas de auditoria e testes.

Conclusão: o EduControll apresenta uma base significativa de controles de segurança, incluindo autenticação, TOTP, validação de requisições, RBAC em diversas rotas, criptografia e registros de auditoria. Entretanto, não é possível considerá-lo integralmente aprovado nos cinco vetores solicitados enquanto os achados de severidade alta não forem corrigidos ou descartados mediante evidências de execução.

---

## Complemento de documentação da v1.0.1 (não altera o diagnóstico acima)

Os itens seguintes **já estavam implementados ou publicados**, mas a documentação anterior não refletia o estado efetivo. Por isso, recebem a anotação solicitada; não devem ser confundidos com os 12 achados técnicos ainda abertos.

- Redirecionamento após login/2FA por `next` interno seguro **(resolvido mas esquecido de editar)**: `apps/usuarios/views.py` valida e preserva o destino solicitado. `Docs/Documentacoes_Tecnicas/Documentacao_Tecnica_v1.0.0.md` ainda afirmava que o login terminava sempre no dashboard. Nesta atualização, a descrição documental é corrigida.
- Páginas dos portais e dashboards atualizadas **(resolvido mas esquecido de editar)**: o código da `main` já inclui os portais separados, indicadores consultados no banco e layout modular, mas `Docs/Checklist.md` ainda registrava várias dessas alterações como «Correção preparada». Esse indicador é atualizado sem fingir que a homologação manual em produção ocorreu.
- Release `v1.0.0` já publicado **(resolvido mas esquecido de editar)**: o GitHub registra a publicação do release, enquanto `Docs/Checklist.md` ainda dizia «Ainda não publicado».
- Pôster e resumo simples adicionados ao repositório **(resolvido mas esquecido de editar)**: os PDFs já existiam em `Docs/Resumo e Poster/`, mas os links do README apontavam para `Docs/Poster_e_Resumo/`. As referências são ajustadas nesta versão.

**Atenção:** este rótulo é uma anotação de **documentação desatualizada**, não uma alegação de que os achados de RBAC, migrações, LGPD, disponibilidade, auditoria ou média ponderada tenham sido corrigidos. Os arquivos do projeto devem preservar o histórico da auditoria de 18/10/2026 e separar implementação de testes de homologação.
