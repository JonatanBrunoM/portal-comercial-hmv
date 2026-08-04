import html

import streamlit as st


def render_metric_card(
    title: str,
    value: str | int,
    description: str,
    icon: str,
) -> None:
    """
    Renderiza um card resumido para indicadores da página inicial.
    """

    safe_title = html.escape(str(title))
    safe_value = html.escape(str(value))
    safe_description = html.escape(str(description))
    safe_icon = html.escape(icon)

    st.markdown(
        f"""
        <article style="
            min-height: 160px;
            padding: 1.25rem;
            background-color: #FFFFFF;
            border: 1px solid #DCE3E8;
            border-radius: 14px;
            box-shadow: 0 4px 16px rgba(0, 61, 102, 0.045);
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
            ">
                <div style="
                    color: #5B6773;
                    font-size: 0.82rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                ">
                    {safe_title}
                </div>

                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 38px;
                    height: 38px;
                    border-radius: 10px;
                    background-color: #EAF4FA;
                    font-size: 1.15rem;
                ">
                    {safe_icon}
                </div>
            </div>

            <div style="
                margin-top: 1rem;
                color: #17212B;
                font-size: 1.85rem;
                font-weight: 750;
            ">
                {safe_value}
            </div>

            <div style="
                margin-top: 0.4rem;
                color: #5B6773;
                font-size: 0.88rem;
                line-height: 1.45;
            ">
                {safe_description}
            </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_module_card(
    title: str,
    description: str,
    icon: str,
    button_key: str,
) -> bool:
    """
    Renderiza um card de acesso rápido.

    Retorna:
        True quando o botão do card é acionado.
    """

    safe_title = html.escape(title)
    safe_description = html.escape(description)
    safe_icon = html.escape(icon)

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: flex-start;
                gap: 0.9rem;
                min-height: 92px;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 44px;
                    height: 44px;
                    border-radius: 12px;
                    background-color: #EAF4FA;
                    font-size: 1.3rem;
                ">
                    {safe_icon}
                </div>

                <div>
                    <div style="
                        color: #17212B;
                        font-size: 1rem;
                        font-weight: 700;
                    ">
                        {safe_title}
                    </div>

                    <div style="
                        margin-top: 0.35rem;
                        color: #5B6773;
                        font-size: 0.88rem;
                        line-height: 1.45;
                    ">
                        {safe_description}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return st.button(
            "Acessar",
            key=button_key,
            use_container_width=True,
        )
