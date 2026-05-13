import customtkinter as ctk
import webbrowser
import webbrowser
from utils.paths import resource_path
from ui_styles import (
    THEME_COLORS,
    FONT_HEADER,
    FONT_TITLE,
    FONT_LABEL,
    FONT_NORMAL,
    FONT_METRIC,
    PAD_LARGE,
    PAD_NORMAL,
    PAD_SMALL,
    card_style,
    button_style,
)

pdf_path = resource_path("assets/cera_coco.pdf")

class _InfoCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, description: str) -> None:
        # UI REFATORADA: cards informativos padronizados
        super().__init__(parent, **card_style())
        self.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))

        value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=THEME_COLORS["primary"],
            font=FONT_METRIC,
        )
        value_label.grid(row=1, column=0, sticky="w", padx=16)

        desc_label = ctk.CTkLabel(
            self,
            text=description,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
            wraplength=220,
            justify="left",
        )
        desc_label.grid(row=2, column=0, sticky="w", padx=16, pady=(4, 12))


class MaterialsView(ctk.CTkFrame):

    def __init__(self, parent) -> None:
        # UI REFATORADA: view de materiais com paleta moderna
        super().__init__(parent, fg_color=THEME_COLORS["bg"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color=THEME_COLORS["bg"])
        container.grid(row=0, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        container.grid_columnconfigure(0, weight=1)

        self._build_header(container)
        self._build_description(container)
        self._build_properties(container)
        self._build_conductivity(container)
        self._build_applications(container)
        self._build_sustainability(container)
        self._build_documentation(container)

    def _section_frame(self, parent):
        frame = ctk.CTkFrame(parent, **card_style())
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_header(self, parent):

        header = self._section_frame(parent)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        title = ctk.CTkLabel(
            header,
            text="MATERIAIS / DATASHEET",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        subtitle = ctk.CTkLabel(
            header,
            text="PCM: Cera de Coco — Material de Mudança de Fase para gerenciamento térmico",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

    def _build_description(self, parent):

        block = self._section_frame(parent)
        block.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            block,
            text="Identificação do material",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        text = (
            "A cera de coco é um material orgânico derivado do óleo de coco, "
            "composto principalmente por ácidos graxos saturados como o ácido láurico. "
            "Esse material apresenta boa estabilidade térmica e comportamento adequado "
            "para aplicações como Material de Mudança de Fase (PCM).\n\n"
            "PCMs armazenam energia térmica através do calor latente durante a transição "
            "de fase sólido-líquido. Durante esse processo o material absorve calor sem "
            "elevar significativamente sua temperatura.\n\n"
            "O objetivo geral do uso da cera de coco neste sistema é atuar como "
            "um elemento de armazenamento térmico passivo em eletrônica, absorvendo "
            "picos de calor gerados por componentes como CPUs, GPUs e módulos de potência."
        )

        body = ctk.CTkLabel(
            block,
            text=text,
            text_color=THEME_COLORS["text_primary"],
            wraplength=880,
            justify="left",
        )
        body.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

    def _build_properties(self, parent):

        frame = self._section_frame(parent)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Propriedades térmicas",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        cards = ctk.CTkFrame(frame, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=12, pady=10)

        for col in range(3):
            cards.grid_columnconfigure(col, weight=1)

        data = [

            ("Temperatura de fusão", "50–54 °C",
             "Faixa típica de fusão para cera de coco hidrogenada."),

            ("Calor latente", "≈ 100–114 J/g",
             "Energia absorvida durante a mudança de fase sólido-líquido."),

            ("Condutividade térmica", "≈ 0.2 W/m·K",
             "Condutividade típica de materiais orgânicos PCM."),

            ("Calor específico", "≈ 2.0 kJ/kg·K",
             "Capacidade térmica aproximada para derivados de óleo de coco."),

            ("Ponto de fulgor", "> 200 °C",
             "Temperatura mínima para vapores inflamáveis."),

            ("Estado físico", "Sólido",
             "Apresentado comercialmente em pastilhas brancas.")
        ]

        row = 0
        col = 0

        for title, value, desc in data:

            card = _InfoCard(cards, title, value, desc)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            col += 1
            if col == 3:
                col = 0
                row += 1

    def _build_conductivity(self, parent):

        frame = self._section_frame(parent)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Condutividade térmica",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        text = (
            "Materiais de mudança de fase orgânicos possuem condutividade térmica "
            "relativamente baixa. Apesar disso, apresentam excelente capacidade "
            "de armazenamento de energia térmica.\n\n"
            "Em aplicações de engenharia térmica é comum utilizar aditivos como "
            "grafite expandido, cobre ou grafeno para aumentar a condutividade "
            "e melhorar a eficiência da transferência de calor."
        )

        body = ctk.CTkLabel(
            frame,
            text=text,
            text_color=THEME_COLORS["text_primary"],
            wraplength=880,
            justify="left",
        )

        body.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

    def _build_applications(self, parent):

        frame = self._section_frame(parent)
        frame.grid(row=4, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Aplicações em eletrônica",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )

        label.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="w")

        text = (
            "A cera de coco pode ser utilizada como PCM em sistemas de gerenciamento "
            "térmico passivo para eletrônica.\n\n"
            "Durante picos de carga térmica, o material absorve energia ao fundir, "
            "reduzindo a elevação da temperatura dos componentes eletrônicos.\n\n"
            "Esse comportamento permite estabilizar temperaturas de CPUs, módulos "
            "de potência e dispositivos embarcados, funcionando como uma bateria "
            "térmica que armazena calor temporariamente."
        )

        body = ctk.CTkLabel(
            frame,
            text=text,
            text_color=THEME_COLORS["text_primary"],
            wraplength=880,
            justify="left",
        )

        body.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

    def _build_sustainability(self, parent):

        frame = self._section_frame(parent)
        frame.grid(row=5, column=0, sticky="ew", pady=(0, 16))

        label = ctk.CTkLabel(
            frame,
            text="Sustentabilidade",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )

        label.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="w")

        cards = ctk.CTkFrame(frame, fg_color="transparent")
        cards.grid(row=1, column=0, padx=12, pady=10, sticky="ew")

        for col in range(3):
            cards.grid_columnconfigure(col, weight=1)

        data = [

            ("Biodegradável",
             "Origem natural",
             "Material derivado de óleo vegetal com decomposição natural."),

            ("Fonte renovável",
             "Origem vegetal",
             "Produzido a partir de recursos agrícolas renováveis."),

            ("Baixo impacto ambiental",
             "Alternativa sustentável",
             "Menor impacto ambiental comparado a parafinas derivadas de petróleo.")
        ]

        for i, (t, v, d) in enumerate(data):

            card = _InfoCard(cards, t, v, d)
            card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")

    def _build_documentation(self, parent):

        frame = self._section_frame(parent)
        frame.grid(row=6, column=0, sticky="ew")

        label = ctk.CTkLabel(
            frame,
            text="Documentação",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_LABEL,
        )

        label.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="w")

        button = ctk.CTkButton(
            frame,
            text="Abrir FDS do fabricante",
            command=lambda: webbrowser.open(pdf_path)
            **button_style("neutral"),
        )

        button.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")
