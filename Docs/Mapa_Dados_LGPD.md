
# Mapa de dados e finalidades - EduControll

| Dados                                         | Modelo                                    | Finalidade e acesso                                 | Proteção / retenção                                                        |
| --------------------------------------------- | ----------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------ |
| Nome, e-mail, senha com hash                  | `usuarios.Usuario`                      | Identificação e autenticação                    | Acesso RBAC, hash de senha; desidentificação ao encerrar conta               |
| Telefone, endereço, nascimento               | `Aluno`, `Professor`, `Responsavel` | Contato e cadastro escolar                          | Campos Fernet; não buscar valores criptografados por substring                |
| Segredo TOTP                                  | `Usuario.otp_secret`                    | Autenticação em dois fatores                      | Campo criptografado; não exportar chave secreta                               |
| Matrícula, turma, aula                       | `Matricula`, `Aula`                   | Histórico acadêmico                               | Consulta por perfil/vínculo; preservação justificada                        |
| Títulos, descrições e respostas            | `Atividade`, `Entrega`                | Tarefas escolares e correção                      | Respostas e comentários criptografados; autor/turma e aluno autorizados       |
| Avisos e mensagens                            | `Aviso`, `Mensagem`                   | Comunicação institucional                         | Corpo criptografado; conteúdo visível apenas por RBAC, matrícula e vínculo |
| Consentimento e autorização de responsável | `ConsentimentoUsuario`                  | Preferências de imagem/WhatsApp e comprovação    | Histórico versionado com titular representado, quando aplicável              |
| IP, horário e evento                         | `LogAcesso`, `LogRecuperacaoSenha`    | Segurança, detecção de abuso e auditoria         | Acesso administrativo somente leitura; prazo de retenção a definir           |
| Operação e identificador do objeto          | `LogOperacao`                           | Rastrear alterações acadêmicas e comunicacionais | Nenhum corpo de mensagem ou resposta copiado ao log                            |

**Regras de tratamento:** necessidade, finalidade, transparência e retenção devem ser justificadas pela escola; não presumir que todo dado depende de consentimento. Exportações devem ser autenticadas; documentos produzidos pelo aluno/professor e mensagens podem exigir análise de terceiros antes de compartilhamento. Para crianças, verificar representação legal conforme o art. 14 da LGPD. Configurar prazos reais de retenção antes de produção.

## Campos e correções adicionais (outubro/2026)

| Dado                                                                 | Modelo                                                  | Finalidade                                | Proteção                                                                            |
| -------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------- |
| Identificação da entrega fora do prazo                             | `Entrega.atrasada`                                    | Verificar cumprimento do prazo (RN-08)    | Visibilidade limitada à turma e responsáveis vinculados                             |
| Notas anteriores, notas novas, comentários e professor responsável | `HistoricoCorrecao`                                   | Preservar revisões acadêmicas (RN-11)   | `PROTECT` nos vínculos, comentários criptografados e transação com auditoria    |
| Consentimentos históricos                                           | `ConsentimentoUsuario`                                | Comprovar aceites e revogações          | Exclusão física bloqueada por `PROTECT`; desidentificação permanece disponível |
| Eventos de acesso, operações e recuperações                      | `LogAcesso`, `LogOperacao`, `LogRecuperacaoSenha` | Segurança e investigação de incidentes | Somente leitura no admin e inclusão na exportação do titular (sem tokens)          |

**Migration 0010:** o script `scripts/verificar_criptografia_legada.py` apenas conta os valores que ainda não estão criptografados; não revela conteúdo. Não execute `--corrigir` antes de confirmar backup, restaurar uma cópia para testes e usar a mesma `FIELD_ENCRYPTION_KEY` do banco original. Um valor com chave incompatível interrompe a correção.

**Retenção:** manter a guarda de registros acadêmicos e consentimentos somente pelo prazo institucional/obrigação legal aplicável. Um usuário desidentificado mantém históricos necessários, mas não deve manter telefone, endereço ou tokens ativos. O prazo efetivo de retenção ainda precisa ser acordado com a instituição.
