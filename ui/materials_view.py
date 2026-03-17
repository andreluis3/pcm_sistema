import customtkinter as ctk


class _InfoCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, description: str) -> None:
        super().__init__(parent, fg_color="#121821", corner_radius=16)
        self.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))

        value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color="#E2E8F0",
            font=ctk.CTkFont(family="IBM Plex Mono", size=22, weight="bold"),
        )
        value_label.grid(row=1, column=0, sticky="w", padx=16)

        desc_label = ctk.CTkLabel(
            self,
            text=description,
            text_color="#6B7280",
            font=ctk.CTkFont(size=11),
            wraplength=220,
            justify="left",
        )
        desc_label.grid(row=2, column=0, sticky="w", padx=16, pady=(4, 12))


class MaterialsView(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color="#0B0F14")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color="#0B0F14")
        container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        container.grid_columnconfigure(0, weight=1)

        self._build_header(container)
        self._build_description(container)
        self._build_properties(container)
        self._build_conductivity(container)
        self._build_applications(container)
        self._build_sustainability(container)

    def _section_frame(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=18)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_header(self, parent) -> None:
        header = self._section_frame(parent)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        title = ctk.CTkLabel(
            header,
            text="Material PCM: Cera de Coco",
            text_color="#E2E8F0",
            font=ctk.CTkFont(family="IBM Plex Sans", size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        subtitle = ctk.CTkLabel(
            header,
            text="Propriedades termofísicas e aplicação em gerenciamento térmico de eletrônicos",
            text_color="#A0AEC0",
            font=ctk.CTkFont(size=12),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_description(self, parent) -> None:
        block = self._section_frame(parent)
        block.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            block,
            text="Descrição científica",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        text = (
            "A cera de coco é um material orgânico derivado do óleo de coco, "
            "composto principalmente por ácidos graxos como o ácido láurico. "
            "Por ser biodegradável e renovável, apresenta baixo impacto ambiental "
            "e é uma alternativa sustentável aos PCMs derivados de petróleo.\n\n"
            "Materiais de mudança de fase (PCM) absorvem calor durante a transição "
            "de sólido para líquido sem elevar significativamente a temperatura. "
            "Esse fenômeno é conhecido como armazenamento de calor latente.\n\n"
            "Na eletrônica, a cera de coco pode absorver picos térmicos de componentes, "
            "armazenando energia de forma temporária e estabilizando a temperatura do sistema. "
            "Esse comportamento permite que o PCM atue como uma bateria térmica passiva."
        )

        body = ctk.CTkLabel(
            block,
            text=text,
            text_color="#CBD5F5",
            font=ctk.CTkFont(size=12),
            wraplength=880,
            justify="left",
        )
        body.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_properties(self, parent) -> None:
        frame = self._section_frame(parent)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            frame,
            text="Propriedades termofísicas",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        cards = ctk.CTkFrame(frame, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        for col in range(3):
            cards.grid_columnconfigure(col, weight=1)

        data = [
            (
                "Melting Temperature",
                "38–45 °C",
                "Faixa típica de fusão para cera de coco.",
            ),
            (
                "Latent Heat",
                "200–230 kJ/kg",
                "Valores médios reportados para PCMs à base de coco.",
            ),
            (
                "Thermal Conductivity",
                "≈ 0.2 W/m·K",
                "Condutividade típica de PCMs orgânicos.",
            ),
            (
                "Density",
                "≈ 0.9 g/cm³",
                "Densidade em fase sólida ou semi-sólida.",
            ),
            (
                "Boiling / Decomposition",
                "> 300 °C",
                "Decomposição térmica acima de 300 °C.",
            ),
            (
                "Energy Storage Potential",
                "Alto",
                "Elevada capacidade de armazenamento por calor latente.",
            ),
        ]

        row = 0
        col = 0
        for title, value, desc in data:
            card = _InfoCard(cards, title, value, desc)
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            col += 1
            if col == 3:
                col = 0
                row += 1

        note = ctk.CTkLabel(
            frame,
            text=(
                "Referências científicas indicam calor latente em torno de 100–114 J/g "
                "para PCMs à base de óleo de coco, dependendo da composição e do processamento."
            ),
            text_color="#64748B",
            font=ctk.CTkFont(size=11),
            wraplength=860,
            justify="left",
        )
        note.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_conductivity(self, parent) -> None:
        frame = self._section_frame(parent)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Condutividade térmica",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        text = (
            "PCMs orgânicos possuem baixa condutividade térmica, o que pode limitar a "
            "velocidade de transferência de calor. Ainda assim, são muito eficazes para "
            "armazenamento passivo de energia térmica. Estudos acadêmicos demonstram melhorias "
            "na condutividade com a adição de grafite ou nanopartículas de grafeno."
        )

        body = ctk.CTkLabel(
            frame,
            text=text,
            text_color="#CBD5F5",
            font=ctk.CTkFont(size=12),
            wraplength=880,
            justify="left",
        )
        body.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_applications(self, parent) -> None:
        frame = self._section_frame(parent)
        frame.grid(row=4, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Aplicações em eletrônica",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        text = (
            "A cera de coco pode ser integrada ao resfriamento de CPUs e eletrônicos de potência "
            "como um buffer térmico. O PCM absorve picos de calor durante a fusão e libera a energia "
            "armazenada durante a solidificação, reduzindo a amplitude das variações de temperatura. "
            "Esse mecanismo suporta estratégias de armazenamento de calor passivo e prolonga a estabilidade térmica."
        )

        body = ctk.CTkLabel(
            frame,
            text=text,
            text_color="#CBD5F5",
            font=ctk.CTkFont(size=12),
            wraplength=880,
            justify="left",
        )
        body.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_sustainability(self, parent) -> None:
        frame = self._section_frame(parent)
        frame.grid(row=5, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            frame,
            text="Sustentabilidade",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        cards = ctk.CTkFrame(frame, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))
        for col in range(3):
            cards.grid_columnconfigure(col, weight=1)

        data = [
            (
                "Biodegradable",
                "Material decompõe naturalmente",
                "Menor impacto no descarte após uso.",
            ),
            (
                "Renewable Origin",
                "Derivado de fontes vegetais",
                "Processo alinhado a cadeias sustentáveis.",
            ),
            (
                "Low Environmental Impact",
                "Comparado a parafinas",
                "Alternativa com menor pegada de carbono.",
            ),
        ]

        for col, (title, value, desc) in enumerate(data):
            card = _InfoCard(cards, title, value, desc)
            card.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)
