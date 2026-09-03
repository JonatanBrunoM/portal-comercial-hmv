from __future__ import annotations

from nicegui import ui

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
    },
    {
        "title": "Planos",
        "description": "Planos vinculados às operadoras e suas informações de referência.",
        "icon": "health_and_safety",
        "count_key": "planos",
        "route": "/administracao/cadastros",
    },
    {
        "title": "Portais",
        "description": "Portais externos, instruções de acesso e vínculos operacionais.",
        "icon": "vpn_key",
        "count_key": "portais",
        "route": "/administracao/portais",
    },
    {
        "title": "Credenciais",
        "description": "Logins, senhas criptografadas e histórico protegido dos portais.",
        "icon": "shield_lock",
        "count_key": "portal_credenciais",
        "route": "/administracao/credenciais",
    },
    {
        "title": "Documentos",
        "description": "Documentos e orientações utilizados no atendimento.",
        "icon": "description",
        "count_key": "documentos",
        "route": "/administracao/documentos",
    },
    {
        "title": "Contatos",
        "description": "Centrais, setores, responsáveis e canais de atendimento.",
        "icon": "contacts",
        "count_key": "contatos",
        "route": "/administracao/contatos",
    },
    {
        "title": "Consultores",
        "description": "Consultores e carteiras de relacionamento.",
        "icon": "support_agent",
        "count_key": "consultores",
        "route": "/administracao/consultores",
    },
    {
        "title": "Comunicados",
        "description": "Comunicados institucionais e orientações temporárias.",
        "icon": "campaign",
        "count_key": "comunicados",
        "route": "/administracao/comunicados",
    },
    {
        "title": "Contingências",
        "description": "Incidentes, fluxos alternativos e períodos de contingência.",
        "icon": "warning_amber",
        "count_key": "contingencias",
        "route": "/administracao/contingencias",
    },
)


def _module_card(module: dict, count: int) -> None:
    with ui.element("article").classes("portal-admin-module-card"):
        with ui.row().classes("portal-admin-module-head"):
            with ui.element("div").classes("portal-admin-module-icon"):
                ui.icon(module["icon"])

            ui.label(str(count).zfill(2)).classes("portal-admin-module-count")

        ui.label(module["title"]).classes("portal-admin-module-title")
        ui.label(module["description"]).classes("portal-admin-module-description")

        ui.button(
            "Abrir módulo",
            icon="arrow_forward",
            on_click=lambda route=module["route"]: ui.navigate.to(route),
        ).props("flat no-caps").classes("portal-admin-module-button")


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
            ui.label(
                f"{log.entity} · {log.actor}"
            ).classes("portal-admin-audit-meta")

            if log.detail:
                ui.label(log.detail).classes("portal-admin-audit-detail")

        if log.created_at:
            ui.label(log.created_at).classes("portal-admin-audit-date")


def render_administracao(user: dict) -> None:
    overview = get_admin_overview()
    profiles = get_admin_profiles()
    logs = get_recent_audit_logs()

    active_profiles = sum(1 for profile in profiles if profile.status.lower() == "ativo")
    admin_profiles = sum(1 for profile in profiles if profile.role.lower() == "admin")

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="GESTÃO DO PORTAL",
        page_title="Central de Administração",
        page_description=(
            "Visão consolidada dos cadastros, acessos e estruturas que sustentam "
            "o Portal Comercial."
        ),
    ):
        with ui.element("section").classes("portal-admin-overview"):
            with ui.column().classes("portal-admin-overview-copy"):
                ui.label("AMBIENTE ADMINISTRATIVO").classes("portal-section-kicker")
                ui.label("Controle central, sem perder a simplicidade.").classes(
                    "portal-admin-overview-title"
                )
                ui.label(
                    "Acompanhe a base, usuários e mudanças do portal a partir de um único ponto."
                ).classes("portal-admin-overview-description")

            with ui.row().classes("portal-admin-overview-stats"):
                for value, label in (
                    (sum(overview.get(module["count_key"], 0) for module in MODULES), "Registros principais"),
                    (active_profiles, "Usuários ativos"),
                    (admin_profiles, "Administradores"),
                ):
                    with ui.column().classes("portal-admin-overview-stat"):
                        ui.label(str(value).zfill(2)).classes("portal-admin-overview-value")
                        ui.label(label).classes("portal-admin-overview-label")

        with ui.row().classes("portal-admin-section-heading"):
            with ui.column().classes("portal-admin-section-copy"):
                ui.label("CADASTROS").classes("portal-section-kicker")
                ui.label("Estrutura do Portal").classes("portal-admin-section-title")
            ui.label(
                "Acesso rápido aos módulos operacionais."
            ).classes("portal-admin-section-hint")

        with ui.element("section").classes("portal-admin-modules-grid"):
            for module in MODULES:
                _module_card(module, overview.get(module["count_key"], 0))

        with ui.row().classes("portal-admin-management-grid"):
            with ui.element("section").classes("portal-admin-panel"):
                with ui.row().classes("portal-admin-panel-head"):
                    with ui.column().classes("portal-admin-panel-title-copy"):
                        ui.label("ACESSOS").classes("portal-section-kicker")
                        ui.label("Usuários do Portal").classes("portal-admin-panel-title")
                    with ui.row().classes("items-center q-gutter-sm"):
                        with ui.element("div").classes("portal-admin-panel-badge"):
                            ui.label(str(len(profiles)).zfill(2))
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
                    ui.label(
                        "Nenhum perfil foi localizado."
                    ).classes("portal-admin-panel-empty")

            with ui.element("section").classes("portal-admin-panel"):
                with ui.row().classes("portal-admin-panel-head"):
                    with ui.column().classes("portal-admin-panel-title-copy"):
                        ui.label("RASTREABILIDADE").classes("portal-section-kicker")
                        ui.label("Atividade recente").classes("portal-admin-panel-title")
                    ui.icon("manage_history").classes("portal-admin-panel-head-icon")

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
                ui.icon("shield")
            with ui.column().classes("portal-admin-security-copy"):
                ui.label("CREDENCIAIS E SEGURANÇA").classes("portal-section-kicker")
                ui.label("Gestão de acessos externos").classes(
                    "portal-admin-security-title"
                )
                ui.label(
                    "A estrutura de credenciais será administrada em um módulo próprio, "
                    "com histórico, criptografia e rastreabilidade. Senhas não são "
                    "exibidas nesta central."
                ).classes("portal-admin-security-description")
            with ui.element("div").classes("portal-admin-security-count"):
                ui.label(str(overview.get("portal_credenciais", 0)).zfill(2)).classes(
                    "portal-admin-security-count-value"
                )
                ui.label("credenciais cadastradas").classes(
                    "portal-admin-security-count-label"
                )
