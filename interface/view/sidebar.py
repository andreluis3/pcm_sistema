import customtkinter as ctk

from .widgets import BotaoSidebar
from ui_styles import (
    FONT_NORMAL,
    FONT_SMALL,
    FONT_TITLE,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
    button_style,
)


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, ao_selecionar, user_name="Usuário") -> None:
        super().__init__(parent, fg_color=THEME_COLORS["card"])

       
        self.expanded_width = 230
        self.collapsed_width = 75

        self.is_expanded = True

        self.configure(width=self.expanded_width)


        self.grid_rowconfigure(9, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.grid_propagate(False)
        self.pack_propagate(False)

        # =========================
        # BOTÃO TOGGLE
        # =========================
        self.toggle_btn = ctk.CTkButton(
            self,
            text="☰",
            width=48,
            height=48,
            **button_style("neutral"),
            font=FONT_TITLE,
            command=self.toggle,
        )

        self.toggle_btn.grid(
            row=0,
            column=0,
            padx=PAD_LARGE,
            pady=PAD_NORMAL,
            sticky="ew"
        )

        # =========================
        # MENU ITEMS
        # =========================
        self.menu_buttons = []

        items = [
            ("dashboard", "📊", "Dashboard"),
            ("sensor", "🌡️", "Sensor"),
            ("materiais", "🧪", "Materiais"),
            ("experimentos", "🔬", "Experimentos"),
            ("calculos", "🧮", "Cálculos Térmicos"),
            ("pcm", "🧊", "PCM Calculo Log"),
            ("banco", "🗄️", "Banco de Dados"),
            ("exportar", "📤", "Exportar Dados"),
        ]

        for idx, (key, icon, label) in enumerate(items, start=1):

            full_text = f"{icon}  {label}"

            btn = BotaoSidebar(
                self,
                full_text,
                comando=lambda k=key: self._safe_select(ao_selecionar, k)
            )

            # guardamos dados originais
            btn._page_key = key
            btn._icon = icon
            btn._label = label
            btn._full_text = full_text

            btn.grid(
                row=idx,
                column=0,
                padx=PAD_NORMAL,
                pady=PAD_SMALL,
                sticky="ew"
            )

            self.menu_buttons.append(btn)

        # =========================
        # PERFIL
        # =========================
        self.profile = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS["card_soft"],
            corner_radius=14,
            border_width=1,
            border_color=THEME_COLORS["border"]
        )

        self.profile.grid(
            row=9,
            column=0,
            padx=PAD_NORMAL,
            pady=PAD_LARGE,
            sticky="ew"
        )

        self.profile.grid_columnconfigure(1, weight=1)

        self.avatar = ctk.CTkLabel(
            self.profile,
            text="👤",
            font=FONT_TITLE
        )

        self.avatar.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=12,
            pady=12
        )

        self.user_name = ctk.CTkLabel(
            self.profile,
            text=user_name,
            font=FONT_NORMAL
        )

        self.user_name.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 12),
            pady=(12, 0)
        )

        self.user_role = ctk.CTkLabel(
            self.profile,
            text="Operador",
            font=FONT_SMALL
        )

        self.user_role.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 12),
            pady=(0, 12)
        )

        # estado inicial
        self.set_active("dashboard")

    # =========================
    # TOGGLE PRINCIPAL (SEM CRASH)
    # =========================
    def toggle(self):
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.expand()
        else:
            self.collapse()

    # =========================
    # EXPANDIDO
    # =========================
    def expand(self):
        self.configure(width=self.expanded_width)

        for btn in self.menu_buttons:
            btn.configure(text=btn._full_text)

        self.user_name.configure(text=self.user_name.cget("text"))
        self.user_name.grid()
        self.user_role.grid()

    # =========================
    # COLAPSADO (SÓ ÍCONES)
    # =========================
    def collapse(self):
        self.configure(width=self.collapsed_width)

        for btn in self.menu_buttons:
            btn.configure(text=btn._icon)

        # opcional: esconder texto do usuário
        self.user_name.grid_remove()
        self.user_role.grid_remove()
        
    def _safe_select(self, callback, key):
        try:
            if callback:
                callback(key)
        except Exception as e:
            print("ERRO AO TROCAR PÁGINA:", e)

    # =========================
    # ATIVAR BOTÃO
    # =========================
    def set_active(self, key: str) -> None:
        for btn in self.menu_buttons:
            btn.set_ativo(getattr(btn, "_page_key", "") == key)