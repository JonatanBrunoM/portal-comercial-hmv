from __future__ import annotations
from datetime import date
from nicegui import ui
from nicegui_app.layout import portal_layout
from nicegui_app.services.comunicados_service import ComunicadoPreview, get_comunicado_detail, get_comunicados_preview

def _norm(v:str)->str: return " ".join(v.lower().strip().split())
def _date(v:date|None)->str: return v.strftime("%d/%m/%Y") if v else ""
def _period(c:ComunicadoPreview)->str:
    a,b=_date(c.start_date),_date(c.end_date)
    return f"{a} a {b}" if a and b else f"A partir de {a}" if a else f"Até {b}" if b else "Sem período definido"

def _card(c:ComunicadoPreview):
    with ui.element("article").classes("portal-communication-card" + (" is-featured" if c.featured else "")):
        with ui.row().classes("portal-communication-head"):
            ui.icon("campaign").classes("portal-communication-icon")
            if c.featured: ui.label("★ DESTAQUE").classes("portal-communication-featured")
        if c.category: ui.label(c.category.upper()).classes("portal-communication-category")
        ui.label(c.title).classes("portal-communication-title")
        ui.label(c.operator_name).classes("portal-communication-operator")
        ui.label(c.summary or c.content or "Consulte o comunicado completo.").classes("portal-communication-summary")
        with ui.row().classes("portal-communication-meta"):
            ui.icon("calendar_month"); ui.label(_period(c))
        if c.audience:
            with ui.row().classes("portal-communication-meta"):
                ui.icon("groups"); ui.label(c.audience)
        with ui.row().classes("portal-communication-actions"):
            ui.label(c.priority).classes("portal-communication-priority")
            ui.button("Ler comunicado", icon="arrow_forward",
                on_click=lambda cid=c.communication_id: ui.navigate.to(f"/comunicados/{cid}")
            ).props("flat no-caps").classes("portal-communication-button")

def render_comunicados(user:dict):
    items=get_comunicados_preview()
    with portal_layout(user=user,active="communications",page_eyebrow="CENTRAL DE COMUNICADOS",
        page_title="O que mudou e o que precisa da sua atenção.",
        page_description="Acompanhe orientações, mudanças operacionais e avisos importantes das operadoras em um único lugar."):
        ops=sorted({c.operator_name for c in items}); cats=sorted({c.category for c in items if c.category})
        with ui.element("section").classes("portal-communications-summary"):
            with ui.column():
                ui.label("INFORMAÇÃO OPERACIONAL").classes("portal-section-kicker")
                ui.label(f"{len(items):02d} comunicados cadastrados").classes("portal-communications-summary-value")
                ui.label("Avisos organizados por prioridade, vigência e público.").classes("portal-communications-summary-description")
            with ui.row().classes("portal-communications-stats"):
                for value,label in ((sum(c.featured for c in items),"Destaques"),(sum(c.period_active for c in items),"Vigentes")):
                    with ui.column().classes("portal-communications-stat"):
                        ui.label(str(value).zfill(2)).classes("portal-communications-stat-value"); ui.label(label)

        featured=[c for c in items if c.featured and c.period_active]
        if featured:
            ui.label("EM DESTAQUE").classes("portal-section-kicker portal-communications-featured-heading")
            with ui.element("div").classes("portal-communications-grid"):
                for c in featured[:3]: _card(c)

        with ui.element("section").classes("portal-communications-toolbar"):
            search=ui.input(placeholder="Buscar título, operadora, categoria ou conteúdo").props("outlined dense clearable prepend-icon=search").classes("portal-communications-search")
            op=ui.select(["Todas"]+ops,value="Todas",label="Operadora").props("outlined dense").classes("portal-communications-filter")
            cat=ui.select(["Todas"]+cats,value="Todas",label="Categoria").props("outlined dense").classes("portal-communications-filter")
            period=ui.select(["Todos","Vigentes","Fora da vigência"],value="Todos",label="Período").props("outlined dense").classes("portal-communications-filter")
        count=ui.label("").classes("portal-communications-count"); grid=ui.element("div").classes("portal-communications-grid")
        def refresh():
            term=_norm(search.value or ""); filtered=[]
            for c in items:
                hay=_norm(" ".join((c.title,c.summary,c.content,c.operator_name,c.category,c.priority,c.audience,c.responsible)))
                okop=op.value=="Todas" or c.operator_name==op.value
                okcat=cat.value=="Todas" or c.category==cat.value
                okperiod=period.value=="Todos" or (period.value=="Vigentes" and c.period_active) or (period.value=="Fora da vigência" and not c.period_active)
                if (not term or term in hay) and okop and okcat and okperiod: filtered.append(c)
            count.set_text(f"{len(filtered)} comunicado(s) encontrado(s)"); grid.clear()
            with grid:
                if not filtered:
                    with ui.element("div").classes("portal-communications-empty"):
                        ui.icon("campaign"); ui.label("Nenhum comunicado encontrado.")
                for c in filtered: _card(c)
        for control in (search,op,cat,period): control.on_value_change(lambda _:refresh())
        refresh()

def _detail(icon,label,value):
    if value:
        with ui.element("div").classes("portal-communication-detail-item"):
            ui.icon(icon)
            with ui.column():
                ui.label(label).classes("portal-communication-detail-label")
                ui.label(value).classes("portal-communication-detail-value")

def render_comunicado_detail(user:dict,communication_id:str):
    c=get_comunicado_detail(communication_id)
    with portal_layout(user=user,active="communications"):
        if not c:
            ui.label("Comunicado não encontrado."); return
        ui.button("Voltar para Comunicados",icon="arrow_back",on_click=lambda:ui.navigate.to("/comunicados")).props("flat no-caps")
        with ui.element("section").classes("portal-communication-detail-hero"):
            ui.icon("campaign").classes("portal-communication-detail-icon")
            with ui.column():
                ui.label((c.category or "COMUNICADO").upper()).classes("portal-section-kicker")
                ui.label(c.title).classes("portal-communication-detail-title")
                ui.label(c.operator_name).classes("portal-communication-operator")
        with ui.element("section").classes("portal-communication-detail-grid"):
            _detail("business","Operadora",c.operator_name); _detail("calendar_month","Vigência",_period(c))
            _detail("groups","Público-alvo",c.audience); _detail("person","Responsável",c.responsible)
            _detail("priority_high","Prioridade",c.priority); _detail("fact_check","Status",c.status)
        if c.summary:
            with ui.element("section").classes("portal-communication-content-card"):
                ui.label("RESUMO").classes("portal-section-kicker"); ui.label(c.summary).classes("portal-communication-detail-summary")
        with ui.element("section").classes("portal-communication-content-card"):
            ui.label("COMUNICADO COMPLETO").classes("portal-section-kicker")
            ui.label(c.content or "Nenhum conteúdo detalhado foi informado.").classes("portal-communication-content")
