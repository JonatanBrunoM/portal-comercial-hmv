# Google OAuth: isolamento do estado temporário

Base: `nicegui-poc`, commit `d78c13da630efccc02bc5027dea83ddedc3ee854`.

## Problema e mudança

O Authlib guardava `_state_google_*` em `request.session`, compartilhada com o
armazenamento do navegador do NiceGUI e com `portal_auth`. Uma resposta concorrente
que regrave uma versão anterior desse cookie pode retirar o estado esperado pelo
callback. O erro informado ocorre antes da troca do código por token. Este mecanismo
foi reproduzido nos testes; os logs fornecidos não permitem provar que seja a única
causa no ambiente publicado.

O login agora entrega ao Authlib uma Request com escopo próprio e sessão temporária
independente. O cookie `portal_google_oauth` é assinado com o segredo já existente,
salt próprio, validade de 600 segundos, HttpOnly, SameSite=Lax e Secure quando a URL
pública usa HTTPS. Seu Path é `/auth/google`; respostas comuns do NiceGUI não o
reescrevem. O callback apaga esse cookie em sucesso ou erro. State e nonce continuam
validados pelo Authlib. Tokens e perfil não são gravados nesse cookie.

O início do login redireciona aliases para o host de `PORTAL_BASE_URL` antes de
criar o estado. O callback continua exatamente em `/auth/google/callback` dessa
URL. Não há novas variáveis de ambiente, mudanças no Google Cloud ou Supabase.
A sessão autenticada e o logout mantêm seu comportamento atual.

Há uma tentativa pendente por navegador: iniciar outra substitui a anterior.
Abas com tentativas anteriores devem reiniciar o login. Callbacks iniciados antes
do deploy também devem ser reiniciados, pois ainda usam o armazenamento antigo.

## Validação

`python -m pytest -q tests/test_google_oauth.py` (instalar pytest no ambiente de teste).
Os testes usam rotas HTTP e o Authlib real para geração/validação do state e passagem
do nonce; somente token, claims e acesso ao perfil são simulados, sem rede externa.
Cobrem cookie NiceGUI sobrescrito, login, logout, expiração, adulteração, state
ausente/incorreto, repetição de callback, nova tentativa, domínio, perfil inativo e
alias. A verificação criptográfica real do ID token pertence ao Authlib e não é
simulada como evidência de integração com o Google.

Antes de aprovar publicação, homologar no navegador: login em janela anônima,
logout/login, espera durante a escolha da conta, duas abas e acesso pelo endereço
público oficial. Confirmar que PORTAL_BASE_URL é HTTPS no Render e corresponde à
URI autorizada no Google; manter PORTAL_SESSION_SECRET estável entre instâncias.
Não foram usados segredos de produção nem executado login real com Google.

A proposta não altera requirements.txt, a branch de deploy ou render.yaml.
