import streamlit as st


COLORS = {
    "primary": "#005691",
    "primary_dark": "#003D66",
    "primary_hover": "#004A7C",
    "primary_soft": "#EAF4FA",
    "primary_soft_strong": "#DDEEF8",
    "background": "#F4F7F9",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFB",
    "text": "#17212B",
    "text_strong": "#0D2638",
    "text_secondary": "#52616D",
    "text_muted": "#6B7A86",
    "border": "#D8E1E7",
    "border_strong": "#C8D4DC",
    "success": "#237A3B",
    "success_soft": "#EAF6ED",
    "warning": "#A86100",
    "warning_soft": "#FFF5E5",
    "error": "#B42318",
    "error_soft": "#FFF0EE",
    "info": "#006AA6",
    "info_soft": "#EAF6FC",
}


def apply_theme() -> None:
    """Aplica o sistema visual global do Portal Comercial.

    O tema é deliberadamente claro e com contraste alto. Isso evita que o
    esquema de cores do navegador/sistema operacional altere a legibilidade
    dos componentes nativos do Streamlit.
    """

    css = f"""
    <style>
        :root {{
            color-scheme: light;
            --portal-primary: {COLORS["primary"]};
            --portal-primary-dark: {COLORS["primary_dark"]};
            --portal-primary-hover: {COLORS["primary_hover"]};
            --portal-primary-soft: {COLORS["primary_soft"]};
            --portal-primary-soft-strong: {COLORS["primary_soft_strong"]};
            --portal-background: {COLORS["background"]};
            --portal-surface: {COLORS["surface"]};
            --portal-surface-soft: {COLORS["surface_soft"]};
            --portal-text: {COLORS["text"]};
            --portal-text-strong: {COLORS["text_strong"]};
            --portal-text-secondary: {COLORS["text_secondary"]};
            --portal-text-muted: {COLORS["text_muted"]};
            --portal-border: {COLORS["border"]};
            --portal-border-strong: {COLORS["border_strong"]};
            --portal-success: {COLORS["success"]};
            --portal-success-soft: {COLORS["success_soft"]};
            --portal-warning: {COLORS["warning"]};
            --portal-warning-soft: {COLORS["warning_soft"]};
            --portal-error: {COLORS["error"]};
            --portal-error-soft: {COLORS["error_soft"]};
            --portal-info: {COLORS["info"]};
            --portal-info-soft: {COLORS["info_soft"]};
            --portal-radius-sm: 8px;
            --portal-radius-md: 12px;
            --portal-radius-lg: 18px;
            --portal-shadow-sm: 0 2px 10px rgba(13, 38, 56, 0.045);
            --portal-shadow-md: 0 10px 28px rgba(13, 38, 56, 0.07);
        }}

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {{
            color-scheme: light !important;
            background: var(--portal-background) !important;
            color: var(--portal-text) !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        /* =============================================================
           ESTRUTURA GERAL
           ============================================================= */

        [data-testid="stAppViewContainer"] > .main {{
            background: var(--portal-background) !important;
        }}

        .block-container {{
            max-width: 1460px;
            padding-top: 1.35rem;
            padding-bottom: 3.5rem;
            padding-left: clamp(1.15rem, 3vw, 2.75rem);
            padding-right: clamp(1.15rem, 3vw, 2.75rem);
        }}

        header[data-testid="stHeader"] {{
            background: rgba(244, 247, 249, 0.92) !important;
            border-bottom: 1px solid rgba(216, 225, 231, 0.72);
            backdrop-filter: blur(8px);
        }}

        #MainMenu,
        footer {{
            visibility: hidden;
        }}

        hr {{
            border-color: var(--portal-border) !important;
            margin: 1.5rem 0 !important;
        }}

        /* =============================================================
           TEXTO E HIERARQUIA
           ============================================================= */

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4 {{
            color: var(--portal-text-strong) !important;
            letter-spacing: -0.022em;
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] blockquote,
        [data-testid="stText"] {{
            color: var(--portal-text) !important;
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        small {{
            color: var(--portal-text-secondary) !important;
        }}

        a {{
            color: var(--portal-primary) !important;
        }}


        /* =============================================================
           SIDEBAR V3 — RAIL FIXO + PAINEL SOBREPOSTO
           ============================================================= */

        section[data-testid="stSidebar"] {{
            width: 74px !important;
            min-width: 74px !important;
            max-width: 74px !important;
            overflow: visible !important;
            background: transparent !important;
            border-right: 0 !important;
            z-index: 1000;
        }}

        section[data-testid="stSidebar"] > div {{
            width: 74px !important;
            min-width: 74px !important;
            max-width: 74px !important;
            overflow: hidden !important;
            background: #FFFFFF !important;
            border-right: 1px solid var(--portal-border) !important;
            box-shadow: 5px 0 18px rgba(13, 38, 56, 0.045);
            transition: width .11s ease-out, max-width .11s ease-out, box-shadow .11s ease-out;
        }}

        section[data-testid="stSidebar"]:hover > div,
        section[data-testid="stSidebar"]:focus-within > div {{
            width: 286px !important;
            min-width: 286px !important;
            max-width: 286px !important;
            overflow: visible !important;
            box-shadow: 14px 0 36px rgba(13, 38, 56, 0.13);
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] button[kind="header"] {{
            display: none !important;
        }}

        .portal-sidebar-header {{
            width: 268px;
            padding: .75rem .6rem .75rem .55rem;
            border-bottom: 1px solid #E6EDF1;
            margin-bottom: .45rem;
            white-space: nowrap;
        }}

        .portal-sidebar-brandmark {{
            display: flex;
            align-items: center;
            gap: .72rem;
        }}

        .portal-sidebar-brand-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            min-width: 44px;
            height: 44px;
            margin-left: 1px;
            border-radius: 13px;
            background: linear-gradient(145deg, #005691, #003D66);
            color: #FFFFFF !important;
            font-size: 1.05rem;
            font-weight: 850;
            box-shadow: 0 6px 15px rgba(0, 86, 145, .22);
        }}

        .portal-sidebar-brand-copy,
        .portal-sidebar-user-copy,
        .portal-sidebar-section-label,
        .portal-sidebar-account-label,
        .portal-sidebar-footer {{
            opacity: 0;
            transition: opacity .08s linear;
        }}

        section[data-testid="stSidebar"]:hover .portal-sidebar-brand-copy,
        section[data-testid="stSidebar"]:hover .portal-sidebar-user-copy,
        section[data-testid="stSidebar"]:hover .portal-sidebar-section-label,
        section[data-testid="stSidebar"]:hover .portal-sidebar-account-label,
        section[data-testid="stSidebar"]:hover .portal-sidebar-footer,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-brand-copy,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-user-copy,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-section-label,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-account-label,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-footer {{
            opacity: 1;
        }}

        .portal-sidebar-organization {{
            color: var(--portal-primary) !important;
            font-size: .61rem;
            font-weight: 850;
            letter-spacing: .075em;
            text-transform: uppercase;
        }}

        .portal-sidebar-title {{
            margin-top: .12rem;
            color: var(--portal-text-strong) !important;
            font-size: .96rem;
            font-weight: 800;
            letter-spacing: -.02em;
        }}

        .portal-sidebar-section-label,
        .portal-sidebar-account-label {{
            width: 250px;
            margin: .82rem .85rem .34rem;
            color: #7A8A96 !important;
            font-size: .61rem;
            font-weight: 850;
            letter-spacing: .10em;
        }}

        section[data-testid="stSidebar"] .stButton {{
            width: 268px !important;
            margin: .08rem 0 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            width: 258px !important;
            min-height: 43px !important;
            margin-left: .35rem !important;
            justify-content: flex-start !important;
            padding: .48rem .77rem !important;
            border-radius: 11px !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            font-size: .86rem !important;
            font-weight: 680 !important;
            transition: background-color .08s linear, color .08s linear !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
            background: transparent !important;
            color: #334A59 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
            background: #EEF6FB !important;
            color: #003D66 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: #E0F0F9 !important;
            color: #003D66 !important;
            border-color: #C4E2F3 !important;
            box-shadow: inset 3px 0 0 #005691 !important;
            font-weight: 800 !important;
        }}

        .portal-sidebar-separator {{
            width: 258px;
            height: 1px;
            margin: .8rem .4rem .15rem;
            background: #E6EDF1;
        }}

        .portal-sidebar-user-compact {{
            display: flex;
            align-items: center;
            gap: .72rem;
            width: 258px;
            min-height: 50px;
            margin: 0 .35rem .35rem;
            padding: .3rem .48rem;
            white-space: nowrap;
        }}

        .portal-sidebar-avatar,
        .portal-sidebar-avatar-fallback {{
            width: 40px;
            min-width: 40px;
            height: 40px;
            border-radius: 50%;
        }}

        .portal-sidebar-avatar {{
            object-fit: cover;
            border: 2px solid #E5EEF3;
        }}

        .portal-sidebar-avatar-fallback {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #DDEEF8;
            color: #003D66 !important;
            font-weight: 850;
        }}

        .portal-sidebar-user-name {{
            max-width: 180px;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--portal-text-strong) !important;
            font-size: .78rem;
            font-weight: 760;
        }}

        .portal-sidebar-user-role {{
            margin-top: .08rem;
            color: var(--portal-text-muted) !important;
            font-size: .67rem;
        }}

        .portal-sidebar-footer {{
            width: 245px;
            margin: .7rem .85rem 1rem;
            color: #8897A2 !important;
            font-size: .64rem;
        }}

        @media (max-width: 900px) {{
            section[data-testid="stSidebar"] {{
                width: 286px !important;
                min-width: 286px !important;
                max-width: 286px !important;
            }}

            section[data-testid="stSidebar"] > div {{
                width: 286px !important;
                min-width: 286px !important;
                max-width: 286px !important;
            }}

            .portal-sidebar-brand-copy,
            .portal-sidebar-user-copy,
            .portal-sidebar-section-label,
            .portal-sidebar-account-label,
            .portal-sidebar-footer {{
                opacity: 1 !important;
            }}
        }}

        /* =============================================================
           HERO / CABEÇALHO DE PÁGINA
           ============================================================= */

        .portal-hero {{
            position: relative;
            overflow: hidden;
            padding: clamp(1.4rem, 3vw, 2.05rem) clamp(1.35rem, 3vw, 2.2rem);
            background: linear-gradient(135deg, #FFFFFF 0%, #F1F7FA 100%);
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-lg);
            box-shadow: var(--portal-shadow-sm);
            margin-bottom: 1.4rem;
        }}

        .portal-hero::before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: var(--portal-primary);
        }}

        .portal-hero-eyebrow {{
            color: var(--portal-primary) !important;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.58rem;
        }}

        .portal-hero-title {{
            margin: 0;
            color: var(--portal-text-strong) !important;
            font-size: clamp(1.65rem, 3.3vw, 2.45rem);
            line-height: 1.12;
            letter-spacing: -0.035em;
        }}

        .portal-hero-description {{
            margin: 0.8rem 0 0;
            max-width: 860px;
            color: var(--portal-text-secondary) !important;
            font-size: 0.98rem;
            line-height: 1.6;
        }}

        /* =============================================================
           CARDS E CONTAINERS
           ============================================================= */

        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--portal-border) !important;
            border-radius: var(--portal-radius-md) !important;
            background: var(--portal-surface) !important;
            box-shadow: var(--portal-shadow-sm);
        }}

        .portal-metric-card {{
            min-height: 154px;
            padding: 1.2rem;
            background: var(--portal-surface);
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            box-shadow: var(--portal-shadow-sm);
        }}

        .portal-metric-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .portal-metric-label {{
            color: var(--portal-text-secondary) !important;
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.055em;
        }}

        .portal-metric-icon,
        .portal-module-icon,
        .portal-operadora-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--portal-primary-soft);
        }}

        .portal-metric-icon {{
            width: 38px;
            height: 38px;
            border-radius: 10px;
            font-size: 1.1rem;
        }}

        .portal-metric-value {{
            margin-top: 0.9rem;
            color: var(--portal-text-strong) !important;
            font-size: 1.85rem;
            line-height: 1;
            font-weight: 780;
        }}

        .portal-metric-description {{
            margin-top: 0.5rem;
            color: var(--portal-text-secondary) !important;
            font-size: 0.85rem;
            line-height: 1.45;
        }}

        .portal-module-card {{
            display: flex;
            align-items: flex-start;
            gap: 0.9rem;
            min-height: 88px;
        }}

        .portal-module-icon {{
            min-width: 44px;
            height: 44px;
            border-radius: 12px;
            font-size: 1.25rem;
        }}

        .portal-module-title {{
            color: var(--portal-text-strong) !important;
            font-size: 1rem;
            font-weight: 750;
        }}

        .portal-module-description {{
            margin-top: 0.32rem;
            color: var(--portal-text-secondary) !important;
            font-size: 0.86rem;
            line-height: 1.45;
        }}

        /* =============================================================
           BOTÕES
           ============================================================= */

        .stButton > button,
        .stLinkButton > a {{
            min-height: 42px;
            border-radius: 10px !important;
            font-weight: 680 !important;
            box-shadow: none !important;
        }}

        .stButton > button:not([kind="primary"]),
        button[data-testid="stBaseButton-secondary"],
        .stLinkButton > a {{
            border: 1px solid var(--portal-border-strong) !important;
            background: var(--portal-surface) !important;
            color: var(--portal-text-strong) !important;
        }}

        .stButton > button:not([kind="primary"]):hover,
        button[data-testid="stBaseButton-secondary"]:hover,
        .stLinkButton > a:hover {{
            border-color: var(--portal-primary) !important;
            background: var(--portal-primary-soft) !important;
            color: var(--portal-primary-dark) !important;
        }}

        button[kind="primary"],
        button[data-testid="stBaseButton-primary"] {{
            border: 1px solid var(--portal-primary) !important;
            background: var(--portal-primary) !important;
            color: #FFFFFF !important;
        }}

        button[kind="primary"] p,
        button[data-testid="stBaseButton-primary"] p {{
            color: #FFFFFF !important;
        }}

        button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover {{
            border-color: var(--portal-primary-dark) !important;
            background: var(--portal-primary-dark) !important;
            color: #FFFFFF !important;
        }}

        button:focus-visible,
        a:focus-visible,
        input:focus-visible,
        textarea:focus-visible {{
            outline: 3px solid rgba(0, 86, 145, 0.2) !important;
            outline-offset: 1px;
        }}

        /* =============================================================
           CAMPOS, SELECTS E FORMULÁRIOS
           ============================================================= */

        label,
        label p,
        [data-testid="stWidgetLabel"] p {{
            color: var(--portal-text-strong) !important;
        }}

        input,
        textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {{
            color: var(--portal-text) !important;
            -webkit-text-fill-color: var(--portal-text) !important;
            caret-color: var(--portal-primary) !important;
        }}

        input::placeholder,
        textarea::placeholder {{
            color: #87949E !important;
            -webkit-text-fill-color: #87949E !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div,
        [data-testid="stNumberInput"] > div > div {{
            border-color: var(--portal-border-strong) !important;
            background: var(--portal-surface) !important;
            border-radius: 10px !important;
            color: var(--portal-text) !important;
        }}

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {{
            color: var(--portal-text) !important;
        }}

        div[data-baseweb="popover"],
        div[role="listbox"],
        ul[role="listbox"] {{
            background: var(--portal-surface) !important;
            color: var(--portal-text) !important;
        }}

        li[role="option"],
        li[role="option"] span,
        div[role="option"],
        div[role="option"] span {{
            color: var(--portal-text) !important;
        }}

        li[role="option"]:hover,
        div[role="option"]:hover {{
            background: var(--portal-primary-soft) !important;
        }}

        div[data-testid="stForm"] {{
            padding: 1.2rem !important;
            border: 1px solid var(--portal-border) !important;
            border-radius: var(--portal-radius-md) !important;
            background: var(--portal-surface) !important;
        }}

        [data-testid="stCheckbox"] label p,
        [data-testid="stRadio"] label p {{
            color: var(--portal-text) !important;
        }}

        /* =============================================================
           ABAS
           ============================================================= */

        [data-baseweb="tab-list"] {{
            gap: 0.25rem;
            padding: 0.3rem;
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            background: var(--portal-surface);
        }}

        button[data-baseweb="tab"] {{
            min-height: 42px;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            border-radius: 9px;
        }}

        button[data-baseweb="tab"] p,
        button[data-baseweb="tab"] span {{
            color: var(--portal-text-secondary) !important;
            font-weight: 650 !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background: var(--portal-primary-soft) !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span {{
            color: var(--portal-primary-dark) !important;
            font-weight: 760 !important;
        }}

        [data-baseweb="tab-highlight"] {{
            background-color: var(--portal-primary) !important;
        }}

        /* =============================================================
           MÉTRICAS NATIVAS / DATAFRAMES / EXPANDERS
           ============================================================= */

        [data-testid="stMetric"] {{
            padding: 1rem 1.05rem;
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            background: var(--portal-surface);
            box-shadow: var(--portal-shadow-sm);
        }}

        [data-testid="stMetricLabel"] p {{
            color: var(--portal-text-secondary) !important;
            font-weight: 700 !important;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--portal-text-strong) !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--portal-border) !important;
            border-radius: var(--portal-radius-md) !important;
            background: var(--portal-surface) !important;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p {{
            color: var(--portal-text-strong) !important;
            font-weight: 680 !important;
        }}

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            overflow: hidden;
            background: var(--portal-surface);
        }}

        /* =============================================================
           ALERTAS
           ============================================================= */

        div[data-testid="stAlert"] {{
            border-radius: var(--portal-radius-md) !important;
            border-width: 1px !important;
        }}

        div[data-testid="stAlert"] p {{
            color: var(--portal-text-strong) !important;
        }}

        /* =============================================================
           BUSCA
           ============================================================= */

        .portal-search-result {{
            padding: 0.15rem 0;
        }}

        .portal-search-result-top {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.65rem;
        }}

        .portal-search-result-icon {{
            font-size: 1rem;
        }}

        .portal-search-result-category {{
            color: var(--portal-primary) !important;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.055em;
            text-transform: uppercase;
        }}

        .portal-search-result-operator {{
            padding: 0.18rem 0.42rem;
            border-radius: 999px;
            background: var(--portal-surface-soft);
            color: var(--portal-text-secondary) !important;
            font-size: 0.72rem;
            font-weight: 650;
        }}

        .portal-search-result-title {{
            color: var(--portal-text-strong) !important;
            font-size: 1.04rem;
            font-weight: 760;
            line-height: 1.35;
        }}

        .portal-search-result-subtitle,
        .portal-search-result-description {{
            color: var(--portal-text-secondary) !important;
        }}

        .portal-search-result-subtitle {{
            margin-top: 0.28rem;
            font-size: 0.82rem;
            font-weight: 620;
        }}

        .portal-search-result-description {{
            margin-top: 0.6rem;
            font-size: 0.87rem;
            line-height: 1.55;
        }}

        /* =============================================================
           OPERADORAS
           ============================================================= */

        .portal-operadora-card {{
            min-height: 180px;
            padding: 0.2rem 0;
        }}

        .portal-operadora-card-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .portal-operadora-icon {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            font-size: 1.2rem;
        }}

        .portal-operadora-status {{
            padding: 0.3rem 0.58rem;
            border-radius: 999px;
            background: var(--portal-success-soft);
            color: #166534 !important;
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
        }}

        .portal-operadora-name {{
            margin-top: 0.95rem;
            color: var(--portal-text-strong) !important;
            font-size: 1.08rem;
            font-weight: 760;
            line-height: 1.3;
        }}

        .portal-operadora-full-name {{
            min-height: 40px;
            margin-top: 0.3rem;
            color: var(--portal-text-secondary) !important;
            font-size: 0.82rem;
            line-height: 1.4;
        }}

        .portal-operadora-plans {{
            margin-top: 0.85rem;
            color: var(--portal-text-secondary) !important;
            font-size: 0.84rem;
        }}

        .portal-operadora-plans strong {{
            color: var(--portal-primary) !important;
        }}

        /* =============================================================
           CODE / CREDENCIAIS
           ============================================================= */

        [data-testid="stCode"] {{
            border-radius: 10px !important;
            border: 1px solid var(--portal-border) !important;
        }}

        [data-testid="stCode"] code,
        [data-testid="stCode"] pre {{
            color: #17212B !important;
            background: #F2F5F7 !important;
        }}

        /* =============================================================
           RESPONSIVIDADE
           ============================================================= */

        @media (max-width: 900px) {{
            .block-container {{
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            .portal-hero {{
                padding: 1.35rem 1.25rem;
            }}

            .portal-hero-title {{
                font-size: 1.65rem;
            }}

            [data-baseweb="tab-list"] {{
                overflow-x: auto;
                flex-wrap: nowrap;
            }}
        }}


        /* =============================================================
           HOME V3 — HALL / COMMAND CENTER
           ============================================================= */

        .portal-home-hero-v3 {{
            display: grid;
            grid-template-columns: minmax(0, 1.55fr) minmax(280px, .72fr);
            gap: clamp(1.4rem, 3vw, 3rem);
            align-items: stretch;
            min-height: 312px;
            padding: clamp(2rem, 3.7vw, 3.4rem);
            border-radius: 26px;
            background:
                radial-gradient(circle at 75% 12%, rgba(38, 146, 205, .28), transparent 24%),
                radial-gradient(circle at 98% 92%, rgba(255,255,255,.10), transparent 29%),
                linear-gradient(135deg, #005691 0%, #004B7E 47%, #003D66 100%);
            box-shadow: 0 20px 52px rgba(0,61,102,.17);
            position: relative;
            overflow: hidden;
        }}

        .portal-home-hero-copy {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-width: 0;
        }}

        .portal-home-kicker {{
            color: #CAE9FA !important;
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        .portal-home-title {{
            max-width: 780px;
            margin: .55rem 0 0;
            color: #FFFFFF !important;
            font-size: clamp(2.25rem, 4vw, 3.55rem);
            line-height: 1.02;
            letter-spacing: -.052em;
        }}

        .portal-home-title span {{
            display: block;
            color: #AEDDFA !important;
        }}

        .portal-home-description {{
            max-width: 650px;
            margin: .95rem 0 0;
            color: #E8F4FA !important;
            font-size: .98rem;
            line-height: 1.62;
        }}

        .portal-home-hero-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: .42rem;
            margin-top: 1.2rem;
        }}

        .portal-home-hero-tags span {{
            padding: .33rem .58rem;
            border: 1px solid rgba(255,255,255,.19);
            border-radius: 999px;
            background: rgba(255,255,255,.08);
            color: #F2F9FD !important;
            font-size: .68rem;
            font-weight: 650;
        }}

        .portal-home-pulse {{
            align-self: center;
            padding: 1.25rem;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 20px;
            background: rgba(255,255,255,.10);
            backdrop-filter: blur(10px);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
        }}

        .portal-home-pulse-label {{
            color: #BFE4F7 !important;
            font-size: .61rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        .portal-home-pulse-main {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: .65rem;
            margin-top: .72rem;
        }}

        .portal-home-pulse-main > div {{
            padding: .75rem;
            border-radius: 13px;
            background: rgba(0,35,60,.22);
        }}

        .portal-home-pulse-main strong {{
            display: block;
            color: #FFFFFF !important;
            font-size: 1.7rem;
            line-height: 1;
        }}

        .portal-home-pulse-main span,
        .portal-home-pulse-row span,
        .portal-home-pulse-foot {{
            color: #DDEFF8 !important;
            font-size: .68rem;
        }}

        .portal-home-pulse-row {{
            display: grid;
            gap: .3rem;
            margin-top: .72rem;
        }}

        .portal-home-pulse-row b {{
            color: #FFFFFF !important;
        }}

        .portal-home-pulse-foot {{
            margin-top: .9rem;
            padding-top: .75rem;
            border-top: 1px solid rgba(255,255,255,.14);
        }}

        .portal-command-heading {{
            margin: 1.75rem auto .7rem;
            text-align: center;
        }}

        .portal-command-eyebrow,
        .portal-home-section-eyebrow {{
            color: var(--portal-primary) !important;
            font-size: .64rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        .portal-command-title {{
            margin-top: .16rem;
            color: var(--portal-text-strong) !important;
            font-size: clamp(1.55rem, 2.8vw, 2.18rem);
            font-weight: 820;
            letter-spacing: -.035em;
        }}

        .portal-command-subtitle {{
            max-width: 680px;
            margin: .25rem auto 0;
            color: var(--portal-text-secondary) !important;
            font-size: .82rem;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) {{
            max-width: 1040px;
            margin: 0 auto .6rem;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) div[data-baseweb="input"] > div {{
            min-height: 68px !important;
            border: 1px solid #C7D6E0 !important;
            border-radius: 21px !important;
            background: #FFFFFF !important;
            box-shadow: 0 14px 38px rgba(13,38,56,.095) !important;
            padding-left: .8rem !important;
            padding-right: .8rem !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) input {{
            font-size: .98rem !important;
            color: #163044 !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) div[data-baseweb="input"] > div:focus-within {{
            border-color: #005691 !important;
            box-shadow:
                0 0 0 4px rgba(0,86,145,.09),
                0 17px 42px rgba(13,38,56,.11) !important;
        }}

        .portal-home-dock-label {{
            max-width: 1040px;
            margin: .72rem auto .25rem;
            color: #7B8B96 !important;
            font-size: .59rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        /* atalhos imediatamente após o campo de busca */
        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"])
        + div + div [data-testid="stButton"] button {{
            min-height: 42px;
        }}

        .portal-home-section-head {{
            margin: 2.15rem 0 .8rem;
        }}

        .portal-home-section-title {{
            margin-top: .13rem;
            color: var(--portal-text-strong) !important;
            font-size: 1.62rem;
            font-weight: 810;
            letter-spacing: -.035em;
        }}

        .portal-home-section-description {{
            margin-top: .18rem;
            color: var(--portal-text-secondary) !important;
            font-size: .82rem;
        }}

        .portal-feed-card {{
            padding: 1.05rem 1.1rem;
            margin-bottom: .68rem;
            border: 1px solid #D9E3E9;
            border-radius: 15px;
            background: #FFFFFF;
            box-shadow: 0 3px 13px rgba(13,38,56,.045);
        }}

        .portal-feed-card-featured {{
            padding: 1.3rem;
            border-color: #BFD9E8;
            background: linear-gradient(145deg, #FFFFFF 0%, #F3F9FC 100%);
            box-shadow: 0 12px 28px rgba(0,86,145,.08);
        }}

        .portal-feed-card-alert {{
            border-left: 4px solid #A86100;
        }}

        .portal-feed-topline {{
            display: flex;
            align-items: center;
            gap: .42rem;
            color: #6C7C88 !important;
            font-size: .59rem;
            font-weight: 850;
            letter-spacing: .08em;
        }}

        .portal-feed-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            flex: 0 0 auto;
        }}

        .portal-feed-dot-alert {{ background: #C47A13; }}
        .portal-feed-dot-notice {{ background: #005691; }}

        .portal-feed-priority {{
            margin-left: auto;
            padding: .22rem .46rem;
            border-radius: 999px;
            background: #F2F5F7;
            color: #50616E !important;
            letter-spacing: 0;
        }}

        .portal-feed-title {{
            margin-top: .58rem;
            color: var(--portal-text-strong) !important;
            font-size: 1.02rem;
            font-weight: 790;
            line-height: 1.3;
        }}

        .portal-feed-card-featured .portal-feed-title {{
            font-size: 1.25rem;
        }}

        .portal-feed-meta {{
            margin-top: .25rem;
            color: var(--portal-text-muted) !important;
            font-size: .72rem;
        }}

        .portal-feed-body {{
            margin-top: .62rem;
            color: var(--portal-text-secondary) !important;
            font-size: .82rem;
            line-height: 1.52;
        }}

        .portal-feed-footer {{
            margin-top: .72rem;
            padding-top: .6rem;
            border-top: 1px solid #EDF1F4;
            color: #6B7A86 !important;
            font-size: .69rem;
        }}

        .portal-empty-state {{
            display: flex;
            gap: .75rem;
            align-items: center;
            padding: 1.15rem;
            border: 1px dashed #C7D6DF;
            border-radius: 15px;
            background: rgba(255,255,255,.55);
        }}

        .portal-empty-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: #EAF6ED;
            color: #237A3B !important;
            font-weight: 850;
        }}

        .portal-empty-state strong {{
            display: block;
            color: var(--portal-text-strong) !important;
            font-size: .86rem;
        }}

        .portal-empty-state span {{
            display: block;
            margin-top: .15rem;
            color: var(--portal-text-secondary) !important;
            font-size: .73rem;
        }}

        .portal-explore-card {{
            min-height: 142px;
            margin-top: .12rem;
            padding: 1.12rem;
            border: 1px solid #DAE4EA;
            border-bottom: 0;
            border-radius: 16px 16px 0 0;
            background: #FFFFFF;
        }}

        .portal-explore-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 11px;
            background: #EAF4FA;
            font-size: 1rem;
        }}

        .portal-explore-title {{
            margin-top: .72rem;
            color: var(--portal-text-strong) !important;
            font-size: .93rem;
            font-weight: 790;
        }}

        .portal-explore-description {{
            margin-top: .28rem;
            color: var(--portal-text-secondary) !important;
            font-size: .74rem;
            line-height: 1.45;
        }}

        @media (max-width: 1050px) {{
            .portal-home-hero-v3 {{
                grid-template-columns: 1fr;
            }}

            .portal-home-pulse {{
                display: none;
            }}
        }}

        @media (max-width: 700px) {{
            .portal-home-hero-v3 {{
                min-height: 0;
                padding: 1.65rem 1.3rem;
                border-radius: 19px;
            }}

            .portal-home-title {{
                font-size: 2.05rem;
            }}

            .portal-home-hero-tags {{
                display: none;
            }}
        }}


        /* =============================================================
           AJUSTES FINAIS HOME / SIDEBAR
           ============================================================= */

        /* Sidebar: força contraste dos ícones e textos em qualquer estado */
        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] .stButton > button *,
        section[data-testid="stSidebar"] .stButton > button p,
        section[data-testid="stSidebar"] .stButton > button span {{
            color: #334A59 !important;
            -webkit-text-fill-color: #334A59 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="primary"],
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {{
            color: #003D66 !important;
            -webkit-text-fill-color: #003D66 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button svg {{
            fill: currentColor !important;
            stroke: currentColor !important;
        }}

        /* deixa o primeiro símbolo sempre visível quando a rail está recolhida */
        section[data-testid="stSidebar"] .stButton > button {{
            padding-left: .82rem !important;
            letter-spacing: 0 !important;
        }}

        /* Pesquisa: centralização vertical e melhor leitura */
        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) div[data-baseweb="input"] > div {{
            display: flex !important;
            align-items: center !important;
            min-height: 68px !important;
            height: 68px !important;
            padding: 0 .75rem !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) input {{
            height: 64px !important;
            min-height: 64px !important;
            padding: 0 .75rem !important;
            margin: 0 !important;
            line-height: 1.35 !important;
            display: flex !important;
            align-items: center !important;
            color: #163044 !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) input::placeholder {{
            color: #7B8B96 !important;
            opacity: 1 !important;
        }}

        /* Atalhos da Home: tiles mais convidativos */
        .st-key-home_quick_actions {{
            max-width: 1040px;
            margin: 0 auto 1.1rem;
        }}

        .st-key-home_quick_actions .portal-home-dock-label {{
            margin: .72rem 0 .35rem;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button {{
            min-height: 72px !important;
            border: 1px solid #D4E1E8 !important;
            border-radius: 16px !important;
            background:
                linear-gradient(180deg, #FFFFFF 0%, #F7FBFD 100%) !important;
            color: #173447 !important;
            font-weight: 760 !important;
            font-size: .88rem !important;
            box-shadow: 0 6px 18px rgba(13, 38, 56, .055) !important;
            transition:
                transform .12s ease,
                border-color .12s ease,
                box-shadow .12s ease,
                background-color .12s ease !important;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button * {{
            color: #173447 !important;
            -webkit-text-fill-color: #173447 !important;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button:hover {{
            transform: translateY(-2px);
            border-color: #9EC8DF !important;
            background:
                linear-gradient(180deg, #FFFFFF 0%, #EEF7FC 100%) !important;
            box-shadow: 0 10px 24px rgba(0, 86, 145, .10) !important;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button:focus-visible {{
            outline: 3px solid rgba(0, 86, 145, .16) !important;
            outline-offset: 2px;
        }}

        @media (max-width: 900px) {{
            .st-key-home_quick_actions [data-testid="stButton"] > button {{
                min-height: 60px !important;
            }}
        }}

    </style>
    """

    st.html(css)
