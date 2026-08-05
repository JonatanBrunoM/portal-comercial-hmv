from __future__ import annotations
from dataclasses import dataclass
from utils.formatting import normalize_text

import pandas as pd
import streamlit as st


from components.hero import render_hero
from config.settings import SHEETS
from core.dashboard_service import get_dashboard_summary
from core.sheets_service import (
    clear_sheets_cache,
    read_worksheet,
    update_worksheet,
)
from core.data_quality_service import (
    QualityIssue,
    analyze_sheet_quality,
)
from core.publication_service import (
    PUBLICATION_RULES,
    analyze_publication_status,
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

STATUS_EDIT_RULES = {
    "operadoras": {
        "id_column": "ID Operadora",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
    "planos": {
        "id_column": "ID Plano",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
    "portais": {
        "id_column": "ID Portal",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
    "documentos": {
        "id_column": "ID Documento",
        "status_column": "Status revisão",
        "options": [
            "Pendente",
            "Em revisão",
            "Revisado",
            "Publicável",
        ],
    },
    "contatos": {
        "id_column": "ID Contato",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
    "contingencias": {
        "id_column": "ID Contingência",
        "status_column": "Status contingência",
        "options": [
            "Pendente",
            "Ativa",
            "Encerrada",
            "Inativa",
        ],
    },
    "comunicados": {
        "id_column": "ID Comunicado",
        "status_column": "Status",
        "options": [
            "Rascunho",
            "Pendente",
            "Publicado",
            "Inativo",
        ],
    },
    "consultores": {
        "id_column": "ID Consultor",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
    "forum_posts": {
        "id_column": "ID Post",
        "status_column": "Status",
        "options": [
            "Pendente",
            "Publicado",
            "Oculto",
            "Inativo",
        ],
    },
    "forum_comentarios": {
        "id_column": "ID Comentário",
        "status_column": "Status",
        "options": [
            "Pendente",
            "Publicado",
            "Oculto",
            "Inativo",
        ],
    },
    "conhecimento": {
        "id_column": "ID Conhecimento",
        "status_column": "Status revisão",
        "options": [
            "Pendente",
            "Em revisão",
            "Revisado",
            "Publicável",
        ],
    },
    "particular": {
        "id_column": "ID Particular",
        "status_column": "Status",
        "options": [
            "Ativo",
            "Inativo",
        ],
    },
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


def _severity_icon(
    severity: str,
) -> str:
    """Retorna o ícone visual da severidade."""

    return {
        "Crítico": "🔴",
        "Alerta": "🟠",
        "Informativo": "🔵",
    }.get(
        severity,
        "⚪",
    )


def _render_quality_issue(
    issue: QualityIssue,
    position: int,
) -> None:
    """Renderiza um problema de qualidade."""

    icon = _severity_icon(
        issue.severity
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### {icon} {issue.issue_type}"
        )

        st.caption(
            f"{issue.severity} • Coluna: {issue.column}"
        )

        st.write(
            issue.message
        )

        st.metric(
            "Registros afetados",
            issue.affected_rows,
        )

        if issue.examples:
            with st.expander(
                "Ver exemplos",
                expanded=False,
            ):
                for example in issue.examples:
                    st.markdown(
                        f"- `{example}`"
                    )


def _render_quality_panel() -> None:
    """Renderiza o painel de qualidade da base."""

    st.markdown(
        "## Qualidade da base"
    )

    st.caption(
        "A análise é executada em apenas uma aba por vez "
        "para reduzir o consumo da API do Google Sheets."
    )

    available_keys = [
        key
        for key in EXPECTED_COLUMNS
        if key in SHEETS
    ]

    selected_key = st.selectbox(
        label="Módulo para análise",
        options=available_keys,
        format_func=lambda key: (
            f"{key.replace('_', ' ').title()} "
            f"— {SHEETS[key]}"
        ),
        key="admin_quality_module",
    )

    if not st.button(
        "Analisar qualidade",
        type="primary",
        use_container_width=True,
        key="admin_run_quality",
    ):
        return

    try:
        with st.spinner(
            f"Analisando {SHEETS[selected_key]}..."
        ):
            report = analyze_sheet_quality(
                selected_key
            )

    except (RuntimeError, ValueError) as error:
        st.error(
            "Não foi possível executar a análise."
        )

        with st.expander(
            "Detalhes técnicos",
            expanded=False,
        ):
            st.code(
                str(error)
            )

        return

    score_1, score_2, score_3, score_4 = (
        st.columns(4)
    )

    score_1.metric(
        "Nota da base",
        f"{report.score}/100",
    )

    score_2.metric(
        "Problemas críticos",
        report.critical_issues,
    )

    score_3.metric(
        "Alertas",
        report.warning_issues,
    )

    score_4.metric(
        "Informativos",
        report.info_issues,
    )

    if report.score >= 90:
        st.success(
            "A aba apresenta boa qualidade para testes."
        )

    elif report.score >= 70:
        st.warning(
            "A aba pode ser utilizada, mas possui "
            "pontos que precisam de revisão."
        )

    else:
        st.error(
            "A aba possui problemas relevantes e deve "
            "ser revisada antes da publicação."
        )

    st.caption(
        f"{report.total_rows} registro(s) • "
        f"{report.total_columns} coluna(s) • "
        f"Aba: {report.worksheet}"
    )

    if not report.issues:
        st.success(
            "Nenhum problema foi identificado pelas "
            "regras atuais."
        )
        return

    severity_filter = st.multiselect(
        label="Filtrar severidade",
        options=[
            "Crítico",
            "Alerta",
            "Informativo",
        ],
        default=[
            "Crítico",
            "Alerta",
            "Informativo",
        ],
        key="admin_quality_severity_filter",
    )

    filtered_issues = [
        issue
        for issue in report.issues
        if issue.severity in severity_filter
    ]

    st.caption(
        f"{len(filtered_issues)} problema(s) exibido(s)."
    )

    for position, issue in enumerate(
        filtered_issues
    ):
        _render_quality_issue(
            issue=issue,
            position=position,
        )

def _publication_status_icon(
    status: str,
) -> str:
    """Retorna o ícone de publicação."""

    icons = {
        "Pronto": "🟢",
        "Pendente": "🟡",
        "Incompleto": "🔴",
        "Inativo": "⚪",
        "Não identificado": "🟠",
    }

    return icons.get(
        status,
        "⚪",
    )


def _render_publication_record(
    row: pd.Series,
    position: int,
) -> None:
    """Renderiza um registro da central de publicação."""

    record_id = str(
        row.get(
            "_record_id",
            "Sem ID",
        )
    )

    title = str(
        row.get(
            "_record_title",
            "Registro sem título",
        )
    )

    publication_status = str(
        row.get(
            "_publication_status",
            "Não identificado",
        )
    )

    original_status = str(
        row.get(
            "_status_original",
            "",
        )
    )

    missing_fields = str(
        row.get(
            "_missing_fields",
            "",
        )
    )

    icon = _publication_status_icon(
        publication_status
    )

    with st.container(
        border=True,
    ):
        title_col, status_col = st.columns(
            [4, 1]
        )

        with title_col:
            st.markdown(
                f"### {icon} {title}"
            )

            st.caption(
                f"Identificador: {record_id}"
            )

        with status_col:
            st.markdown(
                f"**{publication_status}**"
            )

        if original_status:
            st.markdown(
                f"**Status na planilha:** "
                f"{original_status}"
            )

        else:
            st.warning(
                "O registro não possui status preenchido."
            )

        if missing_fields:
            st.error(
                "Campos obrigatórios ausentes: "
                f"{missing_fields}"
            )

        with st.expander(
            "Visualizar dados do registro",
            expanded=False,
        ):
            hidden_columns = {
                "_record_id",
                "_record_title",
                "_status_original",
                "_status_normalized",
                "_missing_fields",
                "_publication_status",
                "_status_order",
            }

            visible_items = [
                (
                    column,
                    row[column],
                )
                for column in row.index
                if column not in hidden_columns
                and not pd.isna(
                    row[column]
                )
                and str(
                    row[column]
                ).strip()
                not in {
                    "",
                    "nan",
                    "None",
                }
            ]

            if not visible_items:
                st.caption(
                    "Nenhuma informação adicional "
                    "foi encontrada."
                )

            for column, value in visible_items:
                st.markdown(
                    f"**{column}:** {value}"
                )


def _render_publication_panel() -> None:
    """Renderiza a central de revisão e publicação."""

    st.markdown(
        "## Revisão e publicação"
    )

    st.caption(
        "Esta tela ainda não altera a planilha. "
        "Ela identifica quais registros estão prontos, "
        "pendentes, incompletos ou inativos."
    )

    available_keys = [
        key
        for key in PUBLICATION_RULES
        if key in SHEETS
    ]

    selected_key = st.selectbox(
        label="Módulo para revisão",
        options=available_keys,
        format_func=lambda key: (
            f"{key.replace('_', ' ').title()} "
            f"— {SHEETS[key]}"
        ),
        key="admin_publication_module",
    )

    if not st.button(
        "Carregar registros",
        type="primary",
        use_container_width=True,
        key="admin_load_publication",
    ):
        return

    try:
        with st.spinner(
            f"Analisando {SHEETS[selected_key]}..."
        ):
            summary = analyze_publication_status(
                selected_key
            )

    except (RuntimeError, ValueError) as error:
        st.error(
            "Não foi possível carregar a situação "
            "de publicação."
        )

        with st.expander(
            "Detalhes técnicos",
            expanded=False,
        ):
            st.code(
                str(error)
            )

        return

    metric_1, metric_2, metric_3, metric_4 = (
        st.columns(4)
    )

    metric_1.metric(
        "Total",
        summary.total,
    )

    metric_2.metric(
        "Prontos",
        summary.ready,
    )

    metric_3.metric(
        "Pendentes ou incompletos",
        summary.pending,
    )

    metric_4.metric(
        "Inativos",
        summary.inactive,
    )

    if summary.unidentified:
        st.warning(
            f"{summary.unidentified} registro(s) possuem "
            "situação de publicação não identificada."
        )

    if summary.dataframe.empty:
        st.info(
            "A aba selecionada não possui registros."
        )
        return

    status_options = [
        "Todos",
        "Pronto",
        "Pendente",
        "Incompleto",
        "Inativo",
        "Não identificado",
    ]

    filter_col, search_col = st.columns(
        [1, 2]
    )

    with filter_col:
        selected_status = st.selectbox(
            label="Situação",
            options=status_options,
            key="admin_publication_status_filter",
        )

    with search_col:
        query = st.text_input(
            label="Pesquisar registros",
            placeholder=(
                "Pesquise pelo título ou identificador..."
            ),
            key="admin_publication_search",
        )

    filtered = summary.dataframe.copy()

    if selected_status != "Todos":
        filtered = filtered[
            filtered["_publication_status"]
            .eq(
                selected_status
            )
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        search_text = (
            filtered["_record_id"]
            .fillna("")
            .astype(str)
            + " "
            + filtered["_record_title"]
            .fillna("")
            .astype(str)
        ).map(
            normalize_text
        )

        filtered = filtered[
            search_text.str.contains(
                normalized_query,
                regex=False,
                na=False,
            )
        ]

    st.caption(
        f"{len(filtered)} registro(s) exibido(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum registro corresponde aos "
            "filtros selecionados."
        )
        return

    for position, (_, row) in enumerate(
        filtered.head(30).iterrows()
    ):
        _render_publication_record(
            row=row,
            position=position,
        )

    if len(filtered) > 30:
        st.info(
            "Somente os primeiros 30 registros estão "
            "sendo exibidos nesta versão."
        )

def _update_record_status(
    sheet_key: str,
    record_id: str,
    new_status: str,
) -> None:
    """
    Atualiza somente o campo de status de um registro.
    """

    if sheet_key not in STATUS_EDIT_RULES:
        raise ValueError(
            "Este módulo não permite edição de status."
        )

    if sheet_key not in SHEETS:
        raise ValueError(
            "A aba deste módulo não foi configurada."
        )

    rules = STATUS_EDIT_RULES[
        sheet_key
    ]

    worksheet = SHEETS[
        sheet_key
    ]

    id_column = rules[
        "id_column"
    ]

    status_column = rules[
        "status_column"
    ]

    allowed_options = rules[
        "options"
    ]

    if new_status not in allowed_options:
        raise ValueError(
            "O status selecionado não é permitido."
        )

    dataframe = read_worksheet(
        worksheet=worksheet,
        ttl=0,
    ).copy()

    if dataframe.empty:
        raise ValueError(
            "A aba selecionada não possui registros."
        )

    if id_column not in dataframe.columns:
        raise ValueError(
            f"A coluna '{id_column}' não existe "
            f"na aba '{worksheet}'."
        )

    if status_column not in dataframe.columns:
        dataframe[
            status_column
        ] = ""

    normalized_ids = (
        dataframe[id_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    record_mask = normalized_ids.eq(
        str(record_id).strip()
    )

    affected_rows = int(
        record_mask.sum()
    )

    if affected_rows == 0:
        raise ValueError(
            "O registro selecionado não foi localizado."
        )

    if affected_rows > 1:
        raise ValueError(
            "Existem IDs duplicados na aba. "
            "A atualização foi bloqueada para evitar "
            "alterações em múltiplos registros."
        )

    dataframe.loc[
        record_mask,
        status_column,
    ] = new_status

    update_worksheet(
        worksheet=worksheet,
        dataframe=dataframe,
    )

    clear_sheets_cache()

def _render_status_editor() -> None:
    """
    Renderiza a primeira ferramenta administrativa
    de escrita no Google Sheets.
    """

    st.markdown(
        "## Alteração de status"
    )

    st.warning(
        "Esta ferramenta altera somente o status do "
        "registro selecionado. Os demais campos serão "
        "preservados."
    )

    available_modules = [
        key
        for key in STATUS_EDIT_RULES
        if key in SHEETS
    ]

    selected_module = st.selectbox(
        label="Módulo",
        options=available_modules,
        format_func=lambda key: (
            f"{key.replace('_', ' ').title()} "
            f"— {SHEETS[key]}"
        ),
        key="admin_status_module",
    )

    rules = STATUS_EDIT_RULES[
        selected_module
    ]

    worksheet = SHEETS[
        selected_module
    ]

    try:
        dataframe = read_worksheet(
            worksheet=worksheet,
            ttl=600,
        )

    except RuntimeError as error:
        st.error(
            "Não foi possível carregar os registros."
        )

        with st.expander(
            "Detalhes técnicos",
            expanded=False,
        ):
            st.code(
                str(error)
            )

        return

    if dataframe.empty:
        st.info(
            "A aba selecionada não possui registros."
        )
        return

    id_column = rules[
        "id_column"
    ]

    status_column = rules[
        "status_column"
    ]

    if id_column not in dataframe.columns:
        st.error(
            f"A coluna obrigatória '{id_column}' "
            "não existe nesta aba."
        )
        return

    record_options = (
        dataframe[id_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    record_options = [
        value
        for value in record_options
        if value
    ]

    if not record_options:
        st.error(
            "Nenhum registro com identificador válido "
            "foi encontrado."
        )
        return

    selected_record_id = st.selectbox(
        label="Registro",
        options=record_options,
        key="admin_status_record",
    )

    selected_row = dataframe[
        dataframe[id_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(selected_record_id)
    ].iloc[0]

    current_status = ""

    if status_column in selected_row.index:
        value = selected_row[
            status_column
        ]

        if not pd.isna(value):
            current_status = str(
                value
            ).strip()

    st.info(
        f"Status atual: "
        f"{current_status or 'Não informado'}"
    )

    new_status = st.selectbox(
        label="Novo status",
        options=rules[
            "options"
        ],
        index=(
            rules["options"].index(
                current_status
            )
            if current_status
            in rules["options"]
            else 0
        ),
        key="admin_new_status",
    )

    with st.expander(
        "Visualizar registro antes da alteração",
        expanded=False,
    ):
        preview = pd.DataFrame(
            [selected_row]
        )

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )

    confirmation = st.checkbox(
        label=(
            "Confirmo que revisei o registro e desejo "
            "alterar seu status."
        ),
        key="admin_status_confirmation",
    )

    save_disabled = (
        not confirmation
        or new_status == current_status
    )

    if st.button(
        "Salvar novo status",
        type="primary",
        use_container_width=True,
        disabled=save_disabled,
        key="admin_save_status",
    ):
        try:
            with st.spinner(
                "Atualizando a planilha..."
            ):
                _update_record_status(
                    sheet_key=selected_module,
                    record_id=selected_record_id,
                    new_status=new_status,
                )

        except (
            RuntimeError,
            ValueError,
        ) as error:
            st.error(
                "Não foi possível atualizar o status."
            )

            with st.expander(
                "Detalhes técnicos",
                expanded=False,
            ):
                st.code(
                    str(error)
                )

            return

        st.success(
            f"O registro '{selected_record_id}' "
            f"foi atualizado para '{new_status}'."
        )

        st.session_state[
            "admin_status_confirmation"
        ] = False

        st.rerun()

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

    st.divider()

    _render_quality_panel()

    st.divider()

    _render_publication_panel()

    st.divider()

    _render_status_editor()
