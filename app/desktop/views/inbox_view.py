import queue
import threading
from tkinter import ttk

import customtkinter as ctk

from app.storage import Storage
from app.sync_service import SyncResult, run_sync

COLUMNS = ("classified_at", "sender", "subject", "category", "confidence")
HEADINGS = {
    "classified_at": "Fecha",
    "sender": "De",
    "subject": "Asunto",
    "category": "Categoría",
    "confidence": "Confianza",
}


def _style_treeview() -> None:
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Inbox.Treeview",
        background="#2a2d2e",
        foreground="#dce4ee",
        fieldbackground="#2a2d2e",
        bordercolor="#343638",
        borderwidth=0,
        rowheight=28,
    )
    style.map("Inbox.Treeview", background=[("selected", "#1f538d")])
    style.configure(
        "Inbox.Treeview.Heading",
        background="#3a3d3e",
        foreground="#dce4ee",
        relief="flat",
    )
    style.map("Inbox.Treeview.Heading", background=[("active", "#3a7ebf")])


class InboxView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._storage = Storage()
        self._queue: queue.Queue = queue.Queue()
        self._syncing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_table()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header, text="Bandeja de entrada", font=ctk.CTkFont(size=22, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        self._sync_button = ctk.CTkButton(
            header, text="Sincronizar ahora", command=self._start_sync
        )
        self._sync_button.grid(row=0, column=1, padx=(12, 0))

        self._status_label = ctk.CTkLabel(self, text="", text_color=("gray30", "gray70"))
        self._status_label.grid(row=1, column=0, sticky="w", pady=(0, 8))

    def _build_table(self) -> None:
        _style_treeview()

        table_frame = ctk.CTkFrame(self, fg_color=("gray90", "#2a2d2e"))
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            table_frame,
            columns=COLUMNS,
            show="headings",
            style="Inbox.Treeview",
        )
        for col in COLUMNS:
            self._tree.heading(col, text=HEADINGS[col])
            width = 140 if col in ("classified_at", "sender", "confidence") else 260
            self._tree.column(col, width=width, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def on_show(self) -> None:
        self._reload_table()

    def _reload_table(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for record in self._storage.list_recent(limit=200):
            self._tree.insert(
                "",
                "end",
                values=(
                    record.classified_at.strftime("%Y-%m-%d %H:%M"),
                    record.sender,
                    record.subject,
                    record.category,
                    f"{record.confidence * 100:.0f}%",
                ),
            )

    def _start_sync(self) -> None:
        if self._syncing:
            return
        self._syncing = True
        self._sync_button.configure(state="disabled", text="Sincronizando...")
        self._status_label.configure(text="Iniciando sincronización...")

        thread = threading.Thread(target=self._sync_worker, daemon=True)
        thread.start()
        self.after(100, self._poll_queue)

    def _sync_worker(self) -> None:
        try:
            result = run_sync(progress_callback=lambda msg: self._queue.put(("progress", msg)))
            self._queue.put(("done", result))
        except Exception as exc:  # noqa: BLE001 - se muestra en la UI
            self._queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "progress":
                    self._status_label.configure(text=payload)
                elif kind == "done":
                    self._on_sync_done(payload)
                elif kind == "error":
                    self._on_sync_error(payload)
        except queue.Empty:
            pass

        if self._syncing:
            self.after(100, self._poll_queue)

    def _on_sync_done(self, result: SyncResult) -> None:
        self._syncing = False
        self._sync_button.configure(state="normal", text="Sincronizar ahora")
        by_category = ", ".join(f"{k}: {v}" for k, v in result.by_category.items()) or "—"
        self._status_label.configure(
            text=(
                f"Listo. Procesados: {result.processed} · "
                f"Ya existentes: {result.skipped_already_processed} · Por categoría: {by_category}"
            )
        )
        self._reload_table()

    def _on_sync_error(self, message: str) -> None:
        self._syncing = False
        self._sync_button.configure(state="normal", text="Sincronizar ahora")
        self._status_label.configure(text=f"Error: {message}", text_color="#e06c75")
