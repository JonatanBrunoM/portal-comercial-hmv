from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from components.hero import render_hero
from config.settings import SHEETS
from core.dashboard_service import get_dashboard_summary
from core.sheets_service import (
    clear_sheets_cache,
    read_worksheet,
)


@dataclass(frozen=True)
class SheetDiagnostic:
    """Resultado do diagnóstico de uma aba."""

    sheet_key: str
    worksheet: str
    dataframe: pd.DataFrame
    missing_columns: tuple[str, ...]


EXPECTED_COLUMNS = {
    "operadoras": [
        "ID Operadora",
        "Operadora",
        "Nome curto",
        "Status",
    ],
    "planos": [
        "ID Plano",
        "ID Operadora",
        "Plano",
        "Status",
    ],
    "portais": [
        "ID Portal",
        "ID Operadora",
        "Nome do portal",
        "URL",
    ],
    "documentos": [
        "ID Documento",
        "ID Operadora",
        "Documento",
        "Obrigatório",
    ],
    "contatos": [
        "ID Contato",
        "ID Operadora",
        "Finalidade",
        "Tipo",
        "Contato",
    ],
    "contingencias": [
        "ID Contingência",
        "ID Operadora",
        "Evento",
        "Prioridade",
        "Status contingência",
    ],
    "comunicados": [
        "ID Comunicado",
        "Título",
        "Prioridade",
        "Status",
    ],
    "consultores": [
        "ID Consultor",
        "Nome",
        "E-mail",
        "Status",
    ],
    "carteiras": [
        "ID Consultor",
        "Operadora",
    ],
    "forum_posts": [
        "ID Post",
        "Título",
        "Conteúdo",
        "Status",
    ],
    "forum_comentarios": [
        "ID Comentário",
        "ID Post",
        "Comentário",
        "Status",
    ],
    "conhecimento": [
        "ID Conhecimento",
        "Pergunta",
        "Resposta",
        "Fonte",
    ],
    "particular": [
        "ID Particular",
        "Categoria",
        "Título",
        "Status",
    ],
}


def _is_admin_authenticated() -> bool:
    """Verifica se a sessão administrativa está autenticada."""

    return bool(
        st.session_state.get(
            "admin_authenticated",
            False,
        )
    )


def _authenticate_admin(
    password: str,
) -> bool:
    """Compara a senha informada com o Secret."""

    try:
        configured_password = str(
            st.secrets["ADMIN_PASSWORD"]
        )

    except KeyError:
        st.error(
            "A senha administrativa ainda não foi "
            "configurada nos Secrets."
        )
        return False

    return password == configured_password


def _render_admin_login() -> None:
    """Renderiza o formulário de acesso administrativo."""

    render_hero(
        eyebrow="Acesso restrito",
        title="Administração",
        description=(
            "Entre com a senha administrativa para "
            "acessar o diagnóstico e as configurações "
            "internas do Portal Comercial."
        ),
    )

    with st.form(
        key="admin_login_form",
        clear_on_submit=True,
    ):
        password = st.text_input(
            label="Senha administrativa",
            type="password",
            placeholder="Digite a senha...",
        )

        submitted = st.form_submit_button(
            "Entrar",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not password:
        st.warning(
            "Informe a senha administrativa."
        )
        return

    if _authenticate_admin(password):
        st.session_state.admin_authenticated = True
        st.success(
            "Acesso administrativo liberado."
        )
        st.rerun()

    else:
        st.error(
            "Senha administrativa incorreta."
        )


def _load_sheet_diagnostic(
    sheet_key: str,
) -> SheetDiagnostic:
    """Carrega uma única aba e verifica suas colunas."""

    worksheet = SHEETS[sheet_key]

    dataframe = read_worksheet(
        worksheet=worksheet,
        ttl=1800,
    )

    expected_columns = EXPECTED_COLUMNS.get(
        sheet_key,
        [],
    )

    missing_columns = tuple(
        column
        for column in expected_columns
        if column not in dataframe.columns
    )

    return SheetDiagnostic(
        sheet_key=sheet_key,
        worksheet=worksheet,
        dataframe=dataframe,
        missing_columns=missing_columns,
    )


def _render_summary() -> None:
    """Renderiza o resumo geral da base."""

    try:
        summary = get_dashboard_summary()

    except RuntimeError:
        st.warning(
            "Não foi possível carregar o resumo da base."
        )
        return

    col_1, col_2, col_3, col_4 = st.columns(4)

    col_1.metric(
        "Operadoras",
        summary.operadoras,
    )

    col_2.metric(
        "Planos",
        summary.planos,
    )

    col_3.metric(
        "Comunicados ativos",
        summary.comunicados,
    )

    col_4.metric(
        "Contingências ativas",
        summary.contingencias,
    )


def _render_sheet_diagnostic() -> None:
    """Permite diagnosticar uma aba por vez."""

    st.markdown(
        "## Diagnóstico das abas"
    )

    st.caption(
        "Selecione somente uma aba por vez. "
        "Isso reduz o número de consultas ao Google Sheets."
    )

    available_keys = [
        key
        for key in EXPECTED_COLUMNS
        if key in SHEETS
    ]

    selected_key = st.selectbox(
        label="Módulo",
        options=available_keys,
        format_func=lambda key: (
            f"{key.replace('_', ' ').title()} "
            f"— {SHEETS[key]}"
        ),
        key="admin_sheet_diagnostic",
    )

    if not st.button(
        "Executar diagnóstico",
        type="primary",
        use_container_width=True,
        key="admin_run_diagnostic",
    ):
        return

    try:
        with st.spinner(
            f"Analisando {SHEETS[selected_key]}..."
        ):
            diagnostic = _load_sheet_diagnostic(
                selected_key
            )

    except RuntimeError as error:
        st.error(
            "Não foi possível carregar a aba selecionada."
        )

        with st.expander(
            "Detalhes técnicos",
            expanded=False,
        ):
            st.code(
                str(error)
            )

        return

    dataframe = diagnostic.dataframe

    metric_1, metric_2, metric_3 = st.columns(3)

    metric_1.metric(
        "Registros",
        len(dataframe),
    )

    metric_2.metric(
        "Colunas",
        len(dataframe.columns),
    )

    metric_3.metric(
        "Colunas ausentes",
        len(diagnostic.missing_columns),
    )

    st.markdown(
        f"### `{diagnostic.worksheet}`"
    )

    if dataframe.empty:
        st.warning(
            "A aba existe, mas não possui registros."
        )
        return

    if diagnostic.missing_columns:
        st.warning(
            "Foram identificadas colunas esperadas "
            "que não existem nesta aba."
        )

        for column in diagnostic.missing_columns:
            st.markdown(
                f"- `{column}`"
            )

    else:
        st.success(
            "As colunas essenciais deste módulo "
            "foram encontradas."
        )

    with st.expander(
        "Colunas disponíveis",
        expanded=False,
    ):
        for column in dataframe.columns:
            st.markdown(
                f"- `{column}`"
            )

    st.markdown(
        "### Prévia dos dados"
    )

    preview = dataframe.head(
        10
    )

    st.dataframe(
        preview,
        use_container_width=True,
        hide_index=True,
    )

    duplicated_rows = int(
        dataframe.duplicated().sum()
    )

    completely_empty_columns = [
        column
        for column in dataframe.columns
        if dataframe[column].isna().all()
        or (
            dataframe[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
            .all()
        )
    ]

    st.markdown(
        "### Verificações adicionais"
    )

    check_1, check_2 = st.columns(2)

    check_1.metric(
        "Linhas duplicadas",
        duplicated_rows,
    )

    check_2.metric(
        "Colunas completamente vazias",
        len(completely_empty_columns),
    )

    if completely_empty_columns:
        with st.expander(
            "Ver colunas vazias",
            expanded=False,
        ):
            for column in completely_empty_columns:
                st.markdown(
                    f"- `{column}`"
                )


def render_admin() -> None:
    """Renderiza a primeira versão da área administrativa."""

    if not _is_admin_authenticated():
        _render_admin_login()
        return

    header_left, header_right = st.columns(
        [5, 1]
    )

    with header_left:
        render_hero(
            eyebrow="Centro de controle",
            title="Administração",
            description=(
                "Consulte a situação da base comercial, "
                "verifique estruturas e atualize o cache "
                "do portal."
            ),
        )

    with header_right:
        if st.button(
            "Sair",
            use_container_width=True,
            key="admin_logout",
        ):
            st.session_state.admin_authenticated = False
            st.rerun()

    st.warning(
        "Esta primeira versão é somente para diagnóstico. "
        "Nenhuma informação será alterada na planilha."
    )

    _render_summary()

    st.divider()

    action_1, action_2 = st.columns(2)

    with action_1:
        if st.button(
            "Atualizar dados do portal",
            type="primary",
            use_container_width=True,
            key="admin_refresh_cache",
        ):
            clear_sheets_cache()

            st.success(
                "O cache foi limpo. Os dados serão "
                "carregados novamente."
            )

            st.rerun()

    with action_2:
        st.info(
            "Use a atualização após modificar alguma "
            "informação diretamente no Google Sheets."
        )

    st.divider()

    _render_sheet_diagnostic()
