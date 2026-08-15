"""Cliente Supabase compartilhado (usado por auth.py e storage.py)."""
from __future__ import annotations

import streamlit as st


def supabase_configurado() -> bool:
    try:
        return "supabase" in st.secrets and bool(st.secrets["supabase"].get("url"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def get_client():
    from supabase import create_client

    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)