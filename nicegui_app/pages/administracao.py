from __future__ import annotations

from collections import defaultdict

from nicegui import ui

from nicegui_app.hero_art import render_hero_art
from nicegui_app.layout import portal_layout
from nicegui_app.services.administracao_service import (
    AdminProfile,
    AuditPreview,
    get_admin_overview,
    get_admin_profiles,
    get_recent_audit_logs,
)


MODULES = (
    {
        "title": "Operadoras",
        "description": "Estrutura principal dos convênios disponíveis no portal.",
        "icon": "domain",
        "count_key": "operadoras",
        "route": "/administracao/cadastros",
        "group": "base",
        "tone": "blue",
    },
    {
        "title": "Planos",
        "description": "Planos vinculados às operadoras e suas informações de referência.",
        "icon": "health_and_safety",
        "count_key": "planos",
        "route": "/administracao/cadastros",
        "group": "base",
        "tone": "blue",
    },
    {
        "title": "Portais",
        "description": "Portais externos, instruções de acesso e vínculos operacionais.",
        "icon": "language",
        "count_key": "portais",
        "route": "/administracao/portais",
        "group": "base",
        "tone": "cyan",
    },
    {
        "title": "Documentos",
        "description": "Documentos e orientações utilizados no atendimento.",
        "icon": "description",
        "count_key": "documentos",
        "route": "/administracao/documentos",
        "group": "base",
        "tone": "cyan",
    },
    {
        "title": "Contatos",
        "description": "Centrais, setores, responsáveis e canais de atendimento.",
        "icon": "contacts",
        "count_key": "contatos",
        "route": "/administracao/contatos",
        "group": "relationship",
        "tone": "teal",
    },
    {
        "title": "Consultores",
        "description": "Consultores e carteiras de relacionamento.",
        "icon": "support_agent",
        "count_key": "consultores",
        "route": "/administracao/consultores",
        "group": "relationship",
        "tone": "indigo",
    },
    {
        "title": "Comunicados",
        "description": "Comunicados institucionais e orientações temporárias.",
        "icon": "campaign",
        "count_key": "comunicados",
        "route": "/administracao/comunicados",
        "group": "relationship",
        "tone": "violet",
    },
    {
        "title": "Contingências",
        "description": "Incidentes, fluxos alternativos e períodos de contingência.",
        "icon": "warning_amber",
        "count_key": "contingencias",
        "route": "/administracao/contingencias",
        "group": "relationship",
        "tone": "amber",
    },
    {
        "title": "Credenciais",
        "description": "Logins, senhas criptografadas e histórico protegido dos portais.",
        "icon": "shield_lock",
        "count_key": "portal_credenciais",
        "route": "/administracao/credenciais",
        "group": "governance",
        "tone": "slate",
    },
)

GROUPS = (
    {
        "key": "base",
        "kicker": "BASE OPERACIONAL",
        "title": "Estrutura do Portal",
        "description": "Cadastros que sustentam a consulta diária dos colaboradores.",
        "icon": "account_tree",
    },
    {
        "key": "relationship",
        "kicker": "RELACIONAMENTO E CONTEÚDO",
        "title": "Informação que chega à operação",
        "description": "Pessoas, orientações e situações que precisam estar sempre atualizadas.",
        "icon": "hub",
    },
    {
        "key": "governance",
        "kicker": "SEGURANÇA E GOVERNANÇA",
        "title": "Acessos protegidos",
        "description": "Credenciais institucionais com controle, histórico e rastreabilidade.",
        "icon": "verified_user",
    },
)


def _module_card(module: dict, count: int) -> None:
    with ui.element("article").classes(
        f"portal-admin-module-card portal-admin-module-card--{module['tone']}"
    ):
        with ui.row().classes("portal-admin-module-head"):
            with ui.element("div").classes("portal-admin-module-icon"):
                ui.icon(module["icon"])

            with ui.element("div").classes("portal-admin-module-counter"):
                ui.label(str(count)).classes("portal-admin-module-count")
                ui.label("registros").classes("portal-admin-module-count-label")

        ui.label(module["title"]).classes("portal-admin-module-title")
        ui.label(module["description"]).classes("portal-admin-module-description")

        with ui.row().classes("portal-admin-module-footer"):
            ui.label("Gerenciar módulo").classes("portal-admin-module-action-label")
            ui.icon("arrow_forward").classes("portal-admin-module-arrow")

        ui.element("button").classes("portal-admin-module-hitarea").props(
            f'aria-label="Abrir {module["title"]}"'
        ).on("click", lambda route=module["route"]: ui.navigate.to(route))


def _profile_row(profile: AdminProfile) -> None:
    role_label = "Administrador" if profile.role.lower() == "admin" else "Usuário"

    with ui.element("div").classes("portal-admin-user-row"):
        with ui.element("div").classes("portal-admin-user-avatar"):
            parts = [p for p in profile.name.split() if p]
            initials = "".join(p[0] for p in parts[:2]).upper() if parts else "HM"
            ui.label(initials)

        with ui.column().classes("portal-admin-user-copy"):
            ui.label(profile.name).classes("portal-admin-user-name")
            ui.label(profile.email).classes("portal-admin-user-email")

        with ui.element("div").classes(
            f"portal-admin-role {'is-admin' if profile.role.lower() == 'admin' else ''}"
        ):
            ui.label(role_label)

        with ui.element("div").classes(
            f"portal-admin-status {'is-active' if profile.status.lower() == 'ativo' else ''}"
        ):
            ui.element("span").classes("portal-admin-status-dot")
            ui.label(profile.status)


def _audit_row(log: AuditPreview) -> None:
    with ui.element("div").classes("portal-admin-audit-row"):
        with ui.element("div").classes("portal-admin-audit-icon"):
            ui.icon("history")

        with ui.column().classes("portal-admin-audit-copy"):
            ui.label(log.action).classes("portal-admin-audit-action")
            ui.label(f"{log.entity} · {log.actor}").classes("portal-admin-audit-meta")

            if log.detail:
                ui.label(log.detail).classes("portal-admin-audit-detail")

        if log.created_at:
            ui.label(log.created_at).classes("portal-admin-audit-date")


def _hero_stat(icon: str, value: int, label: str) -> None:
    with ui.element("div").classes("portal-admin-hero-stat"):
        with ui.element("div").classes("portal-admin-hero-stat-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-admin-hero-stat-copy"):
            ui.label(str(value)).classes("portal-admin-hero-stat-value")
            ui.label(label).classes("portal-admin-hero-stat-label")


def render_administracao(user: dict) -> None:
    overview = get_admin_overview()
    profiles = get_admin_profiles()
    logs = get_recent_audit_logs()

    active_profiles = sum(1 for profile in profiles if profile.status.lower() == "ativo")
    admin_profiles = sum(1 for profile in profiles if profile.role.lower() == "admin")
    total_records = sum(overview.get(module["count_key"], 0) for module in MODULES)

    grouped_modules: dict[str, list[dict]] = defaultdict(list)
    for module in MODULES:
        grouped_modules[module["group"]].append(module)

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="GESTÃO DO PORTAL",
        page_title="Central de Administração",
        page_description=(
            "Cadastros, acessos, segurança e rastreabilidade em um único ambiente."
        ),
    ):
        with ui.element("section").classes("portal-admin-hero"):
            render_hero_art(variant="admin", icon="admin_panel_settings")

            with ui.column().classes("portal-admin-hero-copy"):
                ui.label("AMBIENTE ADMINISTRATIVO").classes("portal-admin-hero-kicker")
                ui.label("O centro de comando do Portal Comercial.").classes(
                    "portal-admin-hero-title"
                )
                ui.label(
                    "Mantenha a base confiável, acompanhe acessos e preserve a segurança "
                    "das informações que sustentam a operação comercial."
                ).classes("portal-admin-hero-description")

                with ui.row().classes("portal-admin-hero-actions"):
                    ui.button(
                        "Gerenciar usuários",
                        icon="manage_accounts",
                        on_click=lambda: ui.navigate.to("/administracao/usuarios"),
                    ).props("unelevated no-caps").classes("portal-admin-hero-primary")
                    ui.button(
                        "Ver auditoria",
                        icon="manage_history",
                        on_click=lambda: ui.navigate.to("/administracao/auditoria"),
                    ).props("flat no-caps").classes("portal-admin-hero-secondary")

            with ui.element("div").classes("portal-admin-hero-side"):
                _hero_stat("dataset", total_records, "Registros gerenciados")
                _hero_stat("group", active_profiles, "Usuários ativos")
                _hero_stat("shield_person", admin_profiles, "Administradores")
                _hero_stat(
                    "key",
                    overview.get("portal_credenciais", 0),
                    "Credenciais protegidas",
                )

        with ui.row().classes("portal-admin-command-strip"):
            with ui.row().classes("portal-admin-command-copy"):
                with ui.element("div").classes("portal-admin-command-icon"):
                    ui.icon("verified")
                with ui.column().classes("portal-admin-command-text"):
                    ui.label("Administração protegida").classes("portal-admin-command-title")
                    ui.label(
                        "Alterações administrativas permanecem sujeitas às regras de autorização e auditoria do portal."
                    ).classes("portal-admin-command-description")
            ui.label("AMBIENTE CONTROLADO").classes("portal-admin-command-badge")

        for group in GROUPS:
            modules = grouped_modules.get(group["key"], [])
            if not modules:
                continue

            with ui.row().classes("portal-admin-section-heading"):
                with ui.row().classes("portal-admin-section-heading-main"):
                    with ui.element("div").classes("portal-admin-section-icon"):
                        ui.icon(group["icon"])
                    with ui.column().classes("portal-admin-section-copy"):
                        ui.label(group["kicker"]).classes("portal-section-kicker")
                        ui.label(group["title"]).classes("portal-admin-section-title")
                        ui.label(group["description"]).classes("portal-admin-section-hint")

            with ui.element("section").classes(
                f"portal-admin-modules-grid portal-admin-modules-grid--{group['key']}"
            ):
                for module in modules:
                    _module_card(module, overview.get(module["count_key"], 0))

        with ui.row().classes("portal-admin-management-grid"):
            with ui.element("section").classes("portal-admin-panel"):
                with ui.row().classes("portal-admin-panel-head"):
                    with ui.column().classes("portal-admin-panel-title-copy"):
                        ui.label("ACESSOS").classes("portal-section-kicker")
                        ui.label("Usuários do Portal").classes("portal-admin-panel-title")
                        ui.label(
                            "Quem possui acesso e qual o nível de permissão atual."
                        ).classes("portal-admin-panel-subtitle")
                    with ui.row().classes("items-center q-gutter-sm"):
                        with ui.element("div").classes("portal-admin-panel-badge"):
                            ui.label(str(len(profiles)))
                        ui.button(
                            "Gerenciar",
                            icon="manage_accounts",
                            on_click=lambda: ui.navigate.to("/administracao/usuarios"),
                        ).props("flat no-caps").classes("portal-admin-users-manage-button")

                if profiles:
                    with ui.column().classes("portal-admin-users-list"):
                        for profile in profiles[:8]:
                            _profile_row(profile)
                else:
                    ui.label("Nenhum perfil foi localizado.").classes(
                        "portal-admin-panel-empty"
                    )

            with ui.element("section").classes("portal-admin-panel"):
                with ui.row().classes("portal-admin-panel-head"):
                    with ui.column().classes("portal-admin-panel-title-copy"):
                        ui.label("RASTREABILIDADE").classes("portal-section-kicker")
                        ui.label("Atividade recente").classes("portal-admin-panel-title")
                        ui.label(
                            "Últimas ações registradas na trilha administrativa."
                        ).classes("portal-admin-panel-subtitle")
                    ui.button(
                        "Ver auditoria",
                        icon="manage_history",
                        on_click=lambda: ui.navigate.to("/administracao/auditoria"),
                    ).props("flat no-caps").classes("portal-admin-users-manage-button")

                if logs:
                    with ui.column().classes("portal-admin-audit-list"):
                        for log in logs:
                            _audit_row(log)
                else:
                    with ui.element("div").classes("portal-admin-audit-empty"):
                        ui.icon("history_toggle_off")
                        ui.label("Ainda não há atividades recentes para exibir.").classes(
                            "portal-admin-panel-empty"
                        )

        with ui.element("section").classes("portal-admin-security-card"):
            with ui.element("div").classes("portal-admin-security-icon"):
                ui.icon("encrypted")
            with ui.column().classes("portal-admin-security-copy"):
                ui.label("CREDENCIAIS E SEGURANÇA").classes("portal-section-kicker")
                ui.label("Proteção incorporada ao fluxo administrativo").classes(
                    "portal-admin-security-title"
                )
                ui.label(
                    "Senhas permanecem criptografadas, revelações são auditadas e o histórico "
                    "de alterações é preservado. A Central de Administração não expõe "
                    "credenciais em texto aberto."
                ).classes("portal-admin-security-description")
            with ui.column().classes("portal-admin-security-actions"):
                with ui.element("div").classes("portal-admin-security-count"):
                    ui.label(str(overview.get("portal_credenciais", 0))).classes(
                        "portal-admin-security-count-value"
                    )
                    ui.label("credenciais cadastradas").classes(
                        "portal-admin-security-count-label"
                    )
                ui.button(
                    "Gerenciar credenciais",
                    icon="arrow_forward",
                    on_click=lambda: ui.navigate.to("/administracao/credenciais"),
                ).props("flat no-caps").classes("portal-admin-security-button")
