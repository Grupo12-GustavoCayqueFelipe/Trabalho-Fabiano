
# Checklist  EduControll

Marcar um X na coluna certa.

## 1. Autenticação e Gestão de Credenciais

| O que fazer                                             | Feito | Parcial | Não feito |
| ------------------------------------------------------- | :---: | :-----: | :--------: |
| Login funcionando (email + senha)                       |   X   |        |            |
| Logout funcionando                                      |   X   |        |            |
| Bloquear acesso sem login                               |   X   |        |            |
| Dashboard certo pra cada perfil (admin/prof/aluno/resp) |   X   |        |            |
| Senha salva com hash                                    |   X   |        |            |
| Salt único por usuário                                |   X   |        |            |
| CSRF nos formulários                                   |   X   |        |            |
| Secret key fora do código                              |   X   |        |            |
| 2FA implementado                                        |   X   |        |            |
| Validação do 2FA depois do login primário            |   X   |        |            |
| Sessão com expiração                                 |   X   |        |            |
| Logout invalida sessão                                 |   X   |        |            |
| Rate limit / bloqueio contra força bruta               |   X   |        |            |
| Justificativas técnicas documentadas                   |   X   |        |            |

## 2. Recuperação de Senha

| O que fazer                       | Feito | Parcial | Não feito |
| --------------------------------- | :---: | :-----: | :--------: |
| Recuperação de senha por email  |   X   |        |            |
| Token criptograficamente seguro   |   X   |        |            |
| Token com expiração             |   X   |        |            |
| Token invalidado após uso        |   X   |        |            |
| Falha tratada para token expirado |   X   |        |            |
| Log de solicitação              |   X   |        |            |
| Log de sucesso/falha              |   X   |        |            |

## 3. Criptografia e Comunicação Segura

| O que fazer                                | Feito | Parcial | Não feito |
| ------------------------------------------ | :---: | :-----: | :--------: |
| HTTPS ativo em produção                  |   X   |        |            |
| Bloqueio de conexão não segura           |   X   |        |            |
| Dados sensíveis criptografados em repouso |   X   |        |            |
| Algoritmo adequado (AES via Fernet)        |   X   |        |            |
| Chaves protegidas fora do código          |   X   |        |            |
| Estratégia de criptografia documentada    |   X   |        |            |

## 4. Conformidade com a LGPD

| O que fazer                                 | Feito | Parcial | Não feito |
| ------------------------------------------- | :---: | :-----: | :--------: |
| Dados coletados listados com finalidade     |   X   |        |            |
| Minimização de dados evidenciada          |   X   |        |            |
| Consentimento registrado e revogável       |   X   |        |            |
| Data e versão do consentimento registradas |   X   |        |            |
| Consulta aos dados pelo titular             |   X   |        |            |
| Exportação dos dados                      |   X   |        |            |
| Exclusão dos dados                         |   X   |        |            |

## 5. Auditoria e Logs

| O que fazer                                     | Feito | Parcial | Não feito |
| ----------------------------------------------- | :---: | :-----: | :--------: |
| Código dos logs de autenticação implementado |   X   |        |            |
| Código dos logs de 2FA implementado            |   X   |        |            |
| Logs protegidos contra alteração (admin)      |   X   |        |            |
| Migration aplicada e testada                    |   X   |        |            |
| Evidência real de funcionamento                |   X   |        |            |

## 6. Documentação Técnico-Científica

| O que fazer                                   | Feito | Parcial | Não feito |
| --------------------------------------------- | :---: | :-----: | :--------: |
| Visão geral do sistema                       |   X   |        |            |
| Diagrama de arquitetura                       |   X   |        |            |
| Fluxos de autenticação e dados documentados |   X   |        |            |
| Gestão de credenciais documentada            |   X   |        |            |
| Uso de criptografia documentado               |   X   |        |            |
| Ativos do sistema identificados               |   X   |        |            |
| Ameaças e vulnerabilidades identificadas     |   X   |        |            |
| Risco associado à contramedida               |   X   |        |            |
| Testes de segurança documentados             |   X   |        |            |
| Referências normalizadas                     |   X   |        |            |

## Módulo Acadêmico (fora do checklist oficial, adiantamento do grupo)

| O que fazer                                  | Feito | Parcial | Não feito |
| -------------------------------------------- | :---: | :-----: | :--------: |
| Models (Turma, Disciplina, Matrícula, Aula) |   X   |        |            |
| Views de cadastro/listagem/matrícula/aula   |   X   |        |            |
| Migration da Aula aplicada                   |      |        |     X     |
| Testado no front-end                         |      |        |     X     |

*Não implantado ainda  bloqueado pela mesma instabilidade do Supabase. Views e models já escritos, só falta rodar migration e testar assim que o banco voltar.*

## Geral

| O que fazer                             | Feito | Parcial | Não feito |
| --------------------------------------- | :---: | :-----: | :--------: |
| Documentação técnica no repositório |   X   |        |            |
| Prints/evidência de funcionamento      |   X   |        |            |
| Kanban                                  |   X   |        |            |
| Release no GitHub                       |   X   |        |            |
| Checklist publicado no repositório     |   X   |        |            |

---

Revisado por: Felipe Matta
Data: 27/09/2026
