Arquitetura — Portal Comercial

Fluxo da aplicação

Navegador
   │
   │ HTTPS / WebSocket
   ▼
NiceGUI / FastAPI
   │
   ├── autenticação Google
   ├── autorização em Python
   ├── services
   └── repositories
          │
          ▼
   Supabase REST / RPC
          │
          ▼
      PostgreSQL

App shell

A interface usa ui.sub_pages. O shell principal — sidebar, topbar e sessão —
não é reconstruído a cada navegação. Essa decisão foi adotada para reduzir a
sensação de recarregamento entre módulos.

Camadas

pages

Responsáveis pela apresentação, eventos de UI e navegação.

services

Regras de negócio, filtros públicos, autorização específica, interpretação da
pesquisa e preparação dos dados para apresentação.

repositories

Acesso ao Supabase e persistência. Não devem implementar decisão visual.

data

Cliente HTTP server-side do Supabase, pool de conexões, cache institucional e
RPC.

security

Criptografia e funções relacionadas à proteção de credenciais.

Dados públicos e cache

Dados institucionais de leitura frequente podem usar cache/snapshot em memória.

Não devem participar desse cache:

profiles;

portal_credenciais;

historico_credenciais;

audit_logs.

Mutações feitas pelo Portal invalidam cache das tabelas institucionais
afetadas.

Credenciais

O navegador nunca recebe a chave Fernet. A descriptografia ocorre no servidor
somente quando a ação de revelar/copy é autorizada.

A rotação de senha deve utilizar a RPC portal_rotate_credential, que executa
historização, atualização e auditoria na mesma transação PostgreSQL.

Autorização

O Google OAuth autentica a identidade. O perfil interno em profiles define
permissão e status.

Mutações administrativas críticas reconsultam o perfil atual, em vez de
confiar apenas no papel armazenado na sessão.

Auditoria

audit_logs registra ações administrativas e acessos sensíveis relevantes.

A interface de auditoria mascara chaves potencialmente sensíveis. Auditoria
não é mecanismo de recuperação de senha.

Pesquisa interna

A busca utiliza regras locais:

normalização;

aliases de intenção;

ranking de campos;

tolerância a erros;

contexto de operadora;

resposta conversacional baseada nos registros encontrados.

Não existe chamada para modelo generativo externo nesta versão.

Operação

/health é liveness: verifica se a aplicação está respondendo.

/ready é readiness: verifica configuração, criptografia, OAuth e Supabase.

Separar esses conceitos evita reinícios desnecessários do serviço quando uma
dependência externa apresenta instabilidade temporária.
