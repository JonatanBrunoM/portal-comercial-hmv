Portal Comercial — Hospital Moinhos de Vento

Portal interno para centralizar informações operacionais sobre operadoras e
planos de saúde: portais, acessos protegidos, documentos, contatos,
consultores, autorizações, elegibilidade, coberturas, comunicados e
contingências.

Arquitetura

O projeto utiliza:

NiceGUI 3.16 para a aplicação web Python-first;

FastAPI/Uvicorn no runtime do NiceGUI;

Supabase/PostgreSQL como banco;

Google OAuth com restrição ao domínio institucional @hmv.org.br;

Fernet para criptografia de senhas de portais externos;

Render para hospedagem do POC.

A aplicação utiliza um app shell persistente com ui.sub_pages. Sidebar,
topbar e sessão permanecem vivas enquanto somente a área central troca entre
os módulos.

Estrutura principal

app.py
nicegui_app/
  auth/
  data/
  pages/
  repositories/
  security/
  services/
  layout.py
  theme.py
styles/
  nicegui/
supabase/
  migrations/
docs/

A regra arquitetural é:

page → service → repository → Supabase

Páginas não devem concentrar acesso direto ao banco.

Configuração

Use .env.example apenas como referência. Em produção, configure os segredos
diretamente no Render.

Variáveis obrigatórias:

SUPABASE_URL

SUPABASE_SECRET_KEY (preferencial)

PORTAL_SESSION_SECRET

PORTAL_CREDENTIALS_FERNET_KEY

GOOGLE_CLIENT_ID

GOOGLE_CLIENT_SECRET

PORTAL_BASE_URL

Nenhum segredo real deve ser versionado.

Executar localmente

python -m venv .venv

Ative o ambiente virtual, instale:

pip install -r requirements.txt

Configure as variáveis de ambiente e execute:

python app.py

Por padrão, o Portal abre em http://localhost:8080.

Endpoints operacionais

/health — confirma que o processo web está respondendo;

/ready — verifica configuração crítica, Google OAuth, criptografia e
conexão com Supabase. Não retorna segredos.

Para o Render, mantenha /health como health check. /ready é destinado a
homologação e diagnóstico.

Segurança das credenciais

As senhas de portais externos:

nunca são armazenadas em texto puro;

são criptografadas com Fernet;

só podem ser reveladas para perfil institucional ativo;

têm revelações auditadas;

não são liberadas quando a auditoria obrigatória falha;

mantêm histórico criptografado;

bloqueiam reutilização conforme a política configurada;

usam rotação transacional no PostgreSQL quando a migration da Etapa 17 está
instalada.

Nunca registrar senha, token Fernet, chave Supabase ou OAuth em logs.

Perfis

Os papéis atuais são:

usuario — consulta operacional;

admin — administração e manutenção dos cadastros.

O acesso administrativo é revalidado no servidor antes de mutações críticas.

Pesquisa

A Pesquisa Inteligente é interna e determinística. Ela interpreta intenção,
contexto e erros de digitação usando exclusivamente os registros cadastrados
no Portal. Nesta versão não existe dependência de IA generativa externa.

Deploy

O render.yaml usa:

build: pip install -r requirements.txt
start: python app.py
health: /health

Antes de liberar uma versão, execute o roteiro em
docs/HOMOLOGACAO.md.

Estado desta versão

Esta entrega corresponde à primeira versão funcional do Portal Comercial,
incluindo navegação SPA, Home, pesquisa interna, módulos públicos,
Administração, credenciais seguras e auditoria.

Antes de uso produtivo com dados reais, homologar integralmente os fluxos e
validar as políticas internas de segurança, infraestrutura e governança do
Hospital.
