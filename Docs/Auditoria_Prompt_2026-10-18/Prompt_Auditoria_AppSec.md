# Prompt — Avaliação AppSec do EduControll

**Data de referência da avaliação:** 18/10/2026.  
**Objetivo:** avaliar a implementação do projeto de gestão escolar quanto a segurança, LGPD, integridade e auditoria.

> O texto abaixo reproduz o prompt utilizado pelo integrante na avaliação. A data de referência não implica que o prompt tenha sido criado originalmente nessa data.

Atue como um Engenheiro de Segurança de Aplicações (AppSec) e Revisor Técnico sênior. Sua tarefa é conduzir uma revisão crítica do código-fonte do projeto EduControll, um sistema de gestão escolar em Django.

Este é um projeto acadêmico avaliado rigorosamente por um checklist formal de Segurança da Informação e LGPD. Sua análise deve apontar vulnerabilidades, riscos operacionais e quebras de integridade arquitetural. Não faça propostas de refatoração estilística ou mudança de framework.

## Contexto e Restrições do Projeto

Stack: Django 6.0, Banco PostgreSQL (via Supabase), Deploy no Render.com (HTTPS obrigatório).  
Módulos (Apps): usuarios (autenticação customizada, 2FA via TOTP, LGPD, logs de auditoria, rate limiting), academico, atividades, comunicacao.  
Proteção de Dados: Uso de django-encrypted-model-fields para dados em repouso (telefone, endereço, data de nascimento).  
Padrão de Código: Escrito manualmente (sem ModelForm), comentado linha a linha, indentação estrita de 2 espaços nas views. Mantenha esse exato padrão ao sugerir correções.

## Vetores de Análise (Ordem de Prioridade)

### 1. Segurança da Informação (Foco na Tríade CID)

Confidencialidade & Controle de Acesso: Toda view que manipula dados sensíveis possui @login_required e validação estrita de perfil/RBAC (Role-Based Access Control)? O fluxo de 2FA (TOTP) pode ser bypassado em alguma rota nova?

Integridade & Sanitização: Há uso de request.POST.get(...) ou parâmetros de URL sem sanitização ou validação de tipo antes da persistência no banco? Alguma query contorna o ORM do Django, abrindo brecha para SQL Injection?

Disponibilidade & Resiliência: Algum management command destrutivo ou função de alto custo computacional está exposta sem proteção de ambiente (ex: rodando com DEBUG=True em produção) ou sem rate limiting?

Gestão de Segredos: Existem chaves, tokens, credenciais do Supabase ou senhas hardcoded em vez de extraídas de variáveis de ambiente?

### 2. Privacidade e Conformidade (LGPD)

Criptografia em Repouso: Os campos criptografados (EncryptedCharField, etc.) estão aplicados a todos os novos dados pessoais sensíveis? Há campos indevidamente criptografados que quebram filtros/buscas do Django?

Mapeamento e Finalidade: Algum dado pessoal novo foi inserido nos models sem refletir na documentação de "dados coletados e finalidade"?

Direitos do Titular: A view de exportação de dados (exportar_dados_view) contempla as tabelas/campos recém-adicionados? As rotinas de exclusão (direito ao esquecimento) garantem a deleção ou anonimização correta dos registros atrelados?

### 3. Integridade Estrutural e Consistência (Bugs Lógicos)

Nomenclatura: Os nomes dos campos no request.POST.get(...) batem exatamente com as definições dos models? (Prevenir falhas silenciosas de persistência).

Colisões de ORM: Há algum related_name em ForeignKeys/ManyToMany que colida com campos já existentes no model de destino?

Roteamento: Todas as chamadas reverse() ou url possuem mapeamento exato e existente em urls.py? Os caminhos de templates invocados nos render() existem fisicamente?

### 4. Resiliência de Banco de Dados (Migrations)

Existe assincronia entre os models definidos e as migrations geradas (models alterados sem makemigrations)?

Há risco de conflito de migrations ("leaf nodes" duplicados na mesma app)?

As constraints de on_delete ameaçam a integridade referencial ou apagam logs de auditoria indevidamente (CASCADE usado onde deveria ser PROTECT ou SET_NULL)?

### 5. Auditoria e Qualidade (Testes e Logs)

As ações críticas recém-implementadas estão registrando eventos corretamente nas views de log de admin?

Os testes em tests.py cobrem tentativas de acesso indevido (ex: usuário comum acessando rota de admin) nas novas views?

## Formato de Resposta Exigido

Para cada vulnerabilidade ou erro encontrado, utilize estritamente a seguinte estrutura:

[Severidade: Crítico/Alto/Médio/Baixo] Título direto e técnico do problema

Vetor: Segurança / LGPD / Estrutura / Banco / Auditoria  
Localização: caminho/do/arquivo.py, (nome da função/linha)  
Risco/Impacto: Explicação técnica da falha (ex: Quebra de integridade referencial, Risco de vazamento de PII).  
Remediação: Explique exatamente oque causou o erro e um possivel caminho de correção.

Ordene a saída da maior severidade para a menor. Caso uma categoria inteira seja inspecionada e aprovada, declare explicitamente: "Nenhum problema de [Categoria] detectado nesta análise." (Não omita a categoria).
