
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

## Integração de avaliações e frequência — outubro/2026

| Dado                             | Modelo                  | Finalidade e proteção                                            | Retenção e exportação                                                                 |
| -------------------------------- | ----------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Período letivo                  | `PeriodoLetivo`       | Organizar turmas por período e datas válidas                     | Metadado escolar, sujeito à política acadêmica                                         |
| Avaliação, nome e peso         | `Avaliacao`           | Organização de provas, seminários e pontuações                | Histórico escolar vinculado à disciplina/turma                                          |
| Nota e observação              | `Nota`                | Medir desempenho; `observacao` com Fernet                        | Exportável pelo titular; preservar conforme obrigação acadêmica                       |
| Revisões de nota                | `HistoricoNota`       | Provar autor e valores de correções                              | Somente leitura e preservação por `PROTECT`                                           |
| Presença, falta e justificativa | `RegistroFrequencia`  | Acompanhamento e cálculo da frequência; justificativa com Fernet | Exportável pelo titular ou representante habilitado                                      |
| Revisões de frequência         | `HistoricoFrequencia` | Demonstrar correções, inclusive de justificativas                | Campos pessoais criptografados; acesso RBAC                                               |
| Arquivo de entrega               | `Entrega.arquivo`     | Comprovar entrega de atividade em PDF                              | Bucket privado; rota de download autenticada; prazo de retenção institucional a definir |
| Aviso fixado                     | `Aviso.fixado`        | Priorizar comunicados institucionais                               | Campo booleano sem novo dado pessoal                                                      |

**Migração de observações e justificativas:** as migrations `avaliacoes/0002_criptografia_historico.py` e `frequencia/0002_criptografia_historico.py` adicionam primeiro colunas Fernet temporárias, copiam os dados usando o ORM histórico e só então removem a coluna antiga. Nunca trocar `FIELD_ENCRYPTION_KEY` durante esta operação. Executar primeiro em backup restaurado e conferir os registros lidos pelo ORM.

**Dados legados e tabelas antigas do Supabase:** tabelas terminadas em `_antiga` foram renomeadas pela equipe e não são alteradas por esta remediação. O responsável pelo banco deve confirmar quem as criou, a retenção aplicável e a existência de dados antes de considerar sua exclusão.

**Desidentificação e retenção:** a rotina de encerramento de conta preserva registros acadêmicos necessários, mas a política institucional precisa definir quando arquivos e observações deixam de ter finalidade legítima e podem ser expurgados por um processo próprio, com backup, registro e conferência do armazenamento. Não foi implementada exclusão automática irreversível de arquivos sem essa política.

**Direitos do titular:** `exportar_dados_view` agora inclui avaliações e frequências do aluno, revisões e a referência aos PDFs entregues. O conteúdo físico do PDF é acessível apenas pela rota autenticada e autorizada. O responsável só pode consultar registros dos alunos que lhe estão vinculados.


## Política de retenção e apagamento — pendência de governança

A rotina `excluir_dados_view` encerra acesso, desidentifica cadastro e elimina os tokens, mas NÃO garante anonimização absoluta: textos livres em `Mensagem.assunto`, `Mensagem.texto`, `Entrega.resposta`, anexos PDF e registros de terceiros podem continuar contendo identificadores.

**Matriz de decisão obrigatória (responsável pela instituição):**

| Categoria | Medida técnica existente | Decisão pendente para expurgo |
|---|---|---|
| Cadastro e credenciais | Desidentificação, inutilização da senha e remoção de TOTP | Prazo de conservação de logs de autenticação |
| Mensagens pessoais | Assunto e corpo criptografados, RBAC e trilha de envio | Classificar mensagens administrativas que têm dever de guarda; após o prazo, neutralizar conteúdo, incluindo mensagens recebidas |
| Respostas e PDFs | Conteúdo criptografado e arquivo acessível somente por rota autenticada | Definir prazo de retenção e rotina de exclusão do objeto remoto e referência no banco |
| Notas, histórico e frequência | Trilha de alterações, integridade e controle de acesso | Prazo conforme regra acadêmica antes de apagar ou anonimizar |
| Consentimento e logs | `PROTECT`/somente leitura, rastreabilidade | Base legal e prazo de guarda após desligamento |

**O que NÃO executar automaticamente:** exclusão generalizada de mensagens ou arquivos com finalidade escolar, alteração da chave Fernet ou apagamento físico de usuários. O controlador de dados deve aprovar a classificação e os prazos; então o procedimento deve ser testado num backup restaurado, com registro e controle de acesso. A documentação não equivale a uma política institucional já aprovada.
