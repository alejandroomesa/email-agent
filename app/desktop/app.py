import customtkinter as ctk

from app.desktop.views.categories_view import CategoriesView
from app.desktop.views.inbox_view import InboxView
from app.desktop.views.settings_view import SettingsView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NAV_ITEMS = (
    ("inbox", "Bandeja"),
    ("categories", "Categorías"),
    ("settings", "Configuración"),
)


class DesktopApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Gmail Classifier Agent")
        self.geometry("1000x640")
        self.minsize(820, 520)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._build_sidebar()
        self._build_content()

        self._show_view("inbox")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)

        title = ctk.CTkLabel(
            sidebar,
            text="Gmail Agent",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(28, 24), sticky="w")

        for i, (key, label) in enumerate(NAV_ITEMS, start=1):
            button = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray28"),
                command=lambda k=key: self._show_view(k),
            )
            button.grid(row=i, column=0, padx=16, pady=4, sticky="ew")
            self._nav_buttons[key] = button

    def _build_content(self) -> None:
        container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._views = {
            "inbox": InboxView(container),
            "categories": CategoriesView(container),
            "settings": SettingsView(container),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def _show_view(self, key: str) -> None:
        for nav_key, button in self._nav_buttons.items():
            active = nav_key == key
            button.configure(fg_color=("gray75", "gray25") if active else "transparent")

        view = self._views[key]
        view.tkraise()
        if hasattr(view, "on_show"):
            view.on_show()


def main() -> None:
    app = DesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
