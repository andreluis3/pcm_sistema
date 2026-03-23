# Centralized UI style constants for PCM Thermal Manager

FONT_SMALL = ("Segoe UI", 14)
FONT_NORMAL = ("Segoe UI", 15)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 22, "bold")
FONT_TEMP = ("Segoe UI", 32, "bold")

WIDGET_HEIGHT_SMALL = 32
WIDGET_HEIGHT_NORMAL = 38
WIDGET_HEIGHT_LARGE = 44

PAD_SMALL = 8
PAD_NORMAL = 12
PAD_LARGE = 18

# Legacy aliases (keep for backward compatibility)
FONT_SUBTITLE = FONT_TITLE
FONT_SIDEBAR = FONT_NORMAL
FONT_MONO_LARGE = FONT_TEMP

ENTRY_HEIGHT = WIDGET_HEIGHT_NORMAL
BUTTON_HEIGHT = WIDGET_HEIGHT_LARGE
SIDEBAR_BUTTON_HEIGHT = WIDGET_HEIGHT_LARGE

SECTION_PAD_X = PAD_LARGE
SECTION_PAD_Y = PAD_NORMAL

# Theme colors (use across UI for consistent palette)
THEME_COLORS = {
    "bg": "#0D1117",
    "card": "#161B22",
    "card_soft": "#1B222C",
    "border": "#202734",
    "shadow": "#0A0F14",
    "accent": "#8B93A5",
    "accent_strong": "#7A879B",
    "accent_soft": "#18212B",
    "line_avg": "#C5D1DE",
    "text_primary": "#E5E7EB",
    "text_secondary": "#9AA0AB",
    "text_muted": "#8B93A5",
    "white": "#E5E7EB",
}
