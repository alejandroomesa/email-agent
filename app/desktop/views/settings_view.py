import queue
import threading

import customtkinter as ctk

from app import config
from app.gmail_client import GmailClient


class SettingsView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._queue: queue.Queue = queue.Queue()

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Configuración", font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        form = ctk.CTkFrame(self, fg_color=("gray92", "gray17"), corner_radius=10)
        form.grid(row=1, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        self._address_entry = self._add_field(form, 0, "Cuenta de Gmail")
        self._password_entry, self._toggle_button = self._add_password_field(
            form, 1, "Contraseña de aplicación"
        )
        self._model_entry = self._add_field(form, 2, "Modelo de Ollama")
        self._query_entry = self._add_field(form, 3, "Filtro de búsqueda (Gmail search)")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=2, column=0, sticky="w", pady=16)

        save_button = ctk.CTkButton(button_row, text="Guardar", command=self._save)
        save_button.grid(row=0, column=0)

        self._test_button = ctk.CTkButton(
            button_row, text="Probar conexión", command=self._start_test_connection
        )
        self._test_button.grid(row=0, column=1, padx=(12, 0))

        self._status_label = ctk.CTkLabel(self, text="", text_color=("gray30", "gray70"))
        self._status_label.grid(row=3, column=0, sticky="w")

        self._load_from_env()

    def _add_field(self, parent, row: int, label_text: str) -> ctk.CTkEntry:
        label = ctk.CTkLabel(parent, text=label_text, anchor="w")
        label.grid(row=row, column=0, padx=(16, 12), pady=12, sticky="w")

        entry = ctk.CTkEntry(parent, width=360)
        entry.grid(row=row, column=1, padx=(0, 16), pady=12, sticky="ew")
        return entry

    def _add_password_field(self, parent, row: int, label_text: str):
        label = ctk.CTkLabel(parent, text=label_text, anchor="w")
        label.grid(row=row, column=0, padx=(16, 12), pady=12, sticky="w")

        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=1, padx=(0, 16), pady=12, sticky="ew")
        wrapper.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(wrapper, show="*")
        entry.grid(row=0, column=0, sticky="ew")

        def toggle() -> None:
            revealed = entry.cget("show") == ""
            entry.configure(show="*" if revealed else "")
            toggle_button.configure(text="Mostrar" if revealed else "Ocultar")

        toggle_button = ctk.CTkButton(wrapper, text="Mostrar", width=80, command=toggle)
        toggle_button.grid(row=0, column=1, padx=(8, 0))

        return entry, toggle_button

    def on_show(self) -> None:
        pass

    def _load_from_env(self) -> None:
        self._address_entry.insert(0, config.GMAIL_ADDRESS or "")
        self._password_entry.insert(0, config.GMAIL_APP_PASSWORD or "")
        self._model_entry.insert(0, config.OLLAMA_MODEL)
        self._query_entry.insert(0, config.GMAIL_QUERY)

    def _save(self) -> None:
        config.save_env_settings(
            {
                "GMAIL_ADDRESS": self._address_entry.get().strip(),
                "GMAIL_APP_PASSWORD": self._password_entry.get().strip(),
                "OLLAMA_MODEL": self._model_entry.get().strip(),
                "GMAIL_QUERY": self._query_entry.get().strip(),
            }
        )
        self._status_label.configure(
            text="Configuración guardada en .env", text_color=("gray30", "gray70")
        )

    def _start_test_connection(self) -> None:
        self._save()
        self._test_button.configure(state="disabled", text="Probando...")
        self._status_label.configure(text="Conectando a Gmail por IMAP...")

        thread = threading.Thread(target=self._test_connection_worker, daemon=True)
        thread.start()
        self.after(100, self._poll_queue)

    def _test_connection_worker(self) -> None:
        try:
            GmailClient().test_connection()
            self._queue.put(("ok", None))
        except Exception as exc:  # noqa: BLE001 - se muestra en la UI
            self._queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        try:
            kind, payload = self._queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_queue)
            return

        self._test_button.configure(state="normal", text="Probar conexión")
        if kind == "ok":
            self._status_label.configure(text="Conexión exitosa.", text_color="#4caf50")
        else:
            self._status_label.configure(text=f"Error: {payload}", text_color="#e06c75")
