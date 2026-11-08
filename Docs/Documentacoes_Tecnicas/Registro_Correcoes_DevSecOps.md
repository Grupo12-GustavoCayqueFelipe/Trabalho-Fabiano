# Registro de Correções e Justificativas - DevSecOps

## 1. Atualização das dependências

Durante a execução da análise SCA com Trivy, foram identificadas 28 vulnerabilidades de severidade HIGH e CRITICAL na dependência Pillow, fixada anteriormente na versão 12.3.0.

Após consultar a disponibilidade das correções, foi definida a atualização para a versão 13.0.0, que contém as correções relacionadas às vulnerabilidades identificadas.

**Alteração realizada:** atualização de `pillow==12.3.0` para `pillow==13.0.0` no arquivo `requirements.txt`.

**Justificativa:** corrigir vulnerabilidades conhecidas, reduzir os riscos relacionados ao processamento de imagens e manter as dependências do projeto atualizadas e com versões fixadas.

**Requisitos relacionados:** RNF-10: Dependências fixadas no `requirements.txt`.

**Validação:** instalação das dependências, verificação de compatibilidade, testes automatizados, construção da imagem Docker e nova execução do Trivy.

## 2. Tratamento de resultados históricos no TruffleHog

Durante a implementação da análise de segredos, o TruffleHog identificou resultados PostgreSQL em commits antigos do repositório.

A investigação identificou uma exposição histórica do arquivo `.env`, que havia sido enviado ao repositório público por um integrante da equipe. Após a identificação do incidente, as credenciais envolvidas foram substituídas.

A execução histórica do TruffleHog apresentou zero resultados verificados e quatro resultados não verificados. Esses resultados não comprovam que as credenciais antigas continuam válidas, mas demonstram que existiram valores potencialmente sensíveis no histórico do projeto.

**Correção realizada:** ajuste do workflow para que as execuções automáticas de push e pull request verifiquem os commits relacionados a cada evento, em vez de repetir a análise integral do histórico da branch.

**Justificativa:** manter a detecção de novos vazamentos sem bloquear continuamente as alterações por causa de credenciais antigas que já foram substituídas.

**Medida de segurança complementar:** manter as credenciais reais em variáveis de ambiente e impedir o versionamento de arquivos `.env`.

**Requisitos relacionados:** RNF-05: Chaves e credenciais armazenadas em variáveis de ambiente, fora do código versionado.

## 3. Validação da esteira DevSecOps

Após as correções, a esteira deve ser executada novamente para verificar:

- TruffleHog: análise de segredos nos commits do evento.
- Trivy: análise das dependências em busca de vulnerabilidades HIGH e CRITICAL.
- CodeQL: análise estática do código Python.

As evidências das novas execuções devem ser anexadas ao relatório técnico.

## 4. Histórico das alterações

| Arquivo | Alteração | Justificativa |
|---|---|---|
| `requirements.txt` | Pillow 12.3.0 para 13.0.0 | Corrigir vulnerabilidades identificadas pelo Trivy |
| `.github/workflows/devsecops-pipeline.yml` | Remoção de `base` e `head` explícitos | Evitar a repetição da análise integral do histórico |
| `Docs/Documentacoes_Tecnicas/Registro_Correcoes_DevSecOps.md` | Criação do registro técnico | Documentar decisões, justificativas e evidências |

**Observação:** os valores das credenciais antigas e atuais não devem ser publicados na documentação.