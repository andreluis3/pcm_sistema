import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, bg_color: str) -> None:
        super().__init__(parent, fg_color=bg_color)
        self._expanded_width = 220
        self._collapsed_width = 80
        self._is_expanded = True
        self._animating = False
        self._active = None

        self.configure(width=self._expanded_width)
        self.grid_propagate(False)
        self.grid_rowconfigure(6, weight=1)

        self.toggle_btn = ctk.CTkButton(
            self,
            text="≡",
            width=44,
            height=44,
            corner_radius=14,
            fg_color="#161B22",
            hover_color="#1E2530",
            text_color="#E5E7EB",
            command=self.toggle,
        )
        self.toggle_btn.grid(row=0, column=0, padx=16, pady=16, sticky="w")

        self.menu_buttons = []
        items = [
            ("Dashboard", "📊"),
            ("Materials", "🧪"),
            ("Temperature Tests", "🌡"),
            ("Database", "🗄"),
            ("Settings", "⚙"),
        ]
        for idx, (label, icon) in enumerate(items, start=1):
            btn = ctk.CTkButton(
                self,
                text=f"{icon}  {label}",
                anchor="w",
                height=48,
                corner_radius=14,
                fg_color="#161B22",
                hover_color="#1E2530",
                text_color="#E5E7EB",
                command=lambda b=label: self.set_active(b),
            )
            btn._label = label
            btn.grid(row=idx, column=0, padx=14, pady=6, sticky="ew")
            self.menu_buttons.append(btn)

        self.profile = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=16)
        self.profile.grid(row=7, column=0, padx=12, pady=16, sticky="ew")
        self.profile.grid_columnconfigure(1, weight=1)

        self.avatar = ctk.CTkLabel(
            self.profile,
            text="◉",
            text_color="#00F5D4",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.avatar.grid(row=0, column=0, rowspan=2, padx=12, pady=12)

        self.user_name = ctk.CTkLabel(
            self.profile,
            text="André",
            text_color="#E5E7EB",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.user_name.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(12, 0))

        self.user_role = ctk.CTkLabel(
            self.profile,
            text="PCM Research",
            text_color="#9AA0AB",
            font=ctk.CTkFont(size=11),
        )
        self.user_role.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 12))

        self.set_active("Dashboard")
        self.grid_columnconfigure(0, weight=1)

    def set_active(self, label: str) -> None:
        self._active = label
        for btn in self.menu_buttons:
            is_active = label in btn.cget("text")
            btn.configure(
                fg_color="#18212B" if is_active else "#161B22",
                text_color="#00F5D4" if is_active else "#E5E7EB",
            )

    def toggle(self) -> None:
        if self._animating:
            return
        self._is_expanded = not self._is_expanded
        target = self._expanded_width if self._is_expanded else self._collapsed_width
        self._animate_width(target)

    def _animate_width(self, target: int) -> None:
        self._animating = True
        current = self.winfo_width() or self._expanded_width
        step = 12 if target > current else -12
        next_width = current + step

        if (step > 0 and next_width >= target) or (step < 0 and next_width <= target):
            next_width = target

        self.configure(width=next_width)
        self.grid_propagate(False)

        if next_width != target:
            self.after(16, lambda: self._animate_width(target))
        else:
            self._animating = False
            for btn in self.menu_buttons:
                text = btn.cget("text")
                icon = text.split(" ")[0]
                btn.configure(text=f"{icon}" if not self._is_expanded else text)
                btn.configure(anchor="center" if not self._is_expanded else "w")
            if not self._is_expanded:
                self.user_name.configure(text="")
                self.user_role.configure(text="")
            else:
                self.user_name.configure(text="André")
                self.user_role.configure(text="PCM Research")
