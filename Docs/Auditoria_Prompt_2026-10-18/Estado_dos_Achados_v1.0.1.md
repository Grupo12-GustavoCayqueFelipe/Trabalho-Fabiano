# Estado dos achados AppSec — acompanhamento da v1.0.1

**Fonte:** resposta de auditoria fornecida pelo grupo em 18/10/2026.
**Conferência complementar:** `main` no commit `9c3cc66c1bdb706b24970f3baa2455a8c9dabbeb`; comparação com `d87fcf26` (somente PDFs e README foram modificados entre as duas revisões).
**Escopo:** análise estática e histórico disponível, sem simular alterações destrutivas no Supabase.

| Severidade | Achado resumido                                                    | Estado verificável                                                                                 |
| ---------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Alto       | Perfil alterado mantém privilégios docentes                      | Pendente                                                                                            |
| Alto       | Atribuição professor/disciplina não diferencia turma            | Pendente                                                                                            |
| Alto       | Conversão de dados anteriores às migrations Fernet               | Diagnóstico dos dados legados feito no banco de dados; homologação após verificação pendente |
| Alto       | HTTP 500 em aulas e frequência                                    | Registro histórico; homologação após correções pendente                                       |
| Médio     | Encerramento da conta preserva dados identificáveis em conteúdos | Pendente de política de retenção e implementação                                               |
| Médio     | Exportação de aluno representado e consentimentos                | Pendente                                                                                            |
| Médio     | Identificação do IP real atrás do proxy                         | Verificação da configuração do Render pendente                                                  |
| Médio     | Limites de escrita para aulas e correções                        | Pendente                                                                                            |
| Médio     | Upload S3 sem compensação em caso de rollback                    | Pendente                                                                                            |
| Médio     | Troca de senha pelo Admin sem LogOperacao customizado              | Pendente                                                                                            |
| Médio     | Cálculo de média ignora peso/nota máxima                        | Pendente                                                                                            |
| Médio     | Testes de regressão de RBAC por perfil/turma                      | Pendente                                                                                            |

## Itens previamente implementados e sem atualização documental

- Redirecionamento `next` seguro no login e 2FA **(resolvido mas esquecido de editar)**.
- Portais separados, dashboards reais e CSS modular em produção de código **(resolvido mas esquecido de editar)**; a homologação completa permanece pendente.
- Release `v1.0.0` já publicado no GitHub **(resolvido mas esquecido de editar)**.
- Pôster e resumo presentes na pasta `Docs/Resumo e Poster/`; links do README desatualizados **(resolvido mas esquecido de editar)**.

**Critério:** não usar a etiqueta acima para nenhum dos 12 achados técnicos sem evidência adicional de correção e testes. Especialmente, os erros 500 têm registros históricos nos logs e precisam de reteste autenticado.
