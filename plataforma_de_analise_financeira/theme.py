"""
Módulo de temas: paletas de cor de destaque + modo claro/escuro.

Como o Streamlit renderiza `st.dataframe` / `st.data_editor` em um canvas
que ignora CSS, o fundo desses componentes segue o tema definido em
`.streamlit/config.toml` (fixo, escuro). O que este módulo controla
dinamicamente é a cor de destaque (accent) e o modo claro/escuro de todo o
restante da interface (cards, botões, badges, textos, gráficos).
"""
from __future__ import annotations

PALETAS: dict[str, dict[str, str]] = {
    "Oceano": {"accent": "#38BDF8", "accent_strong": "#0284C7", "accent_hover": "#0369A1"},
    "Esmeralda": {"accent": "#34D399", "accent_strong": "#059669", "accent_hover": "#047857"},
    "Ametista": {"accent": "#A78BFA", "accent_strong": "#7C3AED", "accent_hover": "#6D28D9"},
    "Solar": {"accent": "#FBBF24", "accent_strong": "#D97706", "accent_hover": "#B45309"},
    "Rubi": {"accent": "#FB7185", "accent_strong": "#E11D48", "accent_hover": "#BE123C"},
    "Grafite": {"accent": "#94A3B8", "accent_strong": "#475569", "accent_hover": "#334155"},
}

MODOS: dict[str, dict[str, str]] = {
    "Escuro": {
        "bg_gradient_start": "#10141F",
        "bg_app": "#0B0E14",
        "bg_panel": "#111622",
        "bg_panel_2": "#0D1119",
        "bg_input": "#1E293B",
        "border_color": "#1E293B",
        "border_color_strong": "#334155",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "img_filter": "saturate(0.9) brightness(0.85)",
    },
    "Claro": {
        "bg_gradient_start": "#EFF3F9",
        "bg_app": "#F5F7FB",
        "bg_panel": "#FFFFFF",
        "bg_panel_2": "#F1F5F9",
        "bg_input": "#F1F5F9",
        "border_color": "#E2E8F0",
        "border_color_strong": "#CBD5E1",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#64748B",
        "img_filter": "saturate(1) brightness(1)",
    },
}

DEFAULT_PALETA = "Oceano"
DEFAULT_MODO = "Escuro"


def build_theme_css(
    paleta_nome: str,
    modo_nome: str,
    accent_custom: str | None = None,
    accent_strong_custom: str | None = None,
) -> str:
    """Gera um bloco CSS que sobrescreve as variáveis de :root definidas em style.css.

    Injetado *depois* do style.css, sobrepõe os valores padrão por ordem de
    cascata (mesma especificidade, declaração posterior prevalece).
    """
    paleta = PALETAS.get(paleta_nome, PALETAS[DEFAULT_PALETA])
    modo = MODOS.get(modo_nome, MODOS[DEFAULT_MODO])

    accent = accent_custom or paleta["accent"]
    accent_strong = accent_strong_custom or paleta["accent_strong"]
    accent_hover = paleta["accent_hover"] if not accent_strong_custom else _escurecer(accent_strong_custom)

    return f"""
    :root {{
        --accent: {accent};
        --accent-strong: {accent_strong};
        --accent-strong-hover: {accent_hover};
        --bg-gradient-start: {modo["bg_gradient_start"]};
        --bg-app: {modo["bg_app"]};
        --bg-panel: {modo["bg_panel"]};
        --bg-panel-2: {modo["bg_panel_2"]};
        --bg-input: {modo["bg_input"]};
        --border-color: {modo["border_color"]};
        --border-color-strong: {modo["border_color_strong"]};
        --text-primary: {modo["text_primary"]};
        --text-secondary: {modo["text_secondary"]};
        --text-muted: {modo["text_muted"]};
    }}
    .card-image {{
        filter: {modo["img_filter"]};
    }}
    """


def _escurecer(hex_color: str, fator: float = 0.82) -> str:
    """Escurece uma cor hex por um fator (usado para o hover de cor personalizada)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"#{hex_color}"
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, int(c * fator))) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def get_active_accents(
    paleta_nome: str, accent_custom: str | None = None, accent_strong_custom: str | None = None
) -> dict[str, str]:
    """Retorna as cores de destaque ativas, para uso direto nos gráficos Plotly."""
    paleta = PALETAS.get(paleta_nome, PALETAS[DEFAULT_PALETA])
    return {
        "accent": accent_custom or paleta["accent"],
        "accent_strong": accent_strong_custom or paleta["accent_strong"],
    }