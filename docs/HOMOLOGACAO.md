Roteiro de Homologação — Portal Comercial

Este roteiro deve ser executado antes de uma apresentação formal, piloto ou
liberação com dados reais.

1. Ambiente

Deploy concluído sem erro.

/health retorna HTTP 200.

/ready retorna HTTP 200 e todos os checks aparecem como ok: true.

Não existem segredos reais no GitHub.

.env não está versionado.

URL configurada em PORTAL_BASE_URL corresponde ao ambiente atual.

Redirect URI do Google OAuth corresponde ao ambiente atual.

2. Autenticação e sessão

Login com conta @hmv.org.br funciona.

Conta externa ao domínio institucional é recusada.

Perfil inativo não acessa o Portal.

Foto/nome do Google são exibidos corretamente.

Logout encerra a sessão.

Após logout, rota protegida redireciona para /login.

3. Navegação e responsividade

Home abre corretamente.

Sidebar permanece funcional em tela de notebook.

Área de navegação da sidebar possui scroll quando necessário.

Perfil da sidebar permanece visível.

Topbar está alinhada.

Navegação entre módulos ocorre sem reload completo perceptível.

Desktop e mobile não apresentam overflow horizontal inesperado.

4. Consulta pública

Validar com pelo menos uma operadora de teste:

Operadoras.

Planos.

Portais.

Documentos.

Contatos.

Consultores.

Comunicados publicados e vigentes.

Contingências programadas/ativas e vigentes.

Elegibilidade.

Autorizações.

Coberturas.

Dicas operacionais.

Registros inativos, rascunhos e fora do período não devem aparecer
publicamente.

5. Pesquisa

Testar:

busca pelo nome da operadora;

senha <operadora>;

telefone <operadora>;

como autorizar <operadora>;

elegibilidade <operadora>;

pesquisa com erros simples de digitação;

pesquisa iniciada pela Home;

pesquisa iniciada pela topbar;

filtro por área;

abertura do registro indicado como fonte.

A resposta conversacional deve ser montada somente a partir dos dados
cadastrados.

6. Administração

Com conta administradora:

Usuários.

Operadoras e planos.

Portais.

Documentos.

Contatos.

Consultores e carteiras.

Comunicados.

Contingências.

Credenciais.

Auditoria.

Com conta usuario, confirmar que rotas administrativas não são utilizáveis.

7. Credenciais protegidas

Utilizar somente credencial fictícia durante homologação.

Criar credencial.

Visualizar login.

Revelar senha.

Copiar senha.

Senha volta a ficar oculta automaticamente.

Alterar senha informando motivo.

Histórico recebe a versão anterior.

Reutilização da senha atual é bloqueada.

Política de N senhas anteriores é respeitada.

Rotação transacional funciona.

Auditoria registra alteração.

Auditoria registra revelação.

Tela de auditoria não exibe senha/ciphertext.

8. Auditoria

Página /administracao/auditoria abre para administrador.

Filtros por texto, ação, área e responsável funcionam.

Datas aparecem em horário de São Paulo.

Antes/depois aparecem quando disponíveis.

Campos sensíveis são mascarados.

Usuário comum não acessa a página.

9. Falhas controladas

Registro inexistente apresenta estado seguro.

Supabase temporariamente indisponível não expõe detalhes de chave/token.

Falha ao auditar revelação impede liberação da senha.

URL externa inválida não vira link executável.

Mensagens de erro não exibem payload sensível.

10. Aprovação

Registrar:

Versão/commit:
Ambiente:
Data:
Responsável técnico:
Responsável de negócio:
Resultado:
Pendências:
Aprovado para:
[ ] apresentação
[ ] piloto
[ ] produção
