
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


## Situação integrada — revisão para v1.0.0 (18/10/2026)

Legenda: **Implementado** = código presente; **Testado local** = evidência de suíte anterior; **Homologação pendente** = exige confirmação na versão de produção.

| Requisito | Implementação | Situação em produção |
|---|---|---|
| Portais separados com senha e 2FA | Implementado | Confirmar autenticação em todos os perfis |
| Landing page sem formulário redundante | Correção preparada | Validar após deploy |
| Dashboard aluno com notas/frequência reais | Correção preparada | Validar matrícula e vínculos no Supabase |
| Dashboard responsável sem mural/chat fictícios | Correção preparada | Validar avisos/mensagens reais vinculados |
| Turmas, disciplinas, matrícula, períodos | Implementado | Fluxos vistos em capturas; testar operações |
| Registro de aula | Implementado | **Erro HTTP 500 visto em produção; bloqueante** |
| Atividades e correção de entregas | Implementado | Tela abre; fluxos completos ainda não homologados |
| Comunicação por avisos e mensagens | Implementado | Tela abre; testar publicação e envio em conta de teste |
| Avaliações e notas | Implementado | Validar consulta e gravação com usuário autorizado |
| Frequência e histórico | Implementado | **Erro HTTP 500 visto em produção; bloqueante** |
| Criptografia LGPD, autorização, logs e rate limiting | Implementado | Confirmar verificações e integrações em produção |
| Layout unificado com CSS por módulo | Correção preparada | Validar responsividade e contraste após deploy |
| 113 testes (antes da correção de interface) | Testado localmente | Reexecutar suíte ampliada; não confundir com prova de homologação |
| Release GitHub v1.0.0 | Preparação concluída no pacote | **Ainda não publicado** |

A documentação e as capturas de setembro são evidências históricas, **não** comprovam automaticamente a versão de outubro. Somente assinalar a release como entregue após executar `check`, `makemigrations --check`, testes, `migrate --plan` e roteiro manual por papel no Render.
