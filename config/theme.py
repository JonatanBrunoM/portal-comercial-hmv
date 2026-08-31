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
           SIDEBAR
           ============================================================= */

        section[data-testid="stSidebar"] {{
            background: var(--portal-surface) !important;
            border-right: 1px solid var(--portal-border) !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background: var(--portal-surface) !important;
            padding-top: 1.15rem;
        }}

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: var(--portal-text-secondary) !important;
        }}

        .portal-sidebar-header {{
            padding: 0.35rem 0.2rem 1.25rem;
            border-bottom: 1px solid var(--portal-border);
            margin-bottom: 0.9rem;
        }}

        .portal-sidebar-organization {{
            color: var(--portal-primary) !important;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }}

        .portal-sidebar-title {{
            color: var(--portal-text-strong) !important;
            font-size: 1.25rem;
            font-weight: 760;
            margin-top: 0.28rem;
            letter-spacing: -0.02em;
        }}

        .portal-sidebar-section-label {{
            margin: 0.8rem 0.2rem 0.45rem;
            color: var(--portal-text-muted) !important;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        section[data-testid="stSidebar"] [role="radiogroup"] {{
            gap: 0.18rem;
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"] {{
            min-height: 42px;
            padding: 0.52rem 0.7rem;
            border-radius: 10px;
            color: var(--portal-text) !important;
            transition: background-color 0.16s ease, color 0.16s ease;
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{
            background: var(--portal-primary-soft) !important;
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"] p {{
            color: var(--portal-text) !important;
            font-weight: 620 !important;
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {{
            background: var(--portal-primary-soft-strong) !important;
            box-shadow: inset 3px 0 0 var(--portal-primary);
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p {{
            color: var(--portal-primary-dark) !important;
            font-weight: 760 !important;
        }}

        section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {{
            display: none;
        }}

        .portal-user-card {{
            padding: 0.85rem;
            margin: 0.25rem 0 0.65rem;
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            background: var(--portal-surface-soft);
        }}

        .portal-user-role {{
            display: inline-flex;
            align-items: center;
            margin-top: 0.25rem;
            padding: 0.2rem 0.45rem;
            border-radius: 999px;
            background: var(--portal-primary-soft);
            color: var(--portal-primary-dark) !important;
            font-size: 0.7rem;
            font-weight: 750;
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
    </style>
    """

    st.html(css)
