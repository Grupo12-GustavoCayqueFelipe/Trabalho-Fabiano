# Documentação Técnica — EduControll v1.0.0

Este sumário acompanha a documentação histórica [Autenticação e Gestão de Credenciais](../Documentacoes_Tecnicas/) e a complementa com o escopo implementado em 18/10/2026.

## Arquitetura e implantação

Django 6.0 e Python 3.14, banco PostgreSQL (Supabase), views e templates Django, deploy Render, HTTPS, WhiteNoise para estáticos, Redis para rate limit em múltiplos workers e SMTP para recuperação de senha. Os segredos (`DATABASE_URL`, `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, SMTP, Redis, Storage S3) são variáveis de ambiente, jamais artefatos versionados.

## Organização funcional

| App | Responsabilidade |
|---|---|
| `usuarios` | Login segregado por portal, TOTP, senha, LGPD, consentimentos e auditoria |
| `academico` | Período letivo, turmas, disciplinas, matrícula, aula |
| `atividades` | Publicação e entregas com controle docente e correção |
| `avaliacoes` | Avaliações, notas e histórico |
| `frequencia` | Registros e histórico de frequência |
| `comunicacao` | Avisos e mensagens internas |

## Fluxo

`/` → seleção de portais → formulário específico (`/login/` ou `/funcionarios/login/`) → autenticação por senha → TOTP quando ativado → dashboard vinculado ao perfil. Consultas e operações são novamente autorizadas no backend. A compatibilidade de POST legado na raiz requer revisão futura.

## Segurança e privacidade

Criptografia de campos sensíveis em repouso, PBKDF2 (padrão Django), sessão protegida, CSRF, limitação de tentativas, controle de acesso por perfil e vínculo, trilhas de autenticação e operações, exportação e tratamento de dados. As métricas mostradas nos dashboards de aluno e responsável são obtidas por consultas autorizadas; não representam dados fictícios.

## Qualidade, ambiente e ressalvas

Antes desta correção de interface: 113 testes locais aprovados em SQLite. As alterações finais precisam passar novamente por suíte, checks e verificação do Render. Em 18/10/2026, capturas de produção registravam **HTTP 500 em `/academico/aulas/registrar/` e `/frequencia/`**; as causas não podem ser estabelecidas sem traceback dos logs. O release v1.0.0 só deve ser marcado como estável após essa confirmação.

Referências complementares: [`Docs/Checklist.md`](../Checklist.md), [`Docs/Mapa_Dados_LGPD.md`](../Mapa_Dados_LGPD.md) e documentação original de credenciais na mesma pasta.
