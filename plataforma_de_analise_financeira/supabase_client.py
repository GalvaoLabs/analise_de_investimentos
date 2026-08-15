"""Cliente Supabase compartilhado (usado por auth.py e storage.py)."""
from __future__ import annotations

import streamlit as st


def _url_bruta() -> str:
    try:
        return str(st.secrets["supabase"]["url"]).strip()
    except Exception:
        return ""


def supabase_configurado() -> bool:
    try:
        return "supabase" in st.secrets and bool(_url_bruta()) and bool(st.secrets["supabase"].get("key"))
    except Exception:
        return False


def _sanitizar_url(url: str) -> str:
    """Remove espaços e barra(s) finais — 'https://x.supabase.co/' quebra o
    cliente do Supabase (gera caminhos com barra dupla, ex: '.co//auth/v1/otp',
    que o servidor rejeita com 'Invalid path specified in request URL')."""
    return url.strip().rstrip("/")


@st.cache_resource(show_spinner=False)
def get_client():
    from supabase import create_client

    url = _sanitizar_url(_url_bruta())
    key = str(st.secrets["supabase"]["key"]).strip()

    if not url.startswith("http"):
        st.error(
            f"URL do Supabase inválida em `secrets.toml`: `{url or '(vazia)'}`. "
            "Deve começar com `https://` e vir de Project Settings → API → "
            "Project URL, **sem barra `/` no final**. Corrija e recarregue a página."
        )
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"Não foi possível conectar ao Supabase: {e}")
        return None

