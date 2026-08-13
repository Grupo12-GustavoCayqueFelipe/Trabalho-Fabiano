# Anexo de Requisitos

**EduControll — Sistema web de gestão acadêmica**

Versão 1.0 — documento base: [Escopo do Projeto](./escopo-do-projeto.md)

---

## 1. Como ler este documento

| Símbolo | Prioridade | Significado |
|:---:|---|---|
| ●●● | Obrigatório | Sem ele o sistema não cumpre seu propósito |
| ●● | Importante | Agrega valor relevante; implementar se o prazo permitir |
| ● | Desejável | Melhoria de conveniência; candidato a versões futuras |

| Prefixo | Significado |
|---|---|
| RF | Requisito Funcional |
| RNF | Requisito Não Funcional |
| RN | Regra de Negócio |

## 2. Permissões por perfil

Símbolo ● = permitido; – = não permitido.

| Funcionalidade | Admin | Professor | Aluno | Responsável |
|---|:---:|:---:|:---:|:---:|
| Gerenciar cadastros | ● | – | – | – |
| Registrar frequência | ● | ● | – | – |
| Consultar frequência | ● | ● | Própria | Do vinculado |
| Lançar notas | ● | ● | – | – |
| Consultar boletim | ● | ● | Próprio | Do vinculado |
| Criar atividades | ● | ● | – | – |
| Enviar entrega | – | – | ● | – |
| Corrigir entrega | ● | ● | – | – |
| Publicar aviso | ● | ● | – | – |
| Ler avisos e mensagens | ● | ● | ● | ● |

## 3. Requisitos funcionais

### 3.1 Acesso

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-01 | Autenticar o usuário por e-mail e senha | ●●● |
| RF-02 | Associar cada usuário a um perfil: admin, professor, aluno ou responsável | ●●● |
| RF-03 | Liberar as funcionalidades conforme a tabela de permissões | ●●● |
| RF-04 | Permitir logout | ●●● |
| RF-05 | Exibir uma página inicial específica para cada perfil | ●●● |
| RF-06 | Permitir troca de senha pelo próprio usuário | ●● |
| RF-07 | Recuperar senha por e-mail | ● |

### 3.2 Cadastros

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-08 | Cadastrar e editar turmas | ●●● |
| RF-09 | Cadastrar e editar disciplinas | ●●● |
| RF-10 | Cadastrar alunos e matriculá-los em turmas | ●●● |
| RF-11 | Cadastrar professores e vinculá-los a disciplinas | ●●● |
| RF-12 | Cadastrar responsáveis e vinculá-los a alunos | ●●● |
| RF-13 | Cadastrar períodos letivos com data de início e fim | ●●● |
| RF-14 | Registrar aulas com data e conteúdo | ●●● |
| RF-15 | Configurar média mínima e frequência mínima | ●● |

### 3.3 Frequência

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-16 | Registrar presença ou falta dos alunos em cada aula | ●●● |
| RF-17 | Calcular automaticamente o percentual de presença por disciplina | ●●● |
| RF-18 | Permitir consulta ao histórico de frequência pelo aluno e responsável | ●●● |
| RF-19 | Permitir correção de um registro já lançado | ●● |
| RF-20 | Registrar falta justificada com observação | ●● |
| RF-21 | Destacar alunos abaixo da frequência mínima | ●● |
| RF-22 | Notificar o responsável ao atingir o limite de faltas | ● |

### 3.4 Notas e boletim

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-23 | Cadastrar avaliações com nome, peso e nota máxima | ●●● |
| RF-24 | Lançar as notas dos alunos em cada avaliação | ●●● |
| RF-25 | Calcular a média por disciplina | ●●● |
| RF-26 | Definir a situação do aluno: aprovado, em recuperação ou reprovado | ●●● |
| RF-27 | Gerar o boletim com notas, médias, frequência e situação | ●●● |
| RF-28 | Permitir consulta ao boletim pelo aluno e responsável | ●●● |
| RF-29 | Exportar o boletim em PDF | ● |
| RF-30 | Exibir resumo de desempenho da turma ao professor | ● |

### 3.5 Atividades

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-31 | Criar atividade com título, enunciado, turma e prazo | ●●● |
| RF-32 | Listar ao aluno as atividades das suas disciplinas, com prazo e situação | ●●● |
| RF-33 | Permitir o envio da entrega com texto e/ou arquivo | ●●● |
| RF-34 | Registrar data da entrega e sinalizar atrasos | ●●● |
| RF-35 | Permitir a correção com nota e comentário | ●●● |
| RF-36 | Exibir ao aluno a nota e o comentário da correção | ●●● |
| RF-37 | Anexar arquivos à atividade | ●● |
| RF-38 | Listar ao professor quem ainda não entregou | ●● |
| RF-39 | Vincular a nota da atividade a uma avaliação | ● |

### 3.6 Comunicação

| ID | Requisito | Prior. |
|---|---|:---:|
| RF-40 | Publicar avisos no mural, por turma ou para toda a escola | ●●● |
| RF-41 | Exibir no aviso título, conteúdo, autor e data | ●●● |
| RF-42 | Mostrar a cada usuário apenas os avisos destinados a ele | ●●● |
| RF-43 | Permitir mensagens diretas entre professor e aluno/responsável | ●● |
| RF-44 | Indicar avisos e mensagens não lidos | ●● |
| RF-45 | Enviar cópia dos avisos por e-mail | ● |

## 4. Requisitos não funcionais

| ID | Requisito | Prior. |
|---|---|:---:|
| RNF-01 | Interface responsiva para computador, tablet e celular | ●●● |
| RNF-02 | Mensagens de erro e confirmação claras em cada operação | ●●● |
| RNF-03 | Interface em português do Brasil | ●●● |
| RNF-04 | Senhas armazenadas com hash (padrão do Django) | ●●● |
| RNF-05 | Chaves e credenciais em variáveis de ambiente, fora do código versionado | ●●● |
| RNF-06 | Toda rota que manipula dados exige login e verifica o perfil | ●●● |
| RNF-07 | Formulários com proteção CSRF | ●●● |
| RNF-08 | `DEBUG` desabilitado em produção | ●●● |
| RNF-09 | Código organizado em apps do Django, seguindo o padrão MTV | ●●● |
| RNF-10 | Dependências fixadas em `requirements.txt` | ●●● |
| RNF-11 | Funcionar em Python 3.14.6 com Django 6.0.x | ●●● |
| RNF-12 | Funcionar com PostgreSQL local ou Supabase sem alterar o código | ●●● |
| RNF-13 | Funcionar em Chrome, Firefox e Edge atualizados | ●●● |
| RNF-14 | Instalação seguindo apenas os passos do README | ●●● |
| RNF-15 | Páginas de consulta respondendo em até 3 segundos | ●● |
| RNF-16 | Paginação em listagens longas | ●● |
| RNF-17 | Validação de tipo e tamanho dos arquivos enviados | ●● |
| RNF-18 | Log das alterações de nota, frequência e permissões | ●● |
| RNF-19 | Backup periódico do banco de dados | ●● |
| RNF-20 | Arquivo `.env.example` documentando as variáveis necessárias | ●● |
| RNF-21 | Acesso a dados pessoais limitado ao mínimo por perfil (LGPD) | ●● |
| RNF-22 | Contraste adequado, rótulos em formulários e navegação por teclado | ●● |
| RNF-23 | Ambiente reproduzível em Windows e Linux/macOS | ●● |

## 5. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | Presença (%) = aulas presentes ÷ total de aulas da disciplina × 100 |
| RN-02 | Frequência mínima para aprovação: 75%, salvo configuração diferente |
| RN-03 | Falta justificada conta como ausência, mas é identificada separadamente |
| RN-04 | A média da disciplina é ponderada pelos pesos das avaliações; sem pesos, usa-se média simples |
| RN-05 | O aluno é aprovado ao atingir, ao mesmo tempo, a média e a frequência mínimas |
| RN-06 | Notas devem ficar entre zero e a nota máxima da avaliação |
| RN-07 | O aluno só envia entregas das disciplinas em que está matriculado |
| RN-08 | Entregas fora do prazo são aceitas, mas marcadas como atrasadas |
| RN-09 | O responsável só acessa dados dos alunos aos quais está vinculado |
| RN-10 | O professor só lança frequência e notas das turmas em que atua |
| RN-11 | Registros de nota e frequência não são apagados; alterações preservam o histórico |
| RN-12 | Turmas, disciplinas e usuários com histórico são inativados, nunca excluídos |

## 6. Entidades do sistema

| Entidade | Descrição |
|---|---|
| Usuario | Dados de acesso e perfil |
| PeriodoLetivo | Ano ou semestre, com data de início e fim |
| Turma | Agrupamento de alunos em um período letivo |
| Disciplina | Matéria ministrada em uma turma |
| Matricula | Vínculo entre aluno e turma |
| ResponsavelAluno | Vínculo entre responsável e aluno |
| Aula | Encontro de uma disciplina, com data e conteúdo |
| RegistroFrequencia | Presença ou falta de um aluno em uma aula |
| Avaliacao | Instrumento avaliativo, com peso e nota máxima |
| Nota | Pontuação do aluno em uma avaliação |
| Atividade | Tarefa proposta, com prazo |
| Entrega | Submissão do aluno para uma atividade |
| Aviso | Comunicado publicado no mural |
| Mensagem | Comunicação direta entre usuários |
