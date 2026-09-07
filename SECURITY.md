Segurança — Portal Comercial

Princípios

Nenhum segredo deve existir no repositório.

Credenciais de portais externos não são armazenadas em texto puro.

Autorização administrativa é validada no servidor.

Acesso a senha é auditável.

Logs não devem conter senha, chave Fernet, token OAuth ou chave Supabase.

A Pesquisa não utiliza dados externos para inventar orientação operacional.

Segredos

Configurar exclusivamente por variáveis de ambiente no ambiente de deploy.

Rotacionar imediatamente qualquer segredo que tenha sido publicado em commit,
issue, chat público ou log compartilhado.

Credenciais externas

A chave PORTAL_CREDENTIALS_FERNET_KEY protege os ciphertexts existentes.
Trocar essa chave sem plano de migração torna credenciais antigas
indescriptografáveis.

Uma estratégia futura de rotação de chave deve suportar múltiplas versões de
chave ou recriptografia controlada.

Cabeçalhos HTTP

O Portal configura:

X-Content-Type-Options: nosniff;

X-Frame-Options: DENY;

Referrer-Policy: same-origin;

Permissions-Policy restritiva;

HSTS no Render;

Cache-Control: no-store em autenticação e readiness.

Uma Content-Security-Policy estrita não foi adicionada nesta versão porque
deve ser homologada em conjunto com os scripts/recursos necessários ao
NiceGUI para evitar quebra do frontend.

Produção

Antes de uso com dados reais:

concluir o roteiro docs/HOMOLOGACAO.md;

revisar permissões e chaves do Supabase;

confirmar backup/recuperação do PostgreSQL;

definir responsáveis por administração do Portal;

definir processo formal de rotação da chave Fernet;

revisar retenção de audit_logs e histórico de credenciais;

confirmar requisitos institucionais de infraestrutura e segurança.
