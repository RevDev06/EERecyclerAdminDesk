from __future__ import annotations

import json
import os
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib import error, parse, request

DEFAULT_FIREBASE_URL = "https://eerecycler-f394e-default-rtdb.firebaseio.com/precios.json"
FIREBASE_API_KEY = "AIzaSyC2TcXUgAZnBFuyKeHLJdtWvN034kx-yeo" 

@dataclass(frozen=True)
class Product:
    key: str
    label: str
    unit: str

PRODUCTS = [
    Product("pet", "PET Botella", "kg"),
    Product("carton", "Cartón", "kg"),
    Product("boteAluminio", "Bote de aluminio", "kg"),
    Product("cobre", "Cobre", "kg"),
    Product("chatarra", "Chatarra", "kg"),
    Product("radiador", "Radiador de aluminio", "kg"),
    Product("bronce", "Bronce", "kg"),
    Product("plastico", "Plástico grueso", "kg"),
    Product("antimonio", "Antimonio", "kg"),
    Product("aluminioGrueso", "Aluminio grueso", "kg"),
    Product("archivo", "Archivo", "kg"),
    Product("chilero", "Bote chilero", "kg"),
    Product("baterias", "Baterías", "pieza"),
]

BG = "#121212"
PANEL_BG = "#181818"
CARD_BG = "#1d1d1d"
HEADER_BG = "#151915"
ACCENT = "#02a127"
ACCENT_DARK = "#017a1d"
TEXT = "#f2f2f2"
MUTED = "#a8a8a8"
BORDER = "#2c2c2c"
ENTRY_BG = "#232323"
ERROR = "#ff6b6b"

def firebase_url() -> str:
    return os.getenv("FIREBASE_PRECIOS_URL", DEFAULT_FIREBASE_URL)

def firebase_request_url(url: str, token: str | None = None) -> str:
    parsed = parse.urlsplit(url)
    query = dict(parse.parse_qsl(parsed.query, keep_blank_values=True))
    if token:
        query["auth"] = token
    parsed = parsed._replace(query=parse.urlencode(query))
    return parse.urlunsplit(parsed)

def authenticate_firebase(email: str, password: str) -> str:
    if not FIREBASE_API_KEY or FIREBASE_API_KEY == "TU_WEB_API_KEY_AQUI":
        raise ValueError("No has configurado la FIREBASE_API_KEY en el código.")
        
    auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    }).encode("utf-8")
    
    req = request.Request(auth_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["idToken"]
    except error.HTTPError as e:
        err_data = json.loads(e.read().decode("utf-8"))
        err_msg = err_data.get("error", {}).get("message", "Error desconocido")
        if err_msg in ("EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"):
            raise ValueError("Correo o contraseña incorrectos.")
        raise ValueError(f"Fallo de autenticación: {err_msg}")

def normalize_prices_payload(payload: object) -> dict[str, float]:
    if not isinstance(payload, dict):
        raise ValueError("La respuesta de Firebase no tiene un formato valido.")
    if isinstance(payload.get("precios"), dict):
        payload = payload["precios"]
    normalized: dict[str, float] = {}
    for key, value in payload.items():
        if isinstance(key, str) and isinstance(value, (int, float, str)):
            normalized[key] = float(value)
    return normalized

def fetch_prices(url: str, token: str | None = None) -> dict[str, float]:
    request_url = firebase_request_url(url, token)
    with request.urlopen(request_url, timeout=20) as response:
        if response.status != 200:
            raise ConnectionError(f"Firebase respondio con el codigo {response.status}.")
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if parsed is None:
        return {}
    return normalize_prices_payload(parsed)

def save_prices(url: str, token: str, prices: dict[str, float]) -> None:
    payload = json.dumps(prices, ensure_ascii=False, indent=2).encode("utf-8")
    request_url = firebase_request_url(url, token)
    req = request.Request(
        request_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with request.urlopen(req, timeout=20) as response:
        if response.status not in (200, 204):
            raise ConnectionError(f"No fue posible guardar en Firebase. Codigo {response.status}.")

def build_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Header.TFrame", background=HEADER_BG)
    style.configure("Panel.TFrame", background=PANEL_BG)
    style.configure("Section.TFrame", background=BG)
    style.configure("Small.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
    style.configure("Status.TLabel", background=PANEL_BG, foreground=TEXT, font=("Segoe UI", 10, "bold"))
    
    style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff",
                    borderwidth=0, focusthickness=0, padding=(14, 8), font=("Segoe UI", 10, "bold"))
    style.map("Primary.TButton", background=[("active", ACCENT_DARK), ("disabled", "#3a3a3a")],
              foreground=[("disabled", "#9a9a9a")])
              
    style.configure("Secondary.TButton", background="#2a2a2a", foreground=TEXT,
                    borderwidth=0, focusthickness=0, padding=(14, 8), font=("Segoe UI", 10, "bold"))
    style.map("Secondary.TButton", background=[("active", "#343434"), ("disabled", "#2a2a2a")],
              foreground=[("disabled", "#7f7f7f")])
              
    style.configure("Price.TEntry", fieldbackground=ENTRY_BG, foreground=TEXT, insertbackground=TEXT, padding=8, borderwidth=0)
    style.map("Price.TEntry", fieldbackground=[("disabled", "#1d1d1d")], foreground=[("disabled", "#7f7f7f")])


class CustomTitleBar(tk.Frame):
    def __init__(self, parent, window, title_text, on_close, bg_color=HEADER_BG, fg_color=TEXT):
        super().__init__(parent, bg=bg_color)
        self.window = window
        self.pack(fill="x", side="top")

        self.title_label = tk.Label(self, text=title_text, bg=bg_color, fg=fg_color, font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side="left", padx=15, pady=10)

        self.close_btn = tk.Label(self, text=" ✕ ", bg=bg_color, fg=MUTED, font=("Segoe UI", 14), cursor="hand2")
        self.close_btn.pack(side="right", padx=10)
        

        def safe_close(event=None):
            try:
                self.close_btn.unbind("<Leave>")
                self.close_btn.unbind("<Enter>")
            except Exception:
                pass
            on_close()

        self.close_btn.bind("<ButtonRelease-1>", safe_close)
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg=ERROR))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg=MUTED))

        self._offset_x = 0
        self._offset_y = 0

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def do_move(self, event):
        x = self.window.winfo_x() + event.x - self._offset_x
        y = self.window.winfo_y() + event.y - self._offset_y
        self.window.geometry(f"+{x}+{y}")


class LoginWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, app_data: dict):
        super().__init__(parent)
        self.app_data = app_data
        self.configure(bg=BG)
        self.overrideredirect(True) 
        self.grab_set()

        width, height = 380, 460
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        main_frame = tk.Frame(self, bg=BG, highlightbackground=ACCENT, highlightthickness=1)
        main_frame.pack(fill="both", expand=True)

        CustomTitleBar(main_frame, self, "Acceso Seguro", self.destroy, bg_color=BG)

        tk.Label(main_frame, text="EE Recycler", bg=BG, fg=ACCENT, font=("Segoe UI", 24, "bold")).pack(pady=(20, 5))
        tk.Label(main_frame, text="Administración de Precios", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(0, 25))

        tk.Label(main_frame, text="Correo electrónico:", bg=BG, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w", padx=40)
        self.email_var = tk.StringVar()
        email_entry = tk.Entry(main_frame, textvariable=self.email_var, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 12), bd=0, relief="flat")
        email_entry.pack(fill="x", padx=40, pady=(5, 15), ipady=8)

        tk.Label(main_frame, text="Contraseña:", bg=BG, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w", padx=40)
        self.pass_var = tk.StringVar()
        pass_entry = tk.Entry(main_frame, textvariable=self.pass_var, show="*", bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 12), bd=0, relief="flat")
        pass_entry.pack(fill="x", padx=40, pady=(5, 25), ipady=8)

        self.btn_login = ttk.Button(main_frame, text="Iniciar Sesión", style="Primary.TButton", command=self.do_login)
        self.btn_login.pack(fill="x", padx=40, pady=10)
        
        self.lbl_error = tk.Label(main_frame, text="", bg=BG, fg=ERROR, font=("Segoe UI", 9))
        self.lbl_error.pack(fill="x", padx=40)
        
        self.bind("<Return>", lambda e: self.do_login())
        email_entry.focus_set()

    def do_login(self):
        email = self.email_var.get().strip()
        password = self.pass_var.get().strip()
        
        if not email or not password:
            self.lbl_error.config(text="Ingresa correo y contraseña.")
            return
            
        self.btn_login.state(["disabled"])
        self.lbl_error.config(text="Conectando...", fg=MUTED)
        self.update()
        
        try:
            self.app_data["token"] = authenticate_firebase(email, password)
            self.destroy()
        except ValueError as e:
            self.lbl_error.config(text=str(e), fg=ERROR)
            self.btn_login.state(["!disabled"])
        except Exception as e:
            self.lbl_error.config(text="Error de red o conexión.", fg=ERROR)
            self.btn_login.state(["!disabled"])


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class PriceAdminApp:
    def __init__(self, root: tk.Tk, token: str) -> None:
        self.root = root
        self.url = firebase_url()
        self.token = token
        self.price_vars: dict[str, tk.StringVar] = {}
        self.entry_widgets: dict[str, ttk.Entry] = {}
        self.loaded_prices: dict[str, float] = {}
        self.dirty = False
        self.loading = False
        self._suspend_dirty = False

        self._setup_window()
        self._build_ui()
        self._bind_shortcuts()
        self.root.after(200, lambda: self.load_prices(silent=True, confirm_overwrite=False))

    def _setup_window(self) -> None:
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)

        width, height = 1080, 780
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        root_frame = tk.Frame(self.root, bg=BG, highlightbackground=ACCENT, highlightthickness=1)
        root_frame.pack(fill="both", expand=True)

        self.title_bar = CustomTitleBar(root_frame, self.root, "EERecycler | Administrador de precios", self.on_close, bg_color=HEADER_BG)

        header = ttk.Frame(root_frame, style="Header.TFrame", padding=(24, 18))
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=HEADER_BG)
        title_box.pack(side="left", fill="x", expand=True)

        tk.Label(title_box, text="EERecycler | Panel de Control", bg=HEADER_BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Edita los precios y sincroniza el archivo JSON alojado en Firebase.", bg=HEADER_BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        actions = ttk.Frame(root_frame, style="Section.TFrame", padding=(24, 16, 24, 10))
        actions.pack(fill="x")

        self.reload_button = ttk.Button(actions, text="Recargar desde Firebase", style="Primary.TButton", command=self.load_prices)
        self.reload_button.pack(side="left")

        self.save_button = ttk.Button(actions, text="Guardar en Firebase", style="Primary.TButton", command=self.save_prices_to_firebase)
        self.save_button.pack(side="left", padx=(12, 0))

        self.export_button = ttk.Button(actions, text="Exportar copia local", style="Secondary.TButton", command=self.export_backup)
        self.export_button.pack(side="left", padx=(12, 0))

        self.revert_button = ttk.Button(actions, text="Revertir cambios", style="Secondary.TButton", command=self.revert_loaded_values)
        self.revert_button.pack(side="left", padx=(12, 0))

        ttk.Label(actions, text="Los cambios se guardan directamente en /precios.json.", style="Small.TLabel").pack(side="right")

        content = ttk.Frame(root_frame, style="Section.TFrame", padding=(24, 0, 24, 12))
        content.pack(fill="both", expand=True)

        intro = tk.Frame(content, bg=BG)
        intro.pack(fill="x", pady=(0, 12))
        tk.Label(intro, text="Precios actuales", bg=BG, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(intro, text=f"{len(PRODUCTS)} productos configurados. El precio de baterías se maneja por pieza; el resto por kilo.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        self.scrollable = ScrollableFrame(content)
        self.scrollable.pack(fill="both", expand=True)

        for product in PRODUCTS:
            self._create_product_row(self.scrollable.inner, product)

        footer = ttk.Frame(root_frame, style="Panel.TFrame", padding=(24, 12))
        footer.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="Listo para administrar precios.")
        self.status_label = ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.last_sync_var = tk.StringVar(value="Ultima sincronizacion: pendiente")
        ttk.Label(footer, textvariable=self.last_sync_var, style="Small.TLabel").pack(side="right")

    def _create_product_row(self, master: tk.Widget, product: Product) -> None:
        card = tk.Frame(master, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=14)
        card.pack(fill="x", pady=7)

        left = tk.Frame(card, bg=CARD_BG)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text=product.label, bg=CARD_BG, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(left, text=f"Clave: {product.key}   |   Unidad: {product.unit}", bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        right = tk.Frame(card, bg=CARD_BG)
        right.pack(side="right", padx=(18, 0))

        tk.Label(right, text="$", bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 16, "bold")).pack(side="left", pady=(2, 0))

        var = tk.StringVar(value="")
        var.trace_add("write", self._on_value_changed)
        entry = ttk.Entry(right, textvariable=var, width=16, style="Price.TEntry", justify="right")
        entry.pack(side="left", padx=(6, 0))

        tk.Label(right, text=product.unit, bg=CARD_BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(10, 0), pady=(2, 0))

        self.price_vars[product.key] = var
        self.entry_widgets[product.key] = entry

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-s>", lambda event: self.save_prices_to_firebase())
        self.root.bind("<F5>", lambda event: self.load_prices())
        self.root.bind("<Control-e>", lambda event: self.export_backup())

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self.status_var.set(text)
        self.status_label.configure(foreground=ERROR if error else TEXT)

    def _set_dirty(self, value: bool) -> None:
        self.dirty = value
        title = "EERecycler | Administrador de precios"
        if self.dirty:
            title += " *"
        self.title_bar.title_label.config(text=title)

    def _on_value_changed(self, *_: object) -> None:
        if self._suspend_dirty or self.loading:
            return
        if not self.dirty:
            self._set_dirty(True)
            self._set_status("Hay cambios sin guardar.")

    def _set_interaction_state(self, enabled: bool) -> None:
        state = "!disabled" if enabled else "disabled"
        for button in (self.reload_button, self.save_button, self.export_button, self.revert_button):
            button.state([state])
        for entry in self.entry_widgets.values():
            entry.state([state])

    def _format_price(self, value: float) -> str:
        return f"{value:.2f}"

    def _read_form_prices(self) -> tuple[dict[str, float], list[str]]:
        values: dict[str, float] = {}
        errors: list[str] = []

        for product in PRODUCTS:
            raw = self.price_vars[product.key].get().strip().replace(",", ".")
            if not raw:
                errors.append(f"{product.label}: vacio")
                continue
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"{product.label}: '{raw}'")
                continue
            if value < 0:
                errors.append(f"{product.label}: no puede ser negativo")
                continue
            values[product.key] = value

        return values, errors

    def _apply_prices(self, prices: dict[str, float]) -> None:
        self._suspend_dirty = True
        try:
            for product in PRODUCTS:
                value = prices.get(product.key)
                if value is None:
                    self.price_vars[product.key].set("")
                else:
                    self.price_vars[product.key].set(self._format_price(float(value)))
        finally:
            self._suspend_dirty = False

    def load_prices(self, *, silent: bool = False, confirm_overwrite: bool = True) -> None:
        if self.loading:
            return

        if confirm_overwrite and self.dirty:
            if not messagebox.askyesno("Cambios sin guardar", "Hay cambios sin guardar. Si recargas desde Firebase se reemplazaran esos valores. Deseas continuar?"):
                return

        self.loading = True
        self._set_interaction_state(False)
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        try:
            prices = fetch_prices(self.url, self.token)
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, ConnectionError) as exc:
            message = f"No se pudieron cargar los precios: {exc}"
            self._set_status(message, error=True)
            if not silent:
                messagebox.showerror("Error al cargar", message)
            return
        finally:
            self.root.config(cursor="")
            self._set_interaction_state(True)
            self.loading = False

        self.loaded_prices = prices.copy()
        self._apply_prices(prices)
        self._set_dirty(False)
        self.last_sync_var.set(f"Ultima sincronizacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self._set_status("Precios cargados correctamente desde Firebase.")
        if not silent:
            messagebox.showinfo("Carga completa", "Los precios se cargaron correctamente.")

    def save_prices_to_firebase(self, *, show_popup: bool = True) -> None:
        if self.loading:
            return

        prices, errors = self._read_form_prices()
        if errors:
            messagebox.showwarning("Valores invalidos", "Corrige estos campos antes de guardar:\n\n" + "\n".join(f"- {item}" for item in errors))
            return

        self.loading = True
        self._set_interaction_state(False)
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        try:
            save_prices(self.url, self.token, prices)
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, ConnectionError) as exc:
            message = f"No se pudieron guardar los precios: {exc}"
            self._set_status(message, error=True)
            messagebox.showerror("Error al guardar", message)
            return
        finally:
            self.root.config(cursor="")
            self._set_interaction_state(True)
            self.loading = False

        self.loaded_prices = prices.copy()
        self._set_dirty(False)
        self.last_sync_var.set(f"Ultima sincronizacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self._set_status("Precios guardados correctamente en Firebase.")
        if show_popup:
            messagebox.showinfo("Guardado completo", "Los precios se guardaron correctamente en Firebase.")

    def revert_loaded_values(self) -> None:
        if self.loading:
            return
        if not self.loaded_prices:
            messagebox.showinfo("Sin datos", "Aun no se ha cargado ningun archivo desde Firebase.")
            return
        self._apply_prices(self.loaded_prices)
        self._set_dirty(False)
        self._set_status("Se restauraron los ultimos valores cargados.")

    def export_backup(self) -> None:
        if self.loading:
            return

        prices, errors = self._read_form_prices()
        if errors:
            messagebox.showwarning("Valores invalidos", "Corrige estos campos antes de exportar:\n\n" + "\n".join(f"- {item}" for item in errors))
            return

        default_name = f"precios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = filedialog.asksaveasfilename(
            title="Guardar copia local",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("Archivo JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return

        backup_path = Path(path)
        backup_path.write_text(json.dumps(prices, ensure_ascii=False, indent=2), encoding="utf-8")
        self._set_status(f"Copia local guardada en {backup_path.name}.")
        messagebox.showinfo("Exportacion completa", f"Se guardo la copia local en:\n{backup_path}")

    def on_close(self) -> None:
        if self.loading:
            messagebox.showwarning("Operacion en curso", "Espera a que termine la sincronizacion actual.")
            return

        if self.dirty:
            choice = messagebox.askyesnocancel("Cambios sin guardar", "Hay cambios sin guardar. Deseas guardarlos antes de salir?")
            if choice is None:
                return
            if choice:
                self.save_prices_to_firebase(show_popup=False)
                if self.dirty:
                    return

        self.root.destroy()

def main() -> None:
    root = tk.Tk()
    build_styles(root)
    root.withdraw()
    
    app_data = {"token": None}
    
    login_window = LoginWindow(root, app_data)
    root.wait_window(login_window)
    
    if not app_data["token"]:
        root.destroy()
        return
        
    root.deiconify()
    PriceAdminApp(root, token=app_data["token"])
    root.mainloop()

if __name__ == "__main__":
    main()