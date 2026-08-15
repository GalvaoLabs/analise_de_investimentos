"""
Persistência de dados de cada usuário: carteira de ativos e metas
financeiras.

Usa o Supabase (Postgres gerenciado, plano gratuito) quando configurado em
`.streamlit/secrets.toml`. Sem essa configuração, cai para arquivos JSON
locais por usuário — útil para desenvolvimento, mas **não persistente** no
Streamlit Community Cloud, cujo disco é efêmero e reseta a cada redeploy.

Configuração necessária em .streamlit/secrets.toml:

    [supabase]
    url = "https://SEU-PROJETO.supabase.co"
    key = "SUA_ANON_KEY"

Crie as tabelas no Supabase (SQL Editor) com:

    create table carteiras (
        user_id text primary key,
        dados jsonb not null,
        atualizado_em timestamptz default now()
    );

    create table metas (
        user_id text primary key,
        dados jsonb not null,
        atualizado_em timestamptz default now()
    );
"""
from __future__ import annotations

import json
import os

import pandas as pd
import streamlit as st

from supabase_client import get_client, supabase_configurado

LOCAL_DIR = "dados_locais"


def _sanitizar(nome: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in nome)


def _carregar(tabela: str, user_id: str):
    """Carrega os dados brutos (JSON) do usuário em uma tabela. None se não houver nada."""
    if supabase_configurado():
        try:
            sb = get_client()
            res = sb.table(tabela).select("dados").eq("user_id", user_id).execute()
            if res.data:
                return res.data[0]["dados"]
        except Exception as e:
            st.warning(f"Não foi possível carregar seus dados salvos ({tabela}) do Supabase: {e}")
        return None

    os.makedirs(LOCAL_DIR, exist_ok=True)
    caminho = os.path.join(LOCAL_DIR, f"{tabela}_{_sanitizar(user_id)}.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _salvar(tabela: str, user_id: str, dados) -> bool:
    """Salva (upsert) os dados do usuário em uma tabela. Retorna True se OK."""
    if supabase_configurado():
        try:
            sb = get_client()
            sb.table(tabela).upsert({"user_id": user_id, "dados": dados}).execute()
            return True
        except Exception as e:
            st.error(f"Não foi possível salvar seus dados ({tabela}) no Supabase: {e}")
            return False

    try:
        os.makedirs(LOCAL_DIR, exist_ok=True)
        caminho = os.path.join(LOCAL_DIR, f"{tabela}_{_sanitizar(user_id)}.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Não foi possível salvar seus dados ({tabela}) localmente: {e}")
        return False


# ==========================================
# CARTEIRA
# ==========================================
def carregar_carteira(user_id: str) -> pd.DataFrame | None:
    """Carrega a carteira salva do usuário. Retorna None se não houver nada salvo."""
    dados = _carregar("carteiras", user_id)
    if not dados:
        return None
    try:
        return pd.DataFrame(dados)
    except Exception:
        return None


def salvar_carteira(user_id: str, df: pd.DataFrame) -> bool:
    """Salva a carteira (tabela editável de entrada) do usuário. Retorna True se OK."""
    try:
        registros = json.loads(df.to_json(orient="records"))
    except Exception as e:
        st.error(f"Não foi possível preparar a carteira para salvar: {e}")
        return False
    return _salvar("carteiras", user_id, registros)


# ==========================================
# METAS FINANCEIRAS
# ==========================================
def carregar_meta(user_id: str) -> dict | None:
    """Carrega a meta financeira salva do usuário. Retorna None se não houver nada salvo."""
    dados = _carregar("metas", user_id)
    return dados if isinstance(dados, dict) else None


def salvar_meta(user_id: str, meta: dict) -> bool:
    """Salva a meta financeira do usuário. Retorna True se OK."""
    return _salvar("metas", user_id, meta)

