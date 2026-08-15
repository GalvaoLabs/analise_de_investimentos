from __future__ import annotations
import base64
from datetime import datetime, timedelta
import streamlit as st
from supabase_client import get_client, supabase_configurado

try:
    import extra_streamlit_components as stx
    COOKIES_DISPONIVEL = True
except ImportError:
    stx = None
    COOKIES_DISPONIVEL = False

COOKIE_NOME = "investdash_refresh_token"
COOKIE_DIAS_VALIDADE = 30

def carregar_imagem_base64(caminho):
    with open(caminho, "rb") as arquivo:
        dados = arquivo.read()
    return base64.b64encode(dados).decode("utf-8")

def _get_cookie_manager():
    if not COOKIES_DISPONIVEL:
        return None
    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = stx.CookieManager(key="investdash_cookie_manager")
    return st.session_state["_cookie_manager"]

def _salvar_cookie_sessao(cookie_manager, refresh_token: str) -> None:
    if cookie_manager is None or not refresh_token:
        return
    try:
        cookie_manager.set(
            COOKIE_NOME,
            refresh_token,
            expires_at=datetime.now() + timedelta(days=COOKIE_DIAS_VALIDADE),
            key="set_investdash_refresh_token",
        )
    except Exception:
        pass

def _apagar_cookie_sessao(cookie_manager) -> None:
    if cookie_manager is None:
        return
    try:
        cookie_manager.delete(COOKIE_NOME, key="del_investdash_refresh_token")
    except Exception:
        pass

def _sessao_ativa() -> dict | None:
    return st.session_state.get("supabase_user")

def _tentar_restaurar_sessao(cookie_manager) -> None:
    if cookie_manager is None or st.session_state.get("_sessao_restaurada"):
        return

    cookies = cookie_manager.get_all()
    if cookies is None:
        st.stop()

    st.session_state["_sessao_restaurada"] = True
    refresh_token = cookies.get(COOKIE_NOME)
    if not refresh_token:
        return

    try:
        client = get_client()
        res = client.auth.refresh_session(refresh_token)
        if res and res.user and res.session:
            st.session_state["supabase_user"] = {"email": res.user.email, "id": res.user.id}
            _salvar_cookie_sessao(cookie_manager, res.session.refresh_token)
            st.rerun()
    except Exception:
        _apagar_cookie_sessao(cookie_manager)

def exigir_login() -> None:
    if not supabase_configurado():
        st.error(
            "Login ainda não configurado. Preencha `url` e `key` em "
            "`.streamlit/secrets.toml` (veja `secrets.toml.example`) e ajuste os "
            "templates de e-mail no painel do Supabase."
        )
        st.stop()

    cookie_manager = _get_cookie_manager()
    _tentar_restaurar_sessao(cookie_manager)

    if _sessao_ativa():
        return

    # Carrega a imagem para o HTML
    logo_base64 = carregar_imagem_base64("logo.png")

    st.markdown(
        f"""
        <div style="max-width: 440px; margin: 10vh auto 24px auto; text-align: center;">
            <img src="data:image/png;base64,{logo_base64}" style="max-width: 150px; margin-bottom: 16px;">
            <h1 style="border-bottom:none; margin-bottom: 6px;">Plataforma de Análise Financeira</h1>
            <p style="color: var(--text-secondary);">
                Entre com seu e-mail para acessar sua carteira pessoal, salva com segurança na nuvem.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    client = get_client()
    if client is None:
        st.stop()
    etapa = st.session_state.get("login_etapa", "email")

    col = st.columns([1, 1.3, 1])[1]
    with col:
        if etapa == "email":
            email = st.text_input("Seu e-mail", key="login_email_input", placeholder="voce@exemplo.com")
            if st.button("Enviar código de verificação", type="primary", use_container_width=True):
                if not email or "@" not in email:
                    st.error("Digite um e-mail válido.")
                else:
                    try:
                        client.auth.sign_in_with_otp({"email": email, "options": {"should_create_user": True}})
                        st.session_state["login_etapa"] = "codigo"
                        st.session_state["login_email_enviado"] = email
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não foi possível enviar o e-mail: {e}")

        elif etapa == "codigo":
            email = st.session_state.get("login_email_enviado", "")
            st.caption(f"Enviamos um código de 6 dígitos para **{email}**. Confira também o spam.")
            codigo = st.text_input("Código de verificação", key="login_codigo_input", max_chars=6)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirmar", type="primary", use_container_width=True):
                    try:
                        res = client.auth.verify_otp(
                            {"email": email, "token": codigo.strip(), "type": "email"}
                        )
                        if res and res.user:
                            st.session_state["supabase_user"] = {"email": res.user.email, "id": res.user.id}
                            if res.session and res.session.refresh_token:
                                _salvar_cookie_sessao(cookie_manager, res.session.refresh_token)
                            st.session_state.pop("login_etapa", None)
                            st.session_state.pop("login_email_enviado", None)
                            st.rerun()
                        else:
                            st.error("Código inválido ou expirado. Tente reenviar.")
                    except Exception as e:
                        st.error(f"Código inválido ou expirado: {e}")
            with c2:
                if st.button("Usar outro e-mail", use_container_width=True):
                    st.session_state["login_etapa"] = "email"
                    st.rerun()

    if COOKIES_DISPONIVEL:
        st.caption(f"✅ Depois de confirmado, seu login fica salvo por {COOKIE_DIAS_VALIDADE} dias.")
    st.stop()

def render_user_badge() -> None:
    usuario = _sessao_ativa()
    if not usuario:
        return
    with st.sidebar:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"👤 **{usuario['email']}**")
        with col2:
            if st.button("Sair", use_container_width=True):
                try:
                    get_client().auth.sign_out()
                except Exception:
                    pass
                _apagar_cookie_sessao(_get_cookie_manager())
                st.session_state.pop("supabase_user", None)
                st.session_state.pop("_sessao_restaurada", None)
                st.rerun()
        st.markdown("---")

def usuario_id() -> str:
    usuario = _sessao_ativa()
    return usuario["email"] if usuario else "anonimo"

