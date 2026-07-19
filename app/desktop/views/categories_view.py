import customtkinter as ctk

from app import config
from app.models import Category


class _CategoryRow(ctk.CTkFrame):
    def __init__(self, master, on_delete, name: str = "", description: str = "", gmail_label: str = ""):
        super().__init__(master, fg_color=("gray92", "gray17"), corner_radius=8)
        self._on_delete = on_delete

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Nombre (ej: trabajo)")
        self.name_entry.grid(row=0, column=0, padx=(12, 6), pady=(12, 6), sticky="ew")
        self.name_entry.insert(0, name)

        self.label_entry = ctk.CTkEntry(self, placeholder_text="Label de Gmail (ej: Agente/Trabajo)")
        self.label_entry.grid(row=0, column=1, padx=(6, 6), pady=(12, 6), sticky="ew")
        self.label_entry.insert(0, gmail_label)

        delete_button = ctk.CTkButton(
            self, text="Eliminar", width=90, fg_color="#8b3a3a", hover_color="#6e2d2d",
            command=lambda: self._on_delete(self),
        )
        delete_button.grid(row=0, column=2, padx=(6, 12), pady=(12, 6))

        self.description_box = ctk.CTkTextbox(self, height=70)
        self.description_box.grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 12), sticky="ew")
        self.description_box.insert("1.0", description)

    def to_category(self) -> Category | None:
        name = self.name_entry.get().strip()
        gmail_label = self.label_entry.get().strip()
        description = self.description_box.get("1.0", "end").strip()
        if not name or not gmail_label or not description:
            return None
        return Category(name=name, description=description, gmail_label=gmail_label)


class CategoriesView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._rows: list[_CategoryRow] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_list()
        self._load_from_disk()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="Categorías", font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, sticky="w")

        add_button = ctk.CTkButton(header, text="Agregar categoría", command=self._add_empty_row)
        add_button.grid(row=0, column=1, padx=(12, 0))

        save_button = ctk.CTkButton(header, text="Guardar cambios", command=self._save)
        save_button.grid(row=0, column=2, padx=(12, 0))

        self._status_label = ctk.CTkLabel(self, text="", text_color=("gray30", "gray70"))
        self._status_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_list(self) -> None:
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.grid(row=1, column=0, sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

    def on_show(self) -> None:
        pass

    def _load_from_disk(self) -> None:
        for category in config.load_categories():
            self._add_row(category.name, category.description, category.gmail_label)

    def _add_row(self, name: str = "", description: str = "", gmail_label: str = "") -> None:
        row = _CategoryRow(self._list_frame, self._remove_row, name, description, gmail_label)
        row.grid(row=len(self._rows), column=0, sticky="ew", pady=6)
        self._rows.append(row)

    def _add_empty_row(self) -> None:
        self._add_row()

    def _remove_row(self, row: _CategoryRow) -> None:
        row.destroy()
        self._rows.remove(row)
        for i, remaining in enumerate(self._rows):
            remaining.grid(row=i, column=0, sticky="ew", pady=6)

    def _save(self) -> None:
        categories: list[Category] = []
        for row in self._rows:
            category = row.to_category()
            if category is not None:
                categories.append(category)

        if not categories:
            self._status_label.configure(
                text="Agregá al menos una categoría completa antes de guardar.",
                text_color="#e06c75",
            )
            return

        config.save_categories(categories)
        self._status_label.configure(
            text=f"Guardado: {len(categories)} categoría(s) en categories.yaml",
            text_color=("gray30", "gray70"),
        )
