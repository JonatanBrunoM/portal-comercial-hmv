from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from config.settings import DATASETS
from core.admin_portals_service import (
    get_all_credentials,
    get_all_portals,
    save_credential,
    save_portal,
)
from core.admin_master_data_service import (
    get_all_attendance_types,
    get_all_locations,
    get_all_operators,
    get_all_plans,
    get_plan_location_ids,
    save_attendance_type,
    save_location,
    save_operator,
    save_plan,
)
from core.admin_rules_service import (
    get_all_authorizations,
    get_all_coverages,
    get_all_documents,
    get_all_eligibility,
    save_authorization,
    save_coverage,
    save_document,
    save_eligibility,
)
from core.auth_service import get_current_profile
from core.credentials_service import format_timestamp, get_credential_history
from core.data_service import (
    clear_data_cache,
    get_locais_atendimento,
    get_operadoras,
    get_planos,
    read_dataset,
)
from core.supabase_repository import check_supabase_connection, fetch_table


ADMIN_DATASETS = [
    "operadoras", "planos", "portais", "elegibilidade", "documentos",
    "autorizacoes", "coberturas", "contatos", "contingencias",
    "dicas_operacionais", "consultores", "carteiras", "comunicados",
    "locais_atendimento", "tipos_atendimento", "plano_locais",
]


def _is_admin() -> bool:
    profile = get_current_profile()
    return bool(profile and profile.get("status") == "Ativo" and profile.get("role") == "admin")


def _safe(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _row_by_id(dataframe: pd.DataFrame, record_id: str) -> dict:
    if dataframe.empty or not record_id or "id" not in dataframe.columns:
        return {}
    matches = dataframe[dataframe["id"].astype(str) == str(record_id)]
    return matches.iloc[0].to_dict() if not matches.empty else {}


def _options(dataframe: pd.DataFrame, label_columns: tuple[str, ...]) -> tuple[list[str], dict[str, str]]:
    if dataframe.empty:
        return [], {}

    ids: list[str] = []
    labels: dict[str, str] = {}
    for _, row in dataframe.iterrows():
        record_id = _safe(row.get("id"))
        if not record_id:
            continue
        label = next((_safe(row.get(column)) for column in label_columns if _safe(row.get(column))), record_id)
        ids.append(record_id)
        labels[record_id] = label
    return ids, labels


def _index(options: list[str | None], value: object) -> int:
    normalized = None if value is None or pd.isna(value) else str(value)
    try:
        return options.index(normalized)
    except ValueError:
        return 0


def _render_overview() -> None:
    st.markdown("## Visão geral da base")
    cols = st.columns(4)
    counts: list[tuple[str, int]] = []
    for key in ADMIN_DATASETS:
        try:
            counts.append((key, len(read_dataset(key))))
        except Exception:
            counts.append((key, -1))

    for index, (key, count) in enumerate(counts):
        label = key.replace("_", " ").title()
        value = count if count >= 0 else "Erro"
        cols[index % 4].metric(label, value)


def _render_dataset_browser() -> None:
    st.markdown("## Dados no Supabase")
    selected = st.selectbox(
        "Conjunto de dados",
        options=ADMIN_DATASETS,
        format_func=lambda item: item.replace("_", " ").title(),
    )

    try:
        dataframe = read_dataset(selected)
    except Exception:
        st.error(f"Não foi possível carregar '{selected}'.")
        return

    st.caption(f"Tabela: `{DATASETS[selected]}` · {len(dataframe)} registro(s)")
    if dataframe.empty:
        st.info("Este conjunto ainda não possui registros.")
        return

    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def _render_users() -> None:
    st.markdown("## Usuários")
    try:
        dataframe = fetch_table("profiles", order_by="nome")
        visible_columns = [
            "id", "nome", "email", "role", "status", "primeiro_acesso_em",
            "ultimo_acesso_em", "ultimo_login_em",
        ]
        dataframe = dataframe[[column for column in visible_columns if column in dataframe.columns]]
    except Exception:
        st.error("Não foi possível carregar os usuários.")
        return

    if dataframe.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    st.dataframe(dataframe, use_container_width=True, hide_index=True)
    st.caption("A alteração de perfis e permissões será tratada em módulo administrativo próprio.")


def _render_portal_management() -> None:
    st.markdown("## Portais")
    st.caption("Cadastre e mantenha os canais digitais utilizados nas rotinas com as operadoras.")

    try:
        portals = get_all_portals()
        operators = get_operadoras()
        plans = get_planos()
        locations = get_locais_atendimento()
    except Exception:
        st.error("Não foi possível carregar os dados necessários para administrar os portais.")
        return

    portal_ids, portal_labels = _options(portals, ("nome", "codigo"))
    operator_ids, operator_labels = _options(operators, ("nome_curto", "nome"))
    plan_ids, plan_labels = _options(plans, ("nome_padronizado", "nome"))
    location_ids, location_labels = _options(locations, ("nome", "codigo"))

    mode = st.radio(
        "Ação",
        ["Editar portal existente", "Cadastrar novo portal"],
        horizontal=True,
        key="admin_portal_mode",
    )

    selected_portal_id = ""
    current: dict = {}
    if mode == "Editar portal existente":
        if not portal_ids:
            st.info("Nenhum portal cadastrado.")
            return
        selected_portal_id = st.selectbox(
            "Portal",
            portal_ids,
            format_func=lambda item: portal_labels.get(item, item),
            key="admin_portal_selected",
        )
        current = _row_by_id(portals, selected_portal_id)

    filtered_plan_ids = plan_ids
    selected_operator_default = _safe(current.get("operadora_id"))

    with st.form("admin_portal_form"):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("Código", value=_safe(current.get("codigo")), placeholder="Ex.: PORTAL_UNIMED")
            name = st.text_input("Nome do portal *", value=_safe(current.get("nome")))
            operator_id = st.selectbox(
                "Operadora *",
                operator_ids,
                index=_index(operator_ids, selected_operator_default),
                format_func=lambda item: operator_labels.get(item, item),
            ) if operator_ids else ""
            portal_type = st.text_input("Finalidade / tipo", value=_safe(current.get("tipo")), placeholder="Ex.: Elegibilidade e autorização")
            url = st.text_input("URL", value=_safe(current.get("url")), placeholder="https://...")

        with col2:
            plan_options: list[str | None] = [None] + filtered_plan_ids
            plan_id = st.selectbox(
                "Plano específico",
                plan_options,
                index=_index(plan_options, current.get("plano_id")),
                format_func=lambda item: "Todos / não específico" if item is None else plan_labels.get(str(item), str(item)),
            )
            location_options: list[str | None] = [None] + location_ids
            location_id = st.selectbox(
                "Local específico",
                location_options,
                index=_index(location_options, current.get("local_id")),
                format_func=lambda item: "Todos / não específico" if item is None else location_labels.get(str(item), str(item)),
            )
            requires_login = st.checkbox("Exige login", value=bool(current.get("exige_login", False)))
            status = st.selectbox(
                "Status",
                ["Ativo", "Inativo"],
                index=0 if _safe(current.get("status")) != "Inativo" else 1,
            )

        access_instruction = st.text_area("Como acessar", value=_safe(current.get("instrucao_acesso")), height=100)
        general_tip = st.text_area("Dica geral de acesso", value=_safe(current.get("dica_geral_acesso")), height=90)
        observations = st.text_area("Observações", value=_safe(current.get("observacoes")), height=90)

        submitted = st.form_submit_button("Salvar portal", type="primary", use_container_width=True)

    if submitted:
        try:
            save_portal(
                portal_id=selected_portal_id or None,
                code=code,
                operator_id=operator_id,
                plan_id=plan_id,
                location_id=location_id,
                name=name,
                portal_type=portal_type,
                url=url,
                requires_login=requires_login,
                access_instruction=access_instruction,
                general_tip=general_tip,
                observations=observations,
                status=status,
            )
            st.success("Portal salvo com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar o portal. Verifique os dados e tente novamente.")


def _render_credential_management() -> None:
    st.markdown("## Credenciais")
    st.caption("Gerencie logins e senhas institucionais. A senha é criptografada antes de ser gravada no Supabase.")

    try:
        portals = get_all_portals()
    except Exception:
        st.error("Não foi possível carregar os portais.")
        return

    portal_ids, portal_labels = _options(portals, ("nome", "codigo"))
    if not portal_ids:
        st.info("Cadastre um portal antes de criar uma credencial.")
        return

    selected_portal_id = st.selectbox(
        "Portal",
        portal_ids,
        format_func=lambda item: portal_labels.get(item, item),
        key="admin_credentials_portal",
    )

    try:
        credentials = get_all_credentials(selected_portal_id)
    except Exception:
        st.error("Não foi possível carregar as credenciais deste portal.")
        return

    credential_ids, credential_labels = _options(credentials, ("identificacao", "login"))
    mode = st.radio(
        "Ação da credencial",
        ["Editar credencial existente", "Cadastrar nova credencial"],
        horizontal=True,
        key="admin_credential_mode",
    )

    credential_id = ""
    current: dict = {}
    if mode == "Editar credencial existente":
        if not credential_ids:
            st.info("Este portal ainda não possui credenciais. Selecione 'Cadastrar nova credencial'.")
            return
        credential_id = st.selectbox(
            "Credencial",
            credential_ids,
            format_func=lambda item: credential_labels.get(item, item),
            key="admin_credential_selected",
        )
        current = _row_by_id(credentials, credential_id)

    with st.form("admin_credential_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            identification = st.text_input("Identificação *", value=_safe(current.get("identificacao")), placeholder="Ex.: Acesso principal")
            login = st.text_input("Login / usuário", value=_safe(current.get("login")))
            new_password = st.text_input(
                "Nova senha *" if not credential_id else "Nova senha",
                type="password",
                help="Ao editar, deixe em branco para manter a senha atual.",
            )
            status = st.selectbox(
                "Status",
                ["Ativo", "Inativo"],
                index=0 if _safe(current.get("status")) != "Inativo" else 1,
            )

        with col2:
            blocked_count = st.number_input(
                "Quantidade de senhas anteriores bloqueadas",
                min_value=0,
                max_value=50,
                value=int(current.get("quantidade_senhas_bloqueadas") or 0),
                step=1,
            )
            password_rule = st.text_area("Regra de senha", value=_safe(current.get("regra_senha_observacao")), height=90)
            access_tip = st.text_area("Dica de acesso", value=_safe(current.get("dica_acesso")), height=90)

        observations = st.text_area("Observações da credencial", value=_safe(current.get("observacoes")), height=80)
        change_reason = st.text_input(
            "Motivo da troca de senha" if credential_id else "Motivo / referência do cadastro",
            placeholder="Ex.: Expiração periódica da senha",
        )

        submitted = st.form_submit_button("Salvar credencial", type="primary", use_container_width=True)

    if submitted:
        try:
            save_credential(
                credential_id=credential_id or None,
                portal_id=selected_portal_id,
                identification=identification,
                login=login,
                new_password=new_password,
                access_tip=access_tip,
                observations=observations,
                blocked_password_count=int(blocked_count),
                password_rule=password_rule,
                status=status,
                change_reason=change_reason,
            )
            st.success("Credencial salva com segurança.")
            st.rerun()
        except RuntimeError as error:
            st.warning(str(error))
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar a credencial. Nenhuma senha foi exibida nos detalhes do erro.")

    if credential_id:
        changed_at = current.get("senha_alterada_em") or current.get("updated_at")
        st.caption(f"Última atualização: {format_timestamp(changed_at)}")
        try:
            history = get_credential_history(credential_id)
        except Exception:
            history = pd.DataFrame()
        if not history.empty:
            with st.expander(f"Histórico de alterações ({len(history)})"):
                for _, row in history.iterrows():
                    st.write(f"**{format_timestamp(row.get('alterado_em'))}** — {_safe(row.get('motivo_alteracao')) or 'Sem motivo informado'}")
                    if _safe(row.get("login")):
                        st.caption(f"Login anterior: {_safe(row.get('login'))}")
                st.caption("Por segurança, senhas históricas não são exibidas no backoffice.")



def _render_operator_management() -> None:
    st.markdown("### Operadoras")
    st.caption("Cadastre, edite ou inative as operadoras utilizadas no Portal Comercial.")

    try:
        dataframe = get_all_operators()
    except Exception:
        st.error("Não foi possível carregar as operadoras.")
        return

    ids, labels = _options(dataframe, ("nome_curto", "nome", "codigo"))
    mode = st.radio(
        "Ação da operadora",
        ["Editar operadora existente", "Cadastrar nova operadora"],
        horizontal=True,
        key="admin_operator_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar operadora existente":
        if not ids:
            st.info("Nenhuma operadora cadastrada.")
            return
        record_id = st.selectbox(
            "Operadora",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_operator_selected",
        )
        current = _row_by_id(dataframe, record_id)

    with st.form("admin_operator_form"):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("Código", value=_safe(current.get("codigo")))
            name = st.text_input("Nome da operadora *", value=_safe(current.get("nome")))
            short_name = st.text_input("Nome curto", value=_safe(current.get("nome_curto")))
            status = st.selectbox(
                "Status",
                ["Ativo", "Inativo"],
                index=0 if _safe(current.get("status")) != "Inativo" else 1,
            )
        with col2:
            site_url = st.text_input("Site institucional", value=_safe(current.get("site_url")), placeholder="https://...")
            logo_url = st.text_input("URL da logo", value=_safe(current.get("logo_url")), placeholder="https://...")

        observations = st.text_area(
            "Observações",
            value=_safe(current.get("observacoes")),
            height=100,
        )
        submitted = st.form_submit_button(
            "Salvar operadora",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            save_operator(
                operator_id=record_id or None,
                code=code,
                name=name,
                short_name=short_name,
                site_url=site_url,
                logo_url=logo_url,
                observations=observations,
                status=status,
            )
            st.success("Operadora salva com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar a operadora.")


def _render_plan_management() -> None:
    st.markdown("### Planos")
    st.caption("Mantenha os planos vinculados às operadoras e aos locais de atendimento.")

    try:
        plans = get_all_plans()
        operators = get_all_operators()
        locations = get_all_locations()
    except Exception:
        st.error("Não foi possível carregar os dados necessários para administrar os planos.")
        return

    plan_ids, plan_labels = _options(plans, ("nome_padronizado", "nome", "codigo"))
    operator_ids, operator_labels = _options(operators, ("nome_curto", "nome"))
    location_ids, location_labels = _options(locations, ("nome", "codigo"))

    mode = st.radio(
        "Ação do plano",
        ["Editar plano existente", "Cadastrar novo plano"],
        horizontal=True,
        key="admin_plan_mode",
    )

    record_id = ""
    current: dict = {}
    selected_locations: list[str] = []
    if mode == "Editar plano existente":
        if not plan_ids:
            st.info("Nenhum plano cadastrado.")
            return
        record_id = st.selectbox(
            "Plano",
            plan_ids,
            format_func=lambda item: plan_labels.get(item, item),
            key="admin_plan_selected",
        )
        current = _row_by_id(plans, record_id)
        try:
            selected_locations = get_plan_location_ids(record_id)
        except Exception:
            selected_locations = []

    with st.form("admin_plan_form"):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("Código", value=_safe(current.get("codigo")))
            name = st.text_input("Nome do plano *", value=_safe(current.get("nome")))
            standardized_name = st.text_input(
                "Nome padronizado",
                value=_safe(current.get("nome_padronizado")),
            )
            plan_type = st.text_input(
                "Tipo do plano",
                value=_safe(current.get("tipo_plano")),
                placeholder="Ex.: Empresarial, Individual, Associado",
            )

        with col2:
            operator_id = st.selectbox(
                "Operadora *",
                operator_ids,
                index=_index(operator_ids, current.get("operadora_id")),
                format_func=lambda item: operator_labels.get(item, item),
            ) if operator_ids else ""
            status = st.selectbox(
                "Status",
                ["Ativo", "Inativo"],
                index=0 if _safe(current.get("status")) != "Inativo" else 1,
            )
            linked_locations = st.multiselect(
                "Locais de atendimento",
                options=location_ids,
                default=[
                    item for item in selected_locations
                    if item in location_ids
                ],
                format_func=lambda item: location_labels.get(item, item),
            )

        summary = st.text_area(
            "Observação resumida",
            value=_safe(current.get("observacao_resumida")),
            height=100,
        )

        submitted = st.form_submit_button(
            "Salvar plano",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            save_plan(
                plan_id=record_id or None,
                code=code,
                operator_id=operator_id,
                name=name,
                standardized_name=standardized_name,
                plan_type=plan_type,
                summary=summary,
                status=status,
                location_ids=linked_locations,
            )
            st.success("Plano salvo com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar o plano.")


def _render_location_management() -> None:
    st.markdown("### Locais de atendimento")
    st.caption("Cadastre os locais usados para contextualizar regras e planos.")

    try:
        dataframe = get_all_locations()
    except Exception:
        st.error("Não foi possível carregar os locais de atendimento.")
        return

    ids, labels = _options(dataframe, ("nome", "codigo"))
    mode = st.radio(
        "Ação do local",
        ["Editar local existente", "Cadastrar novo local"],
        horizontal=True,
        key="admin_location_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar local existente":
        if not ids:
            st.info("Nenhum local cadastrado.")
            return
        record_id = st.selectbox(
            "Local",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_location_selected",
        )
        current = _row_by_id(dataframe, record_id)

    with st.form("admin_location_form"):
        code = st.text_input("Código", value=_safe(current.get("codigo")))
        name = st.text_input("Nome do local *", value=_safe(current.get("nome")))
        status = st.selectbox(
            "Status",
            ["Ativo", "Inativo"],
            index=0 if _safe(current.get("status")) != "Inativo" else 1,
        )
        submitted = st.form_submit_button(
            "Salvar local",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            save_location(
                location_id=record_id or None,
                code=code,
                name=name,
                status=status,
            )
            st.success("Local salvo com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar o local.")


def _render_attendance_type_management() -> None:
    st.markdown("### Tipos de atendimento")
    st.caption("Mantenha os tipos utilizados nas regras de elegibilidade, autorização, cobertura e documentação.")

    try:
        dataframe = get_all_attendance_types()
    except Exception:
        st.error("Não foi possível carregar os tipos de atendimento.")
        return

    ids, labels = _options(dataframe, ("nome", "codigo"))
    mode = st.radio(
        "Ação do tipo",
        ["Editar tipo existente", "Cadastrar novo tipo"],
        horizontal=True,
        key="admin_attendance_type_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar tipo existente":
        if not ids:
            st.info("Nenhum tipo de atendimento cadastrado.")
            return
        record_id = st.selectbox(
            "Tipo de atendimento",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_attendance_type_selected",
        )
        current = _row_by_id(dataframe, record_id)

    with st.form("admin_attendance_type_form"):
        code = st.text_input("Código", value=_safe(current.get("codigo")))
        name = st.text_input("Nome do tipo *", value=_safe(current.get("nome")))
        status = st.selectbox(
            "Status",
            ["Ativo", "Inativo"],
            index=0 if _safe(current.get("status")) != "Inativo" else 1,
        )
        submitted = st.form_submit_button(
            "Salvar tipo de atendimento",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            save_attendance_type(
                attendance_type_id=record_id or None,
                code=code,
                name=name,
                status=status,
            )
            st.success("Tipo de atendimento salvo com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar o tipo de atendimento.")


def _render_master_data_backoffice() -> None:
    st.markdown("## Cadastros-base")
    st.info(
        "Estes cadastros estruturam todo o restante do Portal Comercial. "
        "Registros em uso devem ser inativados, e não excluídos.",
        icon="🧩",
    )

    tab_operators, tab_plans, tab_locations, tab_types = st.tabs([
        "🏥 Operadoras",
        "📋 Planos",
        "📍 Locais",
        "🩺 Tipos de atendimento",
    ])

    with tab_operators:
        _render_operator_management()
    with tab_plans:
        _render_plan_management()
    with tab_locations:
        _render_location_management()
    with tab_types:
        _render_attendance_type_management()


def _rule_context_data() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame,
    list[str], dict[str, str], list[str], dict[str, str],
    list[str], dict[str, str], list[str], dict[str, str],
]:
    operators = get_all_operators()
    plans = get_all_plans()
    locations = get_all_locations()
    attendance_types = get_all_attendance_types()

    operator_ids, operator_labels = _options(operators, ("nome_curto", "nome"))

    plan_ids: list[str] = []
    plan_labels: dict[str, str] = {}
    operator_names = {
        _safe(row.get("id")): (_safe(row.get("nome_curto")) or _safe(row.get("nome")))
        for _, row in operators.iterrows()
    }
    for _, row in plans.iterrows():
        plan_id = _safe(row.get("id"))
        if not plan_id:
            continue
        plan_name = _safe(row.get("nome_padronizado")) or _safe(row.get("nome")) or plan_id
        operator_name = operator_names.get(_safe(row.get("operadora_id")), "")
        plan_ids.append(plan_id)
        plan_labels[plan_id] = f"{operator_name} · {plan_name}" if operator_name else plan_name

    location_ids, location_labels = _options(locations, ("nome", "codigo"))
    attendance_ids, attendance_labels = _options(attendance_types, ("nome", "codigo"))

    return (
        operators, plans, locations, attendance_types,
        operator_ids, operator_labels, plan_ids, plan_labels,
        location_ids, location_labels, attendance_ids, attendance_labels,
    )


def _rule_common_selects(
    *,
    current: dict,
    operator_ids: list[str],
    operator_labels: dict[str, str],
    plan_ids: list[str],
    plan_labels: dict[str, str],
    location_ids: list[str],
    location_labels: dict[str, str],
    attendance_ids: list[str],
    attendance_labels: dict[str, str],
) -> tuple[str, str | None, str | None, str | None, str]:
    col1, col2 = st.columns(2)
    with col1:
        operator_id = st.selectbox(
            "Operadora *",
            operator_ids,
            index=_index(operator_ids, current.get("operadora_id")),
            format_func=lambda item: operator_labels.get(item, item),
        ) if operator_ids else ""

        plan_options: list[str | None] = [None] + plan_ids
        plan_id = st.selectbox(
            "Plano",
            plan_options,
            index=_index(plan_options, current.get("plano_id")),
            format_func=lambda item: "Todos / regra geral" if item is None else plan_labels.get(str(item), str(item)),
        )

    with col2:
        location_options: list[str | None] = [None] + location_ids
        location_id = st.selectbox(
            "Local de atendimento",
            location_options,
            index=_index(location_options, current.get("local_id")),
            format_func=lambda item: "Todos / não específico" if item is None else location_labels.get(str(item), str(item)),
        )

        attendance_options: list[str | None] = [None] + attendance_ids
        attendance_type_id = st.selectbox(
            "Tipo de atendimento",
            attendance_options,
            index=_index(attendance_options, current.get("tipo_atendimento_id")),
            format_func=lambda item: "Todos / não específico" if item is None else attendance_labels.get(str(item), str(item)),
        )

    status = st.selectbox(
        "Status",
        ["Ativo", "Inativo"],
        index=0 if _safe(current.get("status")) != "Inativo" else 1,
    )

    return operator_id, plan_id, location_id, attendance_type_id, status


def _render_eligibility_management() -> None:
    st.markdown("### Elegibilidade")
    st.caption("Defina quando a elegibilidade deve ser consultada e qual orientação deve ser seguida.")

    try:
        dataframe = get_all_eligibility()
        context = _rule_context_data()
    except Exception:
        st.error("Não foi possível carregar as regras de elegibilidade.")
        return

    ids, labels = _options(dataframe, ("codigo", "orientacao"))
    mode = st.radio(
        "Ação de elegibilidade",
        ["Editar regra existente", "Cadastrar nova regra"],
        horizontal=True,
        key="admin_eligibility_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar regra existente":
        if not ids:
            st.info("Nenhuma regra de elegibilidade cadastrada.")
            return
        record_id = st.selectbox(
            "Regra",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_eligibility_selected",
        )
        current = _row_by_id(dataframe, record_id)

    (_, _, _, _, operator_ids, operator_labels, plan_ids, plan_labels,
     location_ids, location_labels, attendance_ids, attendance_labels) = context

    with st.form("admin_eligibility_form"):
        code = st.text_input("Código", value=_safe(current.get("codigo")))
        operator_id, plan_id, location_id, attendance_type_id, status = _rule_common_selects(
            current=current,
            operator_ids=operator_ids,
            operator_labels=operator_labels,
            plan_ids=plan_ids,
            plan_labels=plan_labels,
            location_ids=location_ids,
            location_labels=location_labels,
            attendance_ids=attendance_ids,
            attendance_labels=attendance_labels,
        )
        required = st.checkbox(
            "Consulta de elegibilidade necessária",
            value=bool(current.get("necessario", False)),
        )
        guidance = st.text_area("Orientação", value=_safe(current.get("orientacao")), height=120)
        observations = st.text_area("Observações", value=_safe(current.get("observacoes")), height=90)
        submitted = st.form_submit_button("Salvar regra de elegibilidade", type="primary", use_container_width=True)

    if submitted:
        try:
            save_eligibility(
                record_id=record_id or None,
                code=code,
                operator_id=operator_id,
                plan_id=plan_id,
                location_id=location_id,
                attendance_type_id=attendance_type_id,
                required=required,
                guidance=guidance,
                observations=observations,
                status=status,
            )
            st.success("Regra de elegibilidade salva com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar a regra de elegibilidade.")


def _render_authorization_management() -> None:
    st.markdown("### Autorizações")
    st.caption("Mantenha necessidade, momento, responsável, canal e prazo de autorização.")

    try:
        dataframe = get_all_authorizations()
        context = _rule_context_data()
    except Exception:
        st.error("Não foi possível carregar as regras de autorização.")
        return

    ids, labels = _options(dataframe, ("codigo", "orientacao"))
    mode = st.radio(
        "Ação de autorização",
        ["Editar regra existente", "Cadastrar nova regra"],
        horizontal=True,
        key="admin_authorization_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar regra existente":
        if not ids:
            st.info("Nenhuma regra de autorização cadastrada.")
            return
        record_id = st.selectbox(
            "Regra",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_authorization_selected",
        )
        current = _row_by_id(dataframe, record_id)

    (_, _, _, _, operator_ids, operator_labels, plan_ids, plan_labels,
     location_ids, location_labels, attendance_ids, attendance_labels) = context

    with st.form("admin_authorization_form"):
        code = st.text_input("Código", value=_safe(current.get("codigo")))
        operator_id, plan_id, location_id, attendance_type_id, status = _rule_common_selects(
            current=current,
            operator_ids=operator_ids,
            operator_labels=operator_labels,
            plan_ids=plan_ids,
            plan_labels=plan_labels,
            location_ids=location_ids,
            location_labels=location_labels,
            attendance_ids=attendance_ids,
            attendance_labels=attendance_labels,
        )
        requires_authorization = st.checkbox(
            "Necessita autorização",
            value=bool(current.get("necessita_autorizacao", False)),
        )
        col1, col2 = st.columns(2)
        with col1:
            moment = st.text_input("Momento da autorização", value=_safe(current.get("momento_autorizacao")), placeholder="Ex.: Antes do atendimento")
            requester = st.text_input("Quem solicita", value=_safe(current.get("quem_solicita")), placeholder="Ex.: Central de Autorizações")
        with col2:
            channel = st.text_input("Meio de solicitação", value=_safe(current.get("meio_solicitacao")), placeholder="Ex.: Portal da operadora")
            deadline = st.text_input("Prazo", value=_safe(current.get("prazo")), placeholder="Ex.: Até 2 dias úteis")
        guidance = st.text_area("Orientação", value=_safe(current.get("orientacao")), height=120)
        observations = st.text_area("Observações", value=_safe(current.get("observacoes")), height=90)
        submitted = st.form_submit_button("Salvar regra de autorização", type="primary", use_container_width=True)

    if submitted:
        try:
            save_authorization(
                record_id=record_id or None,
                code=code,
                operator_id=operator_id,
                plan_id=plan_id,
                location_id=location_id,
                attendance_type_id=attendance_type_id,
                requires_authorization=requires_authorization,
                authorization_moment=moment,
                requester=requester,
                request_channel=channel,
                deadline=deadline,
                guidance=guidance,
                observations=observations,
                status=status,
            )
            st.success("Regra de autorização salva com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar a regra de autorização.")


def _render_coverage_management() -> None:
    st.markdown("### Coberturas")
    st.caption("Registre cobertura, restrições, acomodação, acompanhante e demais particularidades.")

    try:
        dataframe = get_all_coverages()
        context = _rule_context_data()
    except Exception:
        st.error("Não foi possível carregar as regras de cobertura.")
        return

    ids, labels = _options(dataframe, ("codigo", "restricoes_cobertura"))
    mode = st.radio(
        "Ação de cobertura",
        ["Editar regra existente", "Cadastrar nova regra"],
        horizontal=True,
        key="admin_coverage_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar regra existente":
        if not ids:
            st.info("Nenhuma regra de cobertura cadastrada.")
            return
        record_id = st.selectbox(
            "Regra",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_coverage_selected",
        )
        current = _row_by_id(dataframe, record_id)

    (_, _, _, _, operator_ids, operator_labels, plan_ids, plan_labels,
     location_ids, location_labels, attendance_ids, attendance_labels) = context

    current_covered = current.get("coberto")
    coverage_choice = "Não informado"
    if current_covered is True:
        coverage_choice = "Sim"
    elif current_covered is False:
        coverage_choice = "Não"

    with st.form("admin_coverage_form"):
        code = st.text_input("Código", value=_safe(current.get("codigo")))
        operator_id, plan_id, location_id, attendance_type_id, status = _rule_common_selects(
            current=current,
            operator_ids=operator_ids,
            operator_labels=operator_labels,
            plan_ids=plan_ids,
            plan_labels=plan_labels,
            location_ids=location_ids,
            location_labels=location_labels,
            attendance_ids=attendance_ids,
            attendance_labels=attendance_labels,
        )
        coverage_choice = st.selectbox(
            "Possui cobertura?",
            ["Não informado", "Sim", "Não"],
            index=["Não informado", "Sim", "Não"].index(coverage_choice),
        )
        col1, col2 = st.columns(2)
        with col1:
            accommodation = st.text_input("Acomodação", value=_safe(current.get("acomodacao")), placeholder="Ex.: Apartamento")
        with col2:
            companion = st.text_input("Acompanhante", value=_safe(current.get("acompanhante")), placeholder="Ex.: Conforme regra contratual")
        restrictions = st.text_area("Restrições de cobertura", value=_safe(current.get("restricoes_cobertura")), height=110)
        observations = st.text_area("Observações", value=_safe(current.get("observacoes")), height=90)
        submitted = st.form_submit_button("Salvar regra de cobertura", type="primary", use_container_width=True)

    if submitted:
        covered = None if coverage_choice == "Não informado" else coverage_choice == "Sim"
        try:
            save_coverage(
                record_id=record_id or None,
                code=code,
                operator_id=operator_id,
                plan_id=plan_id,
                location_id=location_id,
                attendance_type_id=attendance_type_id,
                covered=covered,
                restrictions=restrictions,
                accommodation=accommodation,
                companion=companion,
                observations=observations,
                status=status,
            )
            st.success("Regra de cobertura salva com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar a regra de cobertura.")


def _render_document_management() -> None:
    st.markdown("### Documentos")
    st.caption("Cadastre a documentação exigida por operadora, plano, local ou tipo de atendimento.")

    try:
        dataframe = get_all_documents()
        context = _rule_context_data()
    except Exception:
        st.error("Não foi possível carregar os documentos.")
        return

    ids, labels = _options(dataframe, ("nome", "codigo"))
    mode = st.radio(
        "Ação de documento",
        ["Editar documento existente", "Cadastrar novo documento"],
        horizontal=True,
        key="admin_document_mode",
    )

    record_id = ""
    current: dict = {}
    if mode == "Editar documento existente":
        if not ids:
            st.info("Nenhum documento cadastrado.")
            return
        record_id = st.selectbox(
            "Documento",
            ids,
            format_func=lambda item: labels.get(item, item),
            key="admin_document_selected",
        )
        current = _row_by_id(dataframe, record_id)

    (_, _, _, _, operator_ids, operator_labels, plan_ids, plan_labels,
     location_ids, location_labels, attendance_ids, attendance_labels) = context

    validity_value = current.get("validade_dias")
    try:
        validity_value = int(validity_value) if validity_value is not None and not pd.isna(validity_value) else 0
    except (TypeError, ValueError):
        validity_value = 0

    with st.form("admin_document_form"):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("Código", value=_safe(current.get("codigo")))
            name = st.text_input("Nome do documento *", value=_safe(current.get("nome")))
        with col2:
            mandatory = st.checkbox("Documento obrigatório", value=bool(current.get("obrigatorio", False)))
            file_format = st.text_input("Formato", value=_safe(current.get("formato")), placeholder="Ex.: PDF, formulário, guia")

        operator_id, plan_id, location_id, attendance_type_id, status = _rule_common_selects(
            current=current,
            operator_ids=operator_ids,
            operator_labels=operator_labels,
            plan_ids=plan_ids,
            plan_labels=plan_labels,
            location_ids=location_ids,
            location_labels=location_labels,
            attendance_ids=attendance_ids,
            attendance_labels=attendance_labels,
        )

        validity_days = st.number_input(
            "Validade em dias (0 = não informada)",
            min_value=0,
            step=1,
            value=validity_value,
        )
        file_url = st.text_input("Link do arquivo / modelo", value=_safe(current.get("arquivo_url")), placeholder="https://...")
        guidance = st.text_area("Orientação", value=_safe(current.get("orientacao")), height=110)
        observations = st.text_area("Observações", value=_safe(current.get("observacoes")), height=90)
        submitted = st.form_submit_button("Salvar documento", type="primary", use_container_width=True)

    if submitted:
        try:
            save_document(
                record_id=record_id or None,
                code=code,
                operator_id=operator_id,
                plan_id=plan_id,
                location_id=location_id,
                attendance_type_id=attendance_type_id,
                name=name,
                mandatory=mandatory,
                file_format=file_format,
                validity_days=int(validity_days) if validity_days else None,
                guidance=guidance,
                observations=observations,
                file_url=file_url,
                status=status,
            )
            st.success("Documento salvo com sucesso.")
            st.rerun()
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("Não foi possível salvar o documento.")


def _render_rules_backoffice() -> None:
    st.markdown("## Regras de atendimento")
    st.info(
        "Centralize aqui as regras que orientam o atendimento. Elas podem ser gerais da operadora "
        "ou específicas por plano, local e tipo de atendimento.",
        icon="📚",
    )

    tab_eligibility, tab_authorizations, tab_coverages, tab_documents = st.tabs([
        "✅ Elegibilidade",
        "📝 Autorizações",
        "🛡️ Coberturas",
        "📄 Documentos",
    ])

    with tab_eligibility:
        _render_eligibility_management()
    with tab_authorizations:
        _render_authorization_management()
    with tab_coverages:
        _render_coverage_management()
    with tab_documents:
        _render_document_management()

def _render_portals_backoffice() -> None:
    st.markdown("## Portais e credenciais")
    st.info(
        "Somente administradores podem alterar estes dados. Senhas nunca são armazenadas em texto puro nem registradas nos logs de auditoria.",
        icon="🔐",
    )
    tab_portals, tab_credentials = st.tabs(["🌐 Portais", "🔐 Credenciais"])
    with tab_portals:
        _render_portal_management()
    with tab_credentials:
        _render_credential_management()


def render_admin() -> None:
    if not _is_admin():
        st.error("Esta área é restrita aos administradores do Portal Comercial.")
        return

    render_hero(
        eyebrow="Gestão do Portal",
        title="Administração",
        description="Gerencie cadastros-base, portais, credenciais, dados operacionais e usuários autorizados.",
    )

    connected, connection_message = check_supabase_connection()
    if connected:
        st.success("Supabase conectado e operacional.", icon="✅")
    else:
        st.error(connection_message, icon="❌")
        return

    if st.button("Atualizar dados agora", use_container_width=False):
        clear_data_cache()
        st.success("Cache atualizado.")
        st.rerun()

    tab_overview, tab_master, tab_rules, tab_portals, tab_data, tab_users = st.tabs([
        "📊 Visão geral",
        "🧩 Cadastros-base",
        "📚 Regras de atendimento",
        "🔐 Portais e credenciais",
        "🗃️ Dados",
        "👥 Usuários",
    ])

    with tab_overview:
        _render_overview()
    with tab_master:
        _render_master_data_backoffice()
    with tab_rules:
        _render_rules_backoffice()
    with tab_portals:
        _render_portals_backoffice()
    with tab_data:
        _render_dataset_browser()
    with tab_users:
        _render_users()
