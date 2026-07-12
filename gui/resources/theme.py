"""
theme.py — Design tokens et gestion des thèmes pour l'interface QuantL.

Centralise toutes les couleurs et styles de l'application afin que
l'ensemble des widgets (Qt Style Sheets + graphiques Matplotlib) restent
visuellement cohérents, que l'on soit en thème sombre ou clair.
"""
import os

_RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Palettes de couleurs "sémantiques" (utilisées pour Matplotlib et pour
# construire dynamiquement certains styles Python qui ne peuvent pas être
# exprimés en QSS pur, ex: le canevas du circuit ou les graphes).
# --------------------------------------------------------------------------
PALETTES = {
    "dark": {
        "bg_primary":   "#1a1b23",
        "bg_secondary": "#20222d",
        "bg_tertiary":  "#282a38",
        "bg_elevated":  "#2f3241",
        "border":       "#3a3d4d",
        "border_soft":  "#31333f",
        "text_primary": "#e7e7f1",
        "text_secondary": "#9799ab",
        "text_muted":   "#6c6f82",
        "accent":       "#7aa2f7",
        "accent_hover": "#5d84e0",
        "accent_text":  "#0d1117",
        "success":      "#9ece6a",
        "warning":      "#e0af68",
        "danger":       "#f7768e",
        "info":         "#7dcfff",
    },
    "light": {
        "bg_primary":   "#f6f7fb",
        "bg_secondary": "#ffffff",
        "bg_tertiary":  "#eef0f5",
        "bg_elevated":  "#ffffff",
        "border":       "#dce0ea",
        "border_soft":  "#e7eaf1",
        "text_primary": "#1f2430",
        "text_secondary": "#5b6070",
        "text_muted":   "#8992a6",
        "accent":       "#3b6fe0",
        "accent_hover": "#2f5bc0",
        "accent_text":  "#ffffff",
        "success":      "#1f8a4c",
        "warning":      "#b5760f",
        "danger":       "#c53030",
        "info":         "#0f7fb8",
    },
}

# Palette dédiée aux graphiques Matplotlib (circuit + histogrammes)
MPL_PALETTES = {
    "dark": {
        "figure_bg": "#20222d",
        "axes_bg":   "#20222d",
        "text":      "#e7e7f1",
        "muted":     "#9799ab",
        "grid":      "#3a3d4d",
        "accent":    "#7aa2f7",
        "success":   "#9ece6a",
        "danger":    "#f7768e",
    },
    "light": {
        "figure_bg": "#ffffff",
        "axes_bg":   "#ffffff",
        "text":      "#1f2430",
        "muted":     "#5b6070",
        "grid":      "#e2e5ec",
        "accent":    "#3b6fe0",
        "success":   "#1f8a4c",
        "danger":    "#c53030",
    },
}

FONT_FAMILY_UI = "Segoe UI, Ubuntu, Cantarell, Arial, sans-serif"
FONT_FAMILY_MONO = "JetBrains Mono, Cascadia Code, Consolas, Courier New, monospace"


def palette(theme_name: str) -> dict:
    return PALETTES.get(theme_name, PALETTES["dark"])


def mpl_palette(theme_name: str) -> dict:
    return MPL_PALETTES.get(theme_name, MPL_PALETTES["dark"])


def stylesheet(theme_name: str) -> str:
    """Charge la feuille de style (.qss) associée au thème demandé."""
    filename = "dark.qss" if theme_name != "light" else "light.qss"
    path = os.path.join(_RESOURCES_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""
