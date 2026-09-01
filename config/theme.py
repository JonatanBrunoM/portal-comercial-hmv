import streamlit as st


COLORS = {
    "primary": "#005691",
    "primary_dark": "#003D66",
    "primary_light": "#EAF4FA",
    "primary_soft": "#F2F8FC",
    "background": "#F4F7F9",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFB",
    "text": "#17212B",
    "text_secondary": "#5B6773",
    "text_muted": "#7C8B96",
    "border": "#D7E1E7",
    "border_strong": "#C6D5DE",
    "success": "#2E7D32",
    "warning": "#B86B00",
    "error": "#C62828",
}


def apply_theme() -> None:
    """Aplica um único sistema visual global ao Portal Comercial."""

    css = f"""
    <style>
        :root {{
            --portal-primary: {COLORS["primary"]};
            --portal-primary-dark: {COLORS["primary_dark"]};
            --portal-primary-light: {COLORS["primary_light"]};
            --portal-primary-soft: {COLORS["primary_soft"]};
            --portal-background: {COLORS["background"]};
            --portal-surface: {COLORS["surface"]};
            --portal-surface-soft: {COLORS["surface_soft"]};
            --portal-text: {COLORS["text"]};
            --portal-text-secondary: {COLORS["text_secondary"]};
            --portal-text-muted: {COLORS["text_muted"]};
            --portal-border: {COLORS["border"]};
            --portal-border-strong: {COLORS["border_strong"]};
            --portal-success: {COLORS["success"]};
            --portal-warning: {COLORS["warning"]};
            --portal-error: {COLORS["error"]};

            --portal-radius-sm: 10px;
            --portal-radius-md: 14px;
            --portal-radius-lg: 20px;
            --portal-shadow-sm: 0 4px 14px rgba(13, 38, 56, 0.05);
            --portal-shadow-md: 0 12px 30px rgba(13, 38, 56, 0.08);
            --portal-content-max: 1320px;
            --portal-sidebar-rail: 76px;
            --portal-sidebar-open: 292px;
        }}

        /* =========================================================
           RESET / ESTRUTURA
           ========================================================= */

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background: var(--portal-background) !important;
            color: var(--portal-text) !important;
        }}

        html,
        body,
        [class*="css"],
        .stApp {{
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif !important;
        }}

        /* Remove a barra visual do Streamlit no topo do portal. */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stAppViewContainer"] {{
            padding-top: 0 !important;
        }}

        .block-container {{
            width: 100% !important;
            max-width: var(--portal-content-max) !important;
            padding-top: 1.25rem !important;
            padding-bottom: 3rem !important;
            padding-left: 1.65rem !important;
            padding-right: 1.65rem !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--portal-text) !important;
            letter-spacing: -0.025em;
        }}

        p, label, span {{
            text-rendering: geometricPrecision;
        }}

        /* =========================================================
           BOTÕES GLOBAIS
           ========================================================= */

        main .stButton > button {{
            min-height: 44px !important;
            border-radius: 12px !important;
            border: 1px solid var(--portal-border-strong) !important;
            background: var(--portal-surface) !important;
            color: var(--portal-text) !important;
            font-size: 0.86rem !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
            box-shadow: none !important;
            transition:
                transform .10s ease,
                border-color .10s ease,
                background .10s ease,
                box-shadow .10s ease !important;
        }}

        main .stButton > button *,
        main .stButton > button p,
        main .stButton > button span {{
            color: inherit !important;
            -webkit-text-fill-color: currentColor !important;
        }}

        main .stButton > button:hover {{
            transform: translateY(-1px);
            border-color: #9FC4D9 !important;
            background: #F8FCFE !important;
            color: var(--portal-primary-dark) !important;
            box-shadow: 0 6px 16px rgba(0, 86, 145, .07) !important;
        }}

        main .stButton > button[kind="primary"] {{
            border-color: var(--portal-primary) !important;
            background: var(--portal-primary) !important;
            color: #FFFFFF !important;
        }}

        main .stButton > button[kind="primary"]:hover {{
            border-color: var(--portal-primary-dark) !important;
            background: var(--portal-primary-dark) !important;
            color: #FFFFFF !important;
        }}

        main .stButton > button:focus-visible {{
            outline: 3px solid rgba(0, 86, 145, .16) !important;
            outline-offset: 2px !important;
        }}

        /* =========================================================
           INPUTS / SELECTS / TEXTAREAS
           ========================================================= */

        [data-testid="stTextInput"] div[data-baseweb="input"],
        [data-testid="stNumberInput"] div[data-baseweb="input"],
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] div[data-baseweb="input"],
        [data-testid="stTextArea"] textarea {{
            border-color: var(--portal-border-strong) !important;
            border-radius: 11px !important;
            background: var(--portal-surface) !important;
            color: var(--portal-text) !important;
            box-shadow: none !important;
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTextArea"] textarea {{
            color: var(--portal-text) !important;
            -webkit-text-fill-color: var(--portal-text) !important;
        }}

        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {{
            color: #8796A1 !important;
            -webkit-text-fill-color: #8796A1 !important;
            opacity: 1 !important;
        }}

        /* =========================================================
           SIDEBAR — RAIL FIXO + OVERLAY INSTANTÂNEO
           ========================================================= */

        section[data-testid="stSidebar"] {{
            width: var(--portal-sidebar-rail) !important;
            min-width: var(--portal-sidebar-rail) !important;
            max-width: var(--portal-sidebar-rail) !important;
            overflow: visible !important;
            background: transparent !important;
            border: 0 !important;
            z-index: 99999 !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            width: var(--portal-sidebar-rail) !important;
            min-width: var(--portal-sidebar-rail) !important;
            max-width: var(--portal-sidebar-rail) !important;
            height: 100% !important;
            overflow: hidden !important;
            background: var(--portal-surface) !important;
            border-right: 1px solid var(--portal-border) !important;
            box-shadow: 5px 0 16px rgba(13, 38, 56, .045);
            transition:
                width .08s linear,
                min-width .08s linear,
                max-width .08s linear,
                box-shadow .08s linear !important;
        }}

        section[data-testid="stSidebar"]:hover > div:first-child,
        section[data-testid="stSidebar"]:focus-within > div:first-child {{
            width: var(--portal-sidebar-open) !important;
            min-width: var(--portal-sidebar-open) !important;
            max-width: var(--portal-sidebar-open) !important;
            box-shadow: 14px 0 34px rgba(13, 38, 56, .13);
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] button[kind="header"] {{
            display: none !important;
        }}

        .portal-sidebar-header {{
            width: 276px;
            height: 72px;
            display: flex;
            align-items: center;
            padding: 0 0 0 15px;
            margin: 0;
            border-bottom: 1px solid var(--portal-border);
            overflow: hidden;
            white-space: nowrap;
        }}

        .portal-sidebar-brandmark {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .portal-sidebar-brand-icon {{
            width: 46px;
            min-width: 46px;
            height: 46px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 13px;
            background: linear-gradient(
                145deg,
                var(--portal-primary),
                var(--portal-primary-dark)
            );
            color: #FFFFFF !important;
            font-size: 1rem;
            font-weight: 850;
            box-shadow: 0 6px 15px rgba(0, 86, 145, .18);
        }}

        .portal-sidebar-brand-copy,
        .portal-sidebar-section-label,
        .portal-sidebar-account-label,
        .portal-sidebar-user-copy,
        .portal-sidebar-footer {{
            opacity: 0;
            transition: opacity .05s linear !important;
        }}

        section[data-testid="stSidebar"]:hover .portal-sidebar-brand-copy,
        section[data-testid="stSidebar"]:hover .portal-sidebar-section-label,
        section[data-testid="stSidebar"]:hover .portal-sidebar-account-label,
        section[data-testid="stSidebar"]:hover .portal-sidebar-user-copy,
        section[data-testid="stSidebar"]:hover .portal-sidebar-footer,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-brand-copy,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-section-label,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-account-label,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-user-copy,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-footer {{
            opacity: 1;
        }}

        .portal-sidebar-organization {{
            color: var(--portal-primary) !important;
            font-size: .60rem;
            font-weight: 850;
            letter-spacing: .075em;
            text-transform: uppercase;
        }}

        .portal-sidebar-title {{
            margin-top: 2px;
            color: var(--portal-text) !important;
            font-size: .97rem;
            font-weight: 800;
        }}

        .portal-sidebar-section-label,
        .portal-sidebar-account-label {{
            width: 260px;
            margin: 13px 0 5px 18px;
            color: var(--portal-text-muted) !important;
            font-size: .59rem;
            font-weight: 850;
            letter-spacing: .105em;
        }}

        section[data-testid="stSidebar"] .stButton {{
            width: 276px !important;
            margin: 1px 0 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            width: 260px !important;
            height: 44px !important;
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 13px !important;
            margin: 0 0 0 7px !important;
            padding: 0 14px !important;
            border: 1px solid transparent !important;
            border-radius: 11px !important;
            background: transparent !important;
            color: #425765 !important;
            box-shadow: none !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            font-size: .84rem !important;
            font-weight: 680 !important;
            line-height: 1 !important;
            transition: background .07s linear, color .07s linear !important;
        }}

        section[data-testid="stSidebar"] .stButton > button *,
        section[data-testid="stSidebar"] .stButton > button p,
        section[data-testid="stSidebar"] .stButton > button span {{
            color: inherit !important;
            -webkit-text-fill-color: currentColor !important;
        }}

        section[data-testid="stSidebar"] .stButton > button svg {{
            width: 22px !important;
            min-width: 22px !important;
            height: 22px !important;
            color: currentColor !important;
            fill: currentColor !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
            background: #EFF7FB !important;
            color: var(--portal-primary-dark) !important;
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: #E2F1FA !important;
            color: var(--portal-primary-dark) !important;
            border-color: #C7E1F0 !important;
            box-shadow: inset 3px 0 0 var(--portal-primary) !important;
            font-weight: 800 !important;
        }}

        .portal-sidebar-separator {{
            width: 260px;
            height: 1px;
            margin: 12px 7px 3px;
            background: var(--portal-border);
        }}

        .portal-sidebar-user-compact {{
            width: 260px;
            min-height: 52px;
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 0 0 4px 7px;
            padding: 4px 8px;
            overflow: hidden;
            white-space: nowrap;
        }}

        .portal-sidebar-avatar,
        .portal-sidebar-avatar-fallback {{
            width: 44px !important;
            min-width: 44px !important;
            height: 44px !important;
            border-radius: 50% !important;
            flex: 0 0 44px !important;
        }}

        .portal-sidebar-avatar {{
            object-fit: cover !important;
            border: 2px solid #E0EAF0;
        }}

        .portal-sidebar-avatar-fallback {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: #DDEEF8;
            color: var(--portal-primary-dark) !important;
            font-weight: 850;
        }}

        .portal-sidebar-user-name {{
            max-width: 185px;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--portal-text) !important;
            font-size: .78rem;
            font-weight: 760;
        }}

        .portal-sidebar-user-role {{
            margin-top: 2px;
            color: var(--portal-text-muted) !important;
            font-size: .66rem;
        }}

        .portal-sidebar-footer {{
            width: 245px;
            margin: 10px 0 20px 20px;
            color: #8B99A3 !important;
            font-size: .63rem;
        }}

        /* =========================================================
           HERO GENÉRICO DAS DEMAIS PÁGINAS
           ========================================================= */

        .portal-hero {{
            padding: 1.8rem 2rem;
            margin-bottom: 1.35rem;
            border: 1px solid #DCE7EE;
            border-radius: 18px;
            background: linear-gradient(135deg, #FFFFFF 0%, #F4F9FC 100%);
            box-shadow: var(--portal-shadow-sm);
        }}

        .portal-hero-eyebrow {{
            color: var(--portal-primary) !important;
            font-size: .70rem;
            font-weight: 800;
            letter-spacing: .09em;
            text-transform: uppercase;
        }}

        .portal-hero-title {{
            margin: .35rem 0 0;
            color: var(--portal-text) !important;
            font-size: clamp(1.75rem, 3vw, 2.45rem);
            line-height: 1.08;
        }}

        .portal-hero-description {{
            max-width: 780px;
            margin: .7rem 0 0;
            color: var(--portal-text-secondary) !important;
            line-height: 1.55;
        }}

        /* =========================================================
           HOME
           ========================================================= */

        .portal-home-hero-v3 {{
            min-height: 306px;
            display: grid;
            grid-template-columns: minmax(0, 1.55fr) minmax(285px, .72fr);
            gap: 2.2rem;
            align-items: center;
            padding: 2.75rem 3rem;
            position: relative;
            overflow: hidden;
            border-radius: 25px;
            background:
                radial-gradient(circle at 75% 12%, rgba(38,146,205,.26), transparent 24%),
                radial-gradient(circle at 98% 92%, rgba(255,255,255,.09), transparent 29%),
                linear-gradient(135deg, #005691 0%, #004B7E 47%, #003D66 100%);
            box-shadow: 0 20px 48px rgba(0,61,102,.16);
        }}

        .portal-home-hero-copy {{
            min-width: 0;
        }}

        .portal-home-kicker {{
            color: #C9E7F7 !important;
            font-size: .67rem;
            font-weight: 850;
            letter-spacing: .105em;
        }}

        .portal-home-title {{
            max-width: 790px;
            margin: .52rem 0 0;
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
            line-height: 1.58;
        }}

        .portal-home-hero-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: .42rem;
            margin-top: 1.15rem;
        }}

        .portal-home-hero-tags span {{
            padding: .34rem .59rem;
            border: 1px solid rgba(255,255,255,.19);
            border-radius: 999px;
            background: rgba(255,255,255,.08);
            color: #F3FAFD !important;
            font-size: .67rem;
            font-weight: 650;
        }}

        .portal-home-pulse {{
            padding: 1.25rem;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 20px;
            background: rgba(255,255,255,.10);
            backdrop-filter: blur(8px);
        }}

        .portal-home-pulse-label {{
            color: #C7E7F8 !important;
            font-size: .60rem;
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
            padding: .78rem;
            border-radius: 13px;
            background: rgba(0,35,60,.22);
        }}

        .portal-home-pulse-main strong {{
            display: block;
            color: #FFFFFF !important;
            font-size: 1.72rem;
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
            gap: .32rem;
            margin-top: .75rem;
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
            margin: 1.8rem auto .72rem;
            text-align: center;
        }}

        .portal-command-eyebrow,
        .portal-home-section-eyebrow {{
            color: var(--portal-primary) !important;
            font-size: .63rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        .portal-command-title {{
            margin-top: .15rem;
            color: var(--portal-text) !important;
            font-size: clamp(1.55rem, 2.8vw, 2.15rem);
            font-weight: 820;
            letter-spacing: -.035em;
        }}

        .portal-command-subtitle {{
            max-width: 680px;
            margin: .25rem auto 0;
            color: var(--portal-text-secondary) !important;
            font-size: .81rem;
        }}

        /* Pesquisa da Home: sem altura forçada no input interno.
           Isso evita o corte vertical do texto observado no Streamlit. */
        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) {{
            width: 100%;
            max-width: 1040px;
            margin: 0 auto .72rem;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"])
        div[data-baseweb="input"] {{
            min-height: 62px !important;
            display: flex !important;
            align-items: center !important;
            overflow: visible !important;
            border: 1px solid #C5D5DF !important;
            border-radius: 18px !important;
            background: var(--portal-surface) !important;
            box-shadow: 0 12px 30px rgba(13,38,56,.085) !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) input {{
            height: auto !important;
            min-height: 0 !important;
            padding: 18px 18px !important;
            margin: 0 !important;
            line-height: 1.3 !important;
            font-size: .96rem !important;
            color: #173447 !important;
            -webkit-text-fill-color: #173447 !important;
            overflow: visible !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"])
        div[data-baseweb="input"]:focus-within {{
            border-color: var(--portal-primary) !important;
            box-shadow:
                0 0 0 4px rgba(0,86,145,.09),
                0 14px 34px rgba(13,38,56,.10) !important;
        }}

        .portal-home-dock-label {{
            margin: .72rem 0 .36rem;
            color: var(--portal-text-muted) !important;
            font-size: .59rem;
            font-weight: 850;
            letter-spacing: .11em;
        }}

        .st-key-home_quick_actions {{
            max-width: 1040px;
            margin: 0 auto 1.15rem;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button {{
            min-height: 74px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 11px !important;
            padding: 0 18px !important;
            border: 1px solid #D4E1E8 !important;
            border-radius: 16px !important;
            background:
                linear-gradient(180deg, #FFFFFF 0%, #F7FBFD 100%) !important;
            color: #173447 !important;
            box-shadow: 0 5px 16px rgba(13,38,56,.05) !important;
            font-size: .86rem !important;
            font-weight: 760 !important;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button svg {{
            width: 23px !important;
            height: 23px !important;
            color: var(--portal-primary) !important;
            fill: var(--portal-primary) !important;
        }}

        .st-key-home_quick_actions [data-testid="stButton"] > button:hover {{
            transform: translateY(-2px);
            border-color: #9CC5DC !important;
            background: #F2F9FD !important;
            color: var(--portal-primary-dark) !important;
            box-shadow: 0 10px 24px rgba(0,86,145,.095) !important;
        }}

        .portal-home-section-head {{
            margin: 2.05rem 0 .8rem;
        }}

        .portal-home-section-title {{
            margin-top: .12rem;
            color: var(--portal-text) !important;
            font-size: 1.58rem;
            font-weight: 810;
            letter-spacing: -.035em;
        }}

        .portal-home-section-description {{
            margin-top: .18rem;
            color: var(--portal-text-secondary) !important;
            font-size: .81rem;
        }}

        .portal-feed-card {{
            padding: 1.05rem 1.1rem;
            margin-bottom: .68rem;
            border: 1px solid #D9E3E9;
            border-radius: 15px;
            background: var(--portal-surface);
            box-shadow: 0 3px 13px rgba(13,38,56,.045);
        }}

        .portal-feed-card-featured {{
            padding: 1.28rem;
            border-color: #BFD9E8;
            background: linear-gradient(145deg, #FFFFFF 0%, #F3F9FC 100%);
            box-shadow: 0 11px 27px rgba(0,86,145,.075);
        }}

        .portal-feed-card-alert {{
            border-left: 4px solid #B26B0B;
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
        .portal-feed-dot-notice {{ background: var(--portal-primary); }}

        .portal-feed-priority {{
            margin-left: auto;
            padding: .22rem .46rem;
            border-radius: 999px;
            background: #F2F5F7;
            color: #50616E !important;
            letter-spacing: 0;
        }}

        .portal-feed-title {{
            margin-top: .56rem;
            color: var(--portal-text) !important;
            font-size: 1.01rem;
            font-weight: 790;
            line-height: 1.3;
        }}

        .portal-feed-card-featured .portal-feed-title {{
            font-size: 1.22rem;
        }}

        .portal-feed-meta {{
            margin-top: .24rem;
            color: var(--portal-text-muted) !important;
            font-size: .71rem;
        }}

        .portal-feed-body {{
            margin-top: .58rem;
            color: var(--portal-text-secondary) !important;
            font-size: .81rem;
            line-height: 1.5;
        }}

        .portal-feed-footer {{
            margin-top: .7rem;
            padding-top: .58rem;
            border-top: 1px solid #EDF1F4;
            color: #6B7A86 !important;
            font-size: .68rem;
        }}

        .portal-empty-state {{
            display: flex;
            gap: .75rem;
            align-items: center;
            padding: 1.12rem;
            border: 1px dashed #C7D6DF;
            border-radius: 15px;
            background: rgba(255,255,255,.55);
        }}

        .portal-empty-icon {{
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #EAF6ED;
            color: #237A3B !important;
            font-weight: 850;
        }}

        .portal-empty-state strong {{
            display: block;
            color: var(--portal-text) !important;
            font-size: .85rem;
        }}

        .portal-empty-state span {{
            display: block;
            margin-top: .14rem;
            color: var(--portal-text-secondary) !important;
            font-size: .72rem;
        }}

        .portal-explore-card {{
            min-height: 136px;
            margin-top: .12rem;
            padding: 1.08rem 1.1rem;
            border: 1px solid #DAE4EA;
            border-bottom: 0;
            border-radius: 16px 16px 0 0;
            background: var(--portal-surface);
        }}

        .portal-explore-eyebrow {{
            color: var(--portal-primary) !important;
            font-size: .59rem;
            font-weight: 850;
            letter-spacing: .09em;
        }}

        .portal-explore-title {{
            margin-top: .48rem;
            color: var(--portal-text) !important;
            font-size: .94rem;
            font-weight: 790;
        }}

        .portal-explore-description {{
            margin-top: .28rem;
            color: var(--portal-text-secondary) !important;
            font-size: .74rem;
            line-height: 1.45;
        }}

        /* =========================================================
           COMPONENTES GERAIS DO STREAMLIT
           ========================================================= */

        [data-testid="stMetric"] {{
            padding: .9rem 1rem;
            border: 1px solid var(--portal-border);
            border-radius: var(--portal-radius-md);
            background: var(--portal-surface);
        }}

        [data-testid="stExpander"] {{
            border-color: var(--portal-border) !important;
            border-radius: 12px !important;
            background: var(--portal-surface) !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--portal-border);
            border-radius: 12px;
            overflow: hidden;
        }}

        [data-testid="stAlert"] {{
            border-radius: 12px !important;
        }}

        /* =========================================================
           RESPONSIVIDADE
           ========================================================= */

        @media (max-width: 1050px) {{
            .portal-home-hero-v3 {{
                grid-template-columns: 1fr;
            }}

            .portal-home-pulse {{
                display: none;
            }}
        }}

        @media (max-width: 900px) {{
            section[data-testid="stSidebar"] {{
                width: var(--portal-sidebar-open) !important;
                min-width: var(--portal-sidebar-open) !important;
                max-width: var(--portal-sidebar-open) !important;
            }}

            section[data-testid="stSidebar"] > div:first-child {{
                width: var(--portal-sidebar-open) !important;
                min-width: var(--portal-sidebar-open) !important;
                max-width: var(--portal-sidebar-open) !important;
            }}

            .portal-sidebar-brand-copy,
            .portal-sidebar-section-label,
            .portal-sidebar-account-label,
            .portal-sidebar-user-copy,
            .portal-sidebar-footer {{
                opacity: 1 !important;
            }}

            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
        }}

        @media (max-width: 700px) {{
            .portal-home-hero-v3 {{
                min-height: 0;
                padding: 1.6rem 1.25rem;
                border-radius: 19px;
            }}

            .portal-home-title {{
                font-size: 2rem;
            }}

            .portal-home-hero-tags {{
                display: none;
            }}

            .st-key-home_quick_actions [data-testid="stButton"] > button {{
                min-height: 58px !important;
                padding: 0 12px !important;
            }}
        }}

        /* =========================================================
           SIDEBAR HTML/SVG — rail real, alinhamento fixo
           ========================================================= */

        .portal-sidebar-shell {{
            width: 276px;
        }}

        .portal-sidebar-header {{
            width: 276px !important;
            height: 74px !important;
            padding: 0 0 0 15px !important;
            display: flex !important;
            align-items: center !important;
        }}

        .portal-sidebar-brand-icon {{
            width: 46px !important;
            min-width: 46px !important;
            height: 46px !important;
            flex: 0 0 46px !important;
        }}

        .portal-sidebar-nav {{
            width: 276px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 0 7px;
        }}

        .portal-sidebar-nav-item {{
            width: 260px;
            height: 44px;
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 0 14px;
            border: 1px solid transparent;
            border-radius: 11px;
            text-decoration: none !important;
            color: #425765 !important;
            background: transparent;
            overflow: hidden;
            white-space: nowrap;
            box-sizing: border-box;
            transition: background .08s linear, color .08s linear, border-color .08s linear;
        }}

        .portal-sidebar-nav-item:hover {{
            background: #EFF7FB;
            color: #003D66 !important;
        }}

        .portal-sidebar-nav-item.is-active {{
            background: #E2F1FA;
            color: #003D66 !important;
            border-color: #C7E1F0;
            box-shadow: inset 3px 0 0 #005691;
        }}

        .portal-sidebar-nav-icon {{
            width: 32px;
            min-width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: 0;
            color: currentColor !important;
        }}

        .portal-sidebar-nav-icon svg {{
            width: 21px;
            height: 21px;
            fill: none;
            stroke: currentColor;
            stroke-width: 1.8;
            stroke-linecap: round;
            stroke-linejoin: round;
            overflow: visible;
        }}

        .portal-sidebar-nav-text {{
            color: inherit !important;
            font-size: .84rem;
            font-weight: 680;
            opacity: 0;
            transition: opacity .04s linear;
        }}

        section[data-testid="stSidebar"]:hover .portal-sidebar-nav-text,
        section[data-testid="stSidebar"]:focus-within .portal-sidebar-nav-text {{
            opacity: 1;
        }}

        /* A rail tem 76px: 7px margem + 46px área visual + respiro.
           Assim ícone da marca, navegação e avatar compartilham o mesmo eixo. */
        .portal-sidebar-nav-item {{
            padding-left: 12px;
        }}

        .portal-sidebar-user-compact {{
            margin-left: 7px !important;
            padding-left: 8px !important;
        }}

        .portal-sidebar-avatar,
        .portal-sidebar-avatar-fallback {{
            width: 44px !important;
            min-width: 44px !important;
            height: 44px !important;
            flex: 0 0 44px !important;
        }}

        section[data-testid="stSidebar"] .stButton {{
            width: 276px !important;
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            width: 260px !important;
            margin-left: 7px !important;
        }}

        /* =========================================================
           HOME — atalhos e CTAs sem aparência de botão padrão
           ========================================================= */

        .portal-home-quick-wrap {{
            max-width: 1040px;
            margin: 0 auto 1.25rem;
        }}

        .portal-home-quick-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: .62rem;
        }}

        .portal-quick-card {{
            min-width: 0;
            min-height: 84px;
            display: grid;
            grid-template-columns: 38px minmax(0, 1fr) 18px;
            align-items: center;
            gap: .7rem;
            padding: .85rem .9rem;
            border: 1px solid #D4E1E8;
            border-radius: 16px;
            background: linear-gradient(180deg, #FFFFFF 0%, #F7FBFD 100%);
            box-shadow: 0 5px 16px rgba(13,38,56,.05);
            color: #173447 !important;
            text-decoration: none !important;
            transition:
                transform .11s ease,
                border-color .11s ease,
                box-shadow .11s ease,
                background .11s ease;
        }}

        .portal-quick-card:hover {{
            transform: translateY(-2px);
            border-color: #99C4DD;
            background: #F1F9FD;
            box-shadow: 0 11px 24px rgba(0,86,145,.10);
            color: #003D66 !important;
        }}

        .portal-quick-icon {{
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 11px;
            background: #E5F2F9;
            color: #005691 !important;
        }}

        .portal-quick-icon svg {{
            width: 20px;
            height: 20px;
            fill: none;
            stroke: currentColor;
            stroke-width: 1.8;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}

        .portal-quick-copy {{
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: .13rem;
        }}

        .portal-quick-copy strong {{
            color: inherit !important;
            font-size: .80rem;
            font-weight: 790;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .portal-quick-copy small {{
            color: #71818D !important;
            font-size: .64rem;
            line-height: 1.25;
        }}

        .portal-quick-arrow {{
            color: #6E8796 !important;
            font-size: 1rem;
        }}

        .portal-section-link {{
            width: fit-content;
            display: inline-flex;
            align-items: center;
            gap: .55rem;
            margin-top: .25rem;
            padding: .58rem .82rem;
            border: 1px solid #CCDCE5;
            border-radius: 11px;
            background: #FFFFFF;
            color: #17425D !important;
            text-decoration: none !important;
            font-size: .76rem;
            font-weight: 740;
            transition: background .1s ease, border-color .1s ease, transform .1s ease;
        }}

        .portal-section-link:hover {{
            transform: translateY(-1px);
            border-color: #9EC6DD;
            background: #F2F9FD;
            color: #003D66 !important;
        }}

        .portal-section-link span {{
            color: inherit !important;
            font-size: .92rem;
        }}

        .portal-explore-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .85rem;
        }}

        .portal-explore-link {{
            min-height: 164px;
            display: flex;
            flex-direction: column;
            padding: 1.15rem 1.18rem 1rem;
            border: 1px solid #D8E3E9;
            border-radius: 16px;
            background: #FFFFFF;
            color: #17212B !important;
            text-decoration: none !important;
            box-shadow: 0 4px 14px rgba(13,38,56,.045);
            transition:
                transform .11s ease,
                border-color .11s ease,
                box-shadow .11s ease;
        }}

        .portal-explore-link:hover {{
            transform: translateY(-2px);
            border-color: #A4CADF;
            box-shadow: 0 11px 24px rgba(0,86,145,.085);
        }}

        .portal-explore-link .portal-explore-title {{
            color: #17212B !important;
        }}

        .portal-explore-action {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: auto;
            padding-top: .9rem;
            color: #005691 !important;
            font-size: .73rem;
            font-weight: 780;
        }}

        .portal-explore-action span {{
            color: inherit !important;
            font-size: 1rem;
        }}

        @media (max-width: 1050px) {{
            .portal-home-quick-grid {{
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 760px) {{
            .portal-home-quick-grid,
            .portal-explore-grid {{
                grid-template-columns: 1fr;
            }}
        }}

    </style>
    """

    st.html(css)
