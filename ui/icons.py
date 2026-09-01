from __future__ import annotations


_ICONS = {
    "home": '<path d="M3 10.8 12 3l9 7.8v9.2a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 5 5"/>',
    "building": '<path d="M4 21V5l8-3v19M12 8h8v13M8 7v2M8 12v2M8 17v2M16 11v2M16 16v2"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>',
    "file": '<path d="M6 2h8l4 4v16H6zM14 2v5h5M9 12h6M9 16h6"/>',
    "phone": '<path d="M7 3 4 5.5c.5 7 7 13.5 14 14l2.5-3-4-3-2 2c-2.5-1-5-3.5-6-6l2-2z"/>',
    "users": '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20c0-4 2.5-6 6-6s6 2 6 6M14 15c4 0 7 1.5 7 5"/>',
    "megaphone": '<path d="M3 11v4h4l8 4V7l-8 4zM15 10l5-2v10l-5-2M7 15l1 5h3l-1-4"/>',
    "warning": '<path d="M12 3 2.8 20h18.4zM12 9v5M12 17.5h.01"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.86 2.86-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.1A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.86-2.86.06-.06A1.7 1.7 0 0 0 4.2 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H2.4v-4h.1A1.7 1.7 0 0 0 4.2 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06L6.66 3.8l.06.06A1.7 1.7 0 0 0 8.6 4.2a1.7 1.7 0 0 0 1-.6A1.7 1.7 0 0 0 10 2.5v-.1h4v.1a1.7 1.7 0 0 0 1 1.7 1.7 1.7 0 0 0 1.88-.34l.06-.06 2.86 2.86-.06.06A1.7 1.7 0 0 0 19.4 8.6a1.7 1.7 0 0 0 .6 1 1.7 1.7 0 0 0 1.1.4h.1v4h-.1a1.7 1.7 0 0 0-1.7 1z"/>',
    "clipboard": '<path d="M8 4h8M9 2h6v4H9zM6 4H4v18h16V4h-2M8 11h8M8 15h8"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "key": '<circle cx="8" cy="12" r="4"/><path d="M12 12h9M18 12v3M15 12v2"/>',
    "shield": '<path d="M12 3 20 6v5c0 5-3 8-8 10-5-2-8-5-8-10V6z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-5 3-8 8-8s8 3 8 8"/>',
    "lightbulb": '<path d="M9 18h6M10 21h4M8 14c-1.5-1.2-2-3-2-5a6 6 0 1 1 12 0c0 2-.5 3.8-2 5-1 .8-1 1.7-1 2H9c0-.3 0-1.2-1-2z"/>',
}

CATEGORY_ICON_NAMES = {
    "Operadoras": "building",
    "Planos": "clipboard",
    "Portais": "globe",
    "Elegibilidade": "check",
    "Documentos": "file",
    "Autorizações": "key",
    "Coberturas": "shield",
    "Contatos": "phone",
    "Consultores": "user",
    "Comunicados": "megaphone",
    "Contingências": "warning",
    "Dicas operacionais": "lightbulb",
}


def icon(name: str, *, css_class: str = "", title: str | None = None) -> str:
    """Retorna um ícone do design system sem SVG inline.

    Os desenhos vivem em styles/components/icons.css como máscaras CSS.
    Isso evita a sanitização de SVG inline pelo HTML do Streamlit e mantém
    todos os ícones centralizados em uma única biblioteca visual.
    """

    resolved = name if name in _ICONS else "search"
    classes = "portal-icon portal-icon-" + resolved
    if css_class:
        classes += " " + css_class.strip()

    if title:
        import html as _html
        safe_title = _html.escape(title, quote=True)
        return f'<span class="{classes}" role="img" aria-label="{safe_title}" title="{safe_title}"></span>'

    return f'<span class="{classes}" aria-hidden="true"></span>'


def category_icon(category: str) -> str:
    return icon(CATEGORY_ICON_NAMES.get(category, "search"))
