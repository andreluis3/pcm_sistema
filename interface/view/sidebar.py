import customtkinter as ctk

from .widgets import BotaoSidebar
from ui_styles import FONT_NORMAL, FONT_SMALL, FONT_TITLE, PAD_SMALL, PAD_NORMAL, PAD_LARGE


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, ao_selecionar, user_name="Usuário") -> None:
        super().__init__(parent, fg_color="#15181F")

        self._expanded_width = 230
        self._collapsed_width = 80
        self._is_expanded = True
        self._animating = False

        self._animation_id = None

        self._user_name_value = user_name

        self.configure(width=self._expanded_width)
        self.grid_propagate(False)

        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # BOTÃO MENU
        self.toggle_btn = ctk.CTkButton(
            self,
            text="☰",
            width=48,
            height=48,
            corner_radius=12,
            fg_color="#161B22",
            hover_color="#1E2530",
            text_color="#E5E7EB",
            font=FONT_TITLE,
            command=self.toggle,
        )

        self.toggle_btn.grid(row=0, column=0, padx=PAD_LARGE, pady=PAD_NORMAL, sticky="w")

        # MENU
        self.menu_buttons = []

        items = [
            ("dashboard", "📊", "Dashboard"),
            ("sensor", "🌡️", "Sensor"),
            ("materiais", "🧪", "Materiais"),
            ("experimentos", "🔬", "Experimentos"),
            ("calculos", "🧮", "Cálculos Térmicos"),
            ("banco", "🗄️", "Banco de Dados"),
            ("exportar", "📤", "Exportar Dados"),
        ]

        for idx, (key, icon, label) in enumerate(items, start=1):

            text = f"{icon}  {label}"

            btn = BotaoSidebar(
                self,
                text,
                comando=lambda k=key: ao_selecionar(k)
            )

            btn._page_key = key
            btn._icon = icon
            btn._label = label

            btn.grid(
                row=idx,
                column=0,
                padx=PAD_NORMAL,
                pady=PAD_SMALL,
                sticky="ew"
            )

            self.menu_buttons.append(btn)

        # PERFIL DO USUÁRIO
        self.profile = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=14)

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
            text_color="#8B93A5",
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
            text=self._user_name_value,
            text_color="#E5E7EB",
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
            text_color="#9AA0AB",
            font=FONT_SMALL
        )

        self.user_role.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 12),
            pady=(0, 12)
        )

        self.set_active("dashboard")

    # ------------------------

    def set_user(self, name):
        """Atualiza nome do usuário após login"""
        self._user_name_value = name
        self.user_name.configure(text=name)

    # ------------------------

    def set_active(self, key: str) -> None:

        for btn in self.menu_buttons:
            btn.set_ativo(getattr(btn, "_page_key", "") == key)

    # ------------------------

    def toggle(self):

        if self._animation_id:
            self.after_cancel(self._animation_id)

        if self._animating:
            return

        self._is_expanded = not self._is_expanded
        target = self._expanded_width if self._is_expanded else self._collapsed_width

        self._animating = True
        self._animate_width(target)

    # ------------------------

    def _animate_width(self, target: int) -> None:
        current = self.winfo_width()
        step = 14 if target > current else -14
        next_width = current + step

        if (step > 0 and next_width >= target) or (step < 0 and next_width <= target):
            next_width = target

        self.configure(width=next_width)

        if next_width != target:
            self._animation_id = self.after(15, lambda: self._animate_width(target))
        else:
            self._animating = False

            

        # Atualizar textos
        for btn in self.menu_buttons:

            if self._is_expanded:
                btn.configure(text=f"{btn._icon}  {btn._label}", anchor="w")
            else:
                btn.configure(text=btn._icon, anchor="center")

        # Perfil
        if self._is_expanded:
            self.user_name.configure(text=self._user_name_value)
            self.user_role.configure(text="Operador")
        else:
            self.user_name.configure(text="")
            self.user_role.configure(text="")