from __future__ import annotations

import pandas as pd
import streamlit as st

from core.credentials_service import (
    decrypt_password,
    format_timestamp,
    get_credential_history,
    get_portal_credentials,
    log_password_reveal,
)


def _safe(row: pd.Series, column: str) -> str:
    if column not in row.index:
        return ""
    value = row[column]
    if pd.isna(value):
        return ""
    return str(value).strip()


def _as_bool(value: object) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"true", "1", "sim", "yes"}


def _render_credential(
    *,
    credential: pd.Series,
    portal_id: str,
    portal_name: str,
) -> None:
    credential_id = _safe(credential, "id")
    identification = _safe(credential, "identificacao") or "Acesso principal"
    login = _safe(credential, "login")
    hint = _safe(credential, "dica_acesso")
    observations = _safe(credential, "observacoes")
    password_rule = _safe(credential, "regra_senha_observacao")
    blocked_count = credential.get("quantidade_senhas_bloqueadas", 0)
    changed_at = credential.get("senha_alterada_em") or credential.get("updated_at")

    st.markdown(f"**🔐 {identification}**")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.caption("LOGIN / USUÁRIO")
        if login:
            st.code(login, language=None)
        else:
            st.write("Não informado")

    reveal_key = f"show_credential_{credential_id}"
    with c2:
        st.caption("SENHA")
        if not st.session_state.get(reveal_key, False):
            if st.button(
                "👁 Exibir senha",
                key=f"reveal_{credential_id}",
                use_container_width=True,
            ):
                result = decrypt_password(_safe(credential, "senha_criptografada"))

                if result.status == "ok" and result.value:
                    st.session_state[reveal_key] = True
                    st.session_state[f"credential_value_{credential_id}"] = result.value

                    try:
                        log_password_reveal(
                            credential_id=credential_id,
                            portal_id=portal_id,
                            portal_name=portal_name,
                        )
                    except Exception:
                        # Falha de auditoria não deve expor detalhes técnicos,
                        # mas também não deve registrar conteúdo sensível localmente.
                        pass

                    st.rerun()

                elif result.status == "test_data":
                    st.info(
                        "Esta é uma credencial fictícia da massa de testes. "
                        "Nenhuma senha real foi cadastrada."
                    )
                elif result.status == "missing_key":
                    st.warning(
                        "A criptografia das credenciais ainda não está configurada "
                        "neste ambiente."
                    )
                else:
                    st.warning(
                        "Não foi possível disponibilizar esta senha com segurança."
                    )
        else:
            password = st.session_state.get(f"credential_value_{credential_id}", "")
            if password:
                # st.code fornece cópia nativa no canto do bloco.
                st.code(password, language=None)

            if st.button(
                "Ocultar senha",
                key=f"hide_{credential_id}",
                use_container_width=True,
            ):
                st.session_state.pop(reveal_key, None)
                st.session_state.pop(f"credential_value_{credential_id}", None)
                st.rerun()

    metadata = []
    if changed_at:
        metadata.append(f"Atualizada em {format_timestamp(changed_at)}")
    if blocked_count not in (None, "", 0, "0"):
        metadata.append(f"{blocked_count} senha(s) anterior(es) bloqueada(s)")
    if metadata:
        st.caption(" • ".join(metadata))

    if hint:
        st.info(hint, icon="💡")

    if password_rule:
        st.caption(f"**Regra de senha:** {password_rule}")

    if observations:
        st.caption(observations)

    profile = st.session_state.get("auth_profile") or {}
    if profile.get("role") == "admin":
        history = get_credential_history(credential_id)
        if not history.empty:
            with st.expander(f"Histórico da credencial ({len(history)})"):
                for _, item in history.iterrows():
                    who = _safe(item, "alterado_por") or "Usuário não identificado"
                    reason = _safe(item, "motivo_alteracao") or "Sem motivo informado"
                    changed = format_timestamp(item.get("alterado_em"))
                    st.write(f"**{changed}** — {reason}")
                    st.caption(
                        "Registro histórico preservado. "
                        "A senha anterior não é exibida nesta tela."
                    )


def render_portal_card(
    portal: pd.Series,
    *,
    operator_name: str = "",
    plan_name: str = "",
    show_credentials: bool = True,
    key_prefix: str = "portal",
) -> None:
    portal_id = _safe(portal, "id")
    portal_name = _safe(portal, "nome") or "Portal sem nome"
    portal_type = _safe(portal, "tipo")
    url = _safe(portal, "url")
    instructions = _safe(portal, "instrucao_acesso")
    tip = _safe(portal, "dica_geral_acesso")
    observations = _safe(portal, "observacoes")
    requires_login = _as_bool(portal.get("exige_login", False))

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1.25])

        with top_left:
            st.markdown(f"### 🌐 {portal_name}")
            context = [value for value in [operator_name, plan_name, portal_type] if value]
            if context:
                st.caption(" • ".join(context))

        with top_right:
            if url:
                st.link_button(
                    "Abrir portal ↗",
                    url,
                    use_container_width=True,
                )

        status_text = "Exige autenticação" if requires_login else "Acesso sem login"
        st.caption(f"🔒 {status_text}")

        if instructions:
            st.markdown("**Como acessar**")
            st.write(instructions)

        if tip:
            st.info(tip, icon="💡")

        if observations:
            st.caption(observations)

        if not show_credentials or not requires_login:
            return

        try:
            credentials = get_portal_credentials(portal_id)
        except Exception:
            st.warning(
                "Não foi possível carregar as credenciais deste portal agora."
            )
            return

        st.divider()
        st.markdown("#### Credenciais de acesso")

        if credentials.empty:
            st.info(
                "Este portal exige autenticação, mas ainda não há credencial "
                "ativa cadastrada no Portal Comercial."
            )
            return

        for index, (_, credential) in enumerate(credentials.iterrows()):
            if index > 0:
                st.divider()

            _render_credential(
                credential=credential,
                portal_id=portal_id,
                portal_name=portal_name,
            )
