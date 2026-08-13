# Escopo do Projeto

**EduControll  Sistema web de gestão acadêmica**

| Campo | Descrição |
|---|---|
| Projeto | EduControll |
| Arquitetura | MTV (Model–Template–View) |
| Repositório | Trabalho-Fabiano |
| Licença | MIT |
| Versão do documento | 1.0 |

---

## 1. Objetivo

Desenvolver um sistema web que permita a escolas e cursos acompanhar frequência, desempenho, atividades e comunicação com alunos e responsáveis, com acesso controlado por perfil.

## 2. Perfis de usuário

| Perfil | O que faz no sistema |
|---|---|
| Administrador | Cadastra turmas, disciplinas e usuários; configura parâmetros |
| Professor | Registra frequência e notas, cria atividades, corrige entregas |
| Aluno | Consulta frequência e boletim, envia entregas, lê avisos |
| Responsável | Acompanha o aluno vinculado e recebe avisos |

## 3. O que o sistema faz

| Módulo | Entrega |
|---|---|
| Acesso | Login, logout e restrição de funcionalidades por perfil |
| Cadastros | Turmas, disciplinas, alunos, professores, responsáveis e matrículas |
| Frequência | Registro de presença por aula e cálculo automático do percentual |
| Desempenho | Lançamento de notas, cálculo de médias e boletim digital |
| Atividades | Criação de atividades, envio de entregas e correção |
| Comunicação | Mural de avisos e mensagens para alunos e responsáveis |

## 4. O que fica fora

- Módulo financeiro (mensalidades e cobranças)
- Aplicativo móvel nativo (o acesso é por navegador)
- Aulas ao vivo ou videoconferência
- Documentos com valor legal (histórico escolar oficial)
- Geração automática de horários
- Integração com sistemas oficiais de secretarias de educação

## 5. Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14.6 |
| Framework | Django 6.0.x |
| Banco de dados | PostgreSQL 18.4 / Supabase PostgreSQL 18 |
| Frontend | HTML5, CSS moderno, JavaScript ES2025+ |
| Versionamento | Git / GitHub |

## 6. Premissas e restrições

**Premissas**

- Usuários com acesso à internet e navegador atualizado
- Dados iniciais (turmas, alunos e responsáveis) fornecidos pela instituição
- Banco PostgreSQL disponível, local ou em nuvem

**Restrições**

- Backend obrigatoriamente em Django, seguindo o padrão MTV
- Banco relacional PostgreSQL
- Frontend sem framework SPA (React, Vue, Angular)
- Uso apenas de ferramentas gratuitas ou de licença aberta

## 7. Etapas de entrega

| # | Etapa | Resultado |
|:---:|---|---|
| 1 | Planejamento | Escopo, requisitos e modelo de dados definidos |
| 2 | Base do sistema | Projeto Django configurado, banco conectado, login por perfil |
| 3 | Cadastros | Turmas, disciplinas, matrículas e vínculos funcionando |
| 4 | Frequência e notas | Registro de presença, notas e boletim operacionais |
| 5 | Atividades e avisos | Entregas, correções e mural funcionando |
| 6 | Fechamento | Testes, ajustes e documentação final |

## 8. Critérios de aceitação

O projeto é considerado concluído quando:

1. Os quatro perfis funcionam com suas restrições de acesso.
2. O professor registra a frequência e o sistema calcula o percentual sozinho.
3. O professor lança notas e o sistema gera o boletim com médias e situação.
4. O aluno envia uma entrega e recebe a correção.
5. O responsável consulta a frequência e o boletim do aluno vinculado.
6. O sistema roda em `http://127.0.0.1:8000` seguindo o README.

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Módulos de atividades e comunicação consumirem mais tempo que o previsto | Entregar primeiro os requisitos obrigatórios |
| Dificuldade na configuração do banco | Documentar a conexão e versionar o `.env.example` |
| Regras de avaliação variarem entre instituições | Deixar média e frequência mínima parametrizáveis |
| Conhecimento concentrado em um integrante | Revisão cruzada e rodízio de módulos |

---


