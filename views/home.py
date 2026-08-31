import streamlit as st

from components.cards import (
    render_metric_card,
    render_module_card,
)
from components.hero import render_hero
from core.dashboard_service import get_dashboard_summary
from components.search_results import render_search_results
from core.search_service import search_global
from components.sidebar import navigate_to

def _priority_icon(
    priority: str,
) -> str:
    """Retorna o ícone correspondente à prioridade."""

    normalized = priority.strip().casefold()

    icons = {
        "alta": "🔴",
        "média": "🟠",
        "media": "🟠",
        "baixa": "🔵",
    }

    return icons.get(
        normalized,
        "📌",
    )


def _render_home_notices(
    summary,
) -> None:
    """Renderiza os comunicados ativos da Home."""

    header_left, header_right = st.columns(
        [5, 1]
    )

    with header_left:
        st.markdown(
            "## Comunicados importantes"
        )

    with header_right:
        if st.button(
            "Ver todos",
            key="home_all_notices",
            use_container_width=True,
        ):
            navigate_to(
                "Comunicados"
            )
            st.rerun()

    if not summary or not summary.notices:
        st.info(
            "Nenhum comunicado ativo neste momento."
        )
        return

    for notice in summary.notices:
        icon = _priority_icon(
            notice.priority
        )

        with st.container(
            border=True,
        ):
            st.markdown(
                f"### {icon} {notice.title}"
            )

            st.caption(
                f"{notice.category} • "
                f"{notice.operator_name}"
            )

            if notice.summary:
                st.write(
                    notice.summary
                )

            detail_1, detail_2 = st.columns(
                2
            )

            detail_1.markdown(
                f"**Prioridade:** "
                f"{notice.priority}"
            )

            period = ""

            if notice.start_date:
                period = notice.start_date

            if notice.end_date:
                period = (
                    f"{period} até "
                    f"{notice.end_date}"
                    if period
                    else (
                        f"Até "
                        f"{notice.end_date}"
                    )
                )

            detail_2.markdown(
                f"**Vigência:** "
                f"{period or 'Não informada'}"
            )


def _render_home_contingencies(
    summary,
) -> None:
    """Renderiza contingências ativas da Home."""

    header_left, header_right = st.columns(
        [5, 1]
    )

    with header_left:
        st.markdown(
            "## Contingências ativas"
        )

    with header_right:
        if st.button(
            "Ver todas",
            key="home_all_contingencies",
            use_container_width=True,
        ):
            navigate_to(
                "Contingências"
            )
            st.rerun()

    if (
        not summary
        or not summary.contingency_items
    ):
        st.success(
            "Nenhuma contingência ativa neste momento."
        )
        return

    for item in summary.contingency_items:
        icon = _priority_icon(
            item.priority
        )

        with st.container(
            border=True,
        ):
            st.markdown(
                f"### {icon} {item.event}"
            )

            st.caption(
                f"{item.operator_name} • "
                f"{item.unit}"
            )

            detail_1, detail_2 = st.columns(
                2
            )

            detail_1.markdown(
                f"**Prioridade:** "
                f"{item.priority}"
            )

            detail_2.markdown(
                f"**Status:** "
                f"{item.status}"
            )

            if item.guidance:
                st.markdown(
                    "**Orientação alternativa:**"
                )
                st.write(
                    item.guidance
                )

def render_home() -> None:
    """Renderiza a página inicial do Portal Comercial."""

    try:
        summary = get_dashboard_summary()
        data_error = None

    except RuntimeError:
        summary = None
        data_error = True

    render_hero(
        eyebrow="Hospital Moinhos de Vento",
        title="Comercial - Hospital Moinhos de Vento",
        description=(
            "Consulte operadoras, planos, documentos, portais, "
            "contatos e orientações em um único ambiente."
        ),
    )

    search_query = st.text_input(
        label="Pesquisa global",
        placeholder=(
            "Pesquise por operadora, plano, documento, "
            "procedimento ou orientação..."
        ),
        label_visibility="collapsed",
        key="home_search",
    )

    if data_error:
        st.warning(
            "Não foi possível carregar todos os indicadores da Home. "
            "Tente novamente em alguns instantes."
        )

    if search_query:
        with st.spinner(
            "Pesquisando na base comercial..."
        ):
            search_results = search_global(
                query=search_query,
                limit=12,
            )

        render_search_results(
            results=search_results,
            key_prefix="home_search",
        )

        st.divider()

    st.markdown(
        "## Visão geral"
    )

    col_1, col_2, col_3, col_4 = (
        st.columns(4)
    )

    with col_1:
        render_metric_card(
            title="Comunicados",
            value=(
                summary.comunicados
                if summary
                else "—"
            ),
            description=(
                "Comunicados ativos."
                if (
                    summary
                    and summary.comunicados
                )
                else (
                    "Nenhum comunicado ativo."
                )
            ),
            icon="📢",
        )

    with col_2:
        render_metric_card(
            title="Contingências",
            value=(
                summary.contingencias
                if summary
                else "—"
            ),
            description=(
                "Contingências ativas."
                if (
                    summary
                    and summary.contingencias
                )
                else (
                    "Nenhuma contingência ativa."
                )
            ),
            icon="⚠️",
        )

    with col_3:
        render_metric_card(
            title="Operadoras",
            value=(
                summary.operadoras
                if summary
                else "—"
            ),
            description=(
                "Operadoras ativas na base."
            ),
            icon="🏥",
        )

    with col_4:
        render_metric_card(
            title="Planos",
            value=(
                summary.planos
                if summary
                else "—"
            ),
            description=(
                "Planos ativos cadastrados."
            ),
            icon="📋",
        )

        st.divider()

    _render_home_notices(
        summary
    )

    st.divider()

    _render_home_contingencies(
        summary
    )

    st.divider()
    
    st.markdown("## Acessos rápidos")

    row_1 = st.columns(3)

    with row_1[0]:
        if render_module_card(
            title="Operadoras",
            description=(
                "Consulte planos, coberturas, documentos "
                "e informações relacionadas."
            ),
            icon="🏥",
            button_key="home_operadoras",
        ):
            navigate_to("Operadoras")
            st.rerun()

    with row_1[1]:
        if render_module_card(
            title="Portais",
            description=(
                "Encontre os portais utilizados para "
                "elegibilidade e autorizações."
            ),
            icon="🌐",
            button_key="home_portais",
        ):
            navigate_to("Portais")
            st.rerun()

    with row_1[2]:
        if render_module_card(
            title="Documentos",
            description=(
                "Consulte documentos obrigatórios, "
                "validade e orientações."
            ),
            icon="📄",
            button_key="home_documentos",
        ):
            navigate_to("Documentos")
            st.rerun()

    row_2 = st.columns(3)

    with row_2[0]:
        if render_module_card(
            title="Contatos",
            description=(
                "Localize telefones, e-mails, centrais "
                "e responsáveis."
            ),
            icon="📞",
            button_key="home_contatos",
        ):
            navigate_to("Contatos")
            st.rerun()

    with row_2[1]:
        if render_module_card(
            title="Contingências",
            description=(
                "Consulte indisponibilidades e fluxos "
                "alternativos."
            ),
            icon="⚠️",
            button_key="home_contingencias",
        ):
            navigate_to("Contingências")
            st.rerun()

    with row_2[2]:
        if render_module_card(
            title="Comunicados",
            description=(
                "Acompanhe avisos, mudanças e orientações "
                "relevantes das operadoras."
            ),
            icon="📢",
            button_key="home_comunicados",
        ):
            navigate_to("Comunicados")
            st.rerun()
