import sys
import time
import re
import json
import subprocess
import argparse
import locale
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


# ============================================================
# KONFIGURACJA PROGRAMU
# ============================================================

APP_NAME = "Modpack Quest Tracker"

APPDATA_DIR = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "ModpackQuestTracker"
)

CONFIG_FILE = APPDATA_DIR / "config.json"

TRACKER_EXE_NAME = "Modpack_Quest_Tracker.exe"
TRACKER_PY_NAME = "Modpack_Quest_Tracker.py"

FTB_PROCESS_NAME = "FTB Electron App.exe"
FTB_EXECUTABLE_PATHS = [
    Path.home() / "AppData" / "Local" / "Programs" / "ftb-app" / FTB_PROCESS_NAME,
]

CHECK_INTERVAL = 2

# ============================================================
# ROZMIAR TRACKERA
# ============================================================

DEFAULT_TRACKER_WIDTH = 300
DEFAULT_TRACKER_HEIGHT = 210

MIN_TRACKER_WIDTH = 300
MAX_TRACKER_WIDTH = 800

MIN_TRACKER_HEIGHT = 210
MAX_TRACKER_HEIGHT = 500

# ============================================================
# DOMYŚLNE / ZNANE LOKALIZACJE
# ============================================================

KNOWN_CURSEFORGE_PATHS = [
    Path(r"D:\MCMODDED\CurseForge Windows\CurseForge.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "CurseForge Windows" / "CurseForge.exe",
    Path.home() / "AppData" / "Local" / "Programs" / "CurseForge" / "CurseForge.exe",
    Path.home() / "AppData" / "Local" / "CurseForge" / "CurseForge.exe",
]


KNOWN_INSTANCES_PATHS = [
    Path(r"D:\MCMODDED\Instances"),
    Path.home() / "AppData" / "Roaming" / "CurseForge" / "Instances",
    Path.home() / "Documents" / "CurseForge" / "Instances",
]


# ============================================================
# ŚCIEŻKA LAUNCHERA
# ============================================================

def get_launcher_directory():
    """
    Zwraca katalog, w którym znajduje się launcher.

    Przy uruchomieniu jako EXE:
        katalog zawierający Modpack_Quest_Launcher.exe

    Przy uruchomieniu jako .py:
        katalog zawierający plik .py
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


# ============================================================
# JĘZYK
# ============================================================

SUPPORTED_LANGUAGES = {
    "pl": "Polski",
    "en": "English"
}


def detect_windows_language():
    """
    Wykrywa język systemu Windows.

    Polski Windows -> pl
    Pozostałe języki -> en
    """

    try:
        language = locale.getlocale()[0]

        if language and language.lower().startswith("pl"):
            return "pl"

    except Exception:
        pass

    return "en"


def normalize_language(language):
    if language in SUPPORTED_LANGUAGES:
        return language

    return detect_windows_language()


LAUNCHER_TRANSLATIONS = {
    "pl": {
        "first_run": "Pierwsze uruchomienie - skonfiguruj program.",
        "settings": "Ustawienia programu.",
        "curseforge": "CurseForge (opcjonalnie):",
        "ftb": "FTB App Standalone (opcjonalnie):",
        "instances": "Folder instancji modpacków:",
        "choose_ftb": "Wskaż plik FTB Electron App.exe.",
        "choose_one_launcher": "Wskaż przynajmniej jeden launcher: CurseForge lub FTB App.",
        "launcher_hint": "Wystarczy skonfigurować launcher, z którego korzystasz. Folder Instances nie jest wymagany.",
        "choose": "Wybierz...",
        "tracker_size": "Rozmiar trackera:",
        "width": "Szerokość:",
        "height": "Wysokość:",
        "language": "Język:",
        "range": "Zakres: {wmin}–{wmax} px szerokości, {hmin}–{hmax} px wysokości.",
        "preview": "Podgląd trackera",
        "sample_pack": "Przykładowa paczka",
        "world": "World: World",
        "day": "Day: 127",
        "completed": "Completed: 42 / 144",
        "remaining": "Remaining: 102",
        "completion": "Completion: 29.17%",
        "live": "● LIVE  18:42:15",
        "size": "Rozmiar: {width} × {height} px",
        "number_error": "Rozmiar trackera musi być liczbą.",
        "choose_cf": "Wskaż plik CurseForge.exe.",
        "choose_instances": "Wskaż folder Instances.",
        "invalid_config": "Nieprawidłowa konfiguracja.",
        "save_error": "Nie udało się zapisać config.json.",
        "reset_size": "Przywróć domyślny rozmiar",
        "save": "Zapisz",
        "cancel": "Anuluj",
        "config_saved": "Konfiguracja została zapisana.",
        "no_changes": "Nie wprowadzono zmian.",
        "settings_open": "Otwiera ustawienia programu.",
        "config_invalid_console": "Konfiguracja jest nieprawidłowa.",
        "starting_config": "Uruchamianie konfiguracji...",
        "no_config": "Nie znaleziono poprawnego config.json.",
        "first_config": "Uruchamianie pierwszej konfiguracji...",
        "config_dir_error": "Nie udało się utworzyć katalogu konfiguracji:",
        "config_read_error": "Nie udało się odczytać config.json:",
        "config_write_error": "Nie udało się zapisać config.json:",
        "language_error": "Nieprawidłowy język.",
    },
    "en": {
        "first_run": "First run - configure the program.",
        "settings": "Program settings.",
        "curseforge": "CurseForge (optional):",
        "ftb": "FTB App Standalone (optional):",
        "instances": "Modpack instances folder:",
        "choose_ftb": "Select FTB Electron App.exe.",
        "choose_one_launcher": "Select at least one launcher: CurseForge or FTB App.",
        "launcher_hint": "Configure only the launcher(s) you use. An Instances folder is not required.",
        "choose": "Browse...",
        "tracker_size": "Tracker size:",
        "width": "Width:",
        "height": "Height:",
        "language": "Language:",
        "range": "Range: {wmin}–{wmax} px width, {hmin}–{hmax} px height.",
        "preview": "Tracker preview",
        "sample_pack": "Example pack",
        "world": "World: World",
        "day": "Day: 127",
        "completed": "Completed: 42 / 144",
        "remaining": "Remaining: 102",
        "completion": "Completion: 29.17%",
        "live": "● LIVE  18:42:15",
        "size": "Size: {width} × {height} px",
        "number_error": "Tracker size must be a number.",
        "choose_cf": "Select CurseForge.exe.",
        "choose_instances": "Select the Instances folder.",
        "invalid_config": "Invalid configuration.",
        "save_error": "Could not save config.json.",
        "reset_size": "Reset default size",
        "save": "Save",
        "cancel": "Cancel",
        "config_saved": "Configuration saved.",
        "no_changes": "No changes were made.",
        "settings_open": "Open program settings.",
        "config_invalid_console": "Configuration is invalid.",
        "starting_config": "Opening configuration...",
        "no_config": "No valid config.json found.",
        "first_config": "Opening first-time configuration...",
        "config_dir_error": "Could not create configuration directory:",
        "config_read_error": "Could not read config.json:",
        "config_write_error": "Could not save config.json:",
        "language_error": "Invalid language.",
    }
}


def tr(language, key, **kwargs):
    language = normalize_language(language)
    value = LAUNCHER_TRANSLATIONS[language].get(key, key)
    return value.format(**kwargs)


# ============================================================
# KONFIGURACJA JSON
# ============================================================

def ensure_appdata_directory():
    """
    Tworzy katalog konfiguracyjny, jeżeli jeszcze nie istnieje.
    """

    try:
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        return True

    except Exception as error:
        print("Nie udało się utworzyć katalogu konfiguracji:")
        print(error)
        return False


def load_config():
    """
    Wczytuje config.json.

    Zwraca:
        dict
    albo:
        None
    """

    if not CONFIG_FILE.exists():
        return None

    try:
        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            config = json.load(file)

        if not isinstance(config, dict):
            return None

        return config

    except Exception as error:
        print("Nie udało się odczytać config.json:")
        print(error)

        return None


def save_config(
    curseforge_path=None,
    ftb_path=None,
    tracker_width=DEFAULT_TRACKER_WIDTH,
    tracker_height=DEFAULT_TRACKER_HEIGHT,
    language=None
):
    """Zapisuje ustawienia, zachowując nieznane i starsze pola konfiguracji."""
    if not ensure_appdata_directory():
        return False

    # Zachowujemy istniejące pola (np. starsze instances_path), aby aktualizacja
    # nie usuwała ustawień zapisanych przez poprzednie wersje programu.
    config = load_config() or {}
    config.update({
        "curseforge_path": str(Path(curseforge_path).resolve()) if curseforge_path else "",
        "ftb_path": str(Path(ftb_path).resolve()) if ftb_path else "",
        "tracker_width": int(tracker_width),
        "tracker_height": int(tracker_height),
        "language": normalize_language(language),
        "config_version": 2,
    })

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
        return True
    except Exception as error:
        print("Nie udało się zapisać config.json:")
        print(error)
        return False


def validate_config(config):
    """Waliduje opcjonalne ścieżki launcherów i ustawienia trackera."""
    if not isinstance(config, dict):
        return False, "Konfiguracja jest nieprawidłowa."

    curseforge_path = (config.get("curseforge_path") or "").strip()
    ftb_path = (config.get("ftb_path") or "").strip()

    if not curseforge_path and not ftb_path:
        # Migracja starszych konfiguracji: spróbuj wykryć dostępne aplikacje.
        detected_cf = find_curseforge_exe()
        detected_ftb = find_ftb_exe()
        if detected_cf:
            config["curseforge_path"] = str(detected_cf)
            curseforge_path = str(detected_cf)
        if detected_ftb:
            config["ftb_path"] = str(detected_ftb)
            ftb_path = str(detected_ftb)
        if not curseforge_path and not ftb_path:
            return False, "Nie skonfigurowano żadnego launchera.\n\n" + tr(config.get("language"), "choose_one_launcher")

    for label, value, expected_name in (
        ("CurseForge", curseforge_path, "curseforge.exe"),
        ("FTB App", ftb_path, FTB_PROCESS_NAME.lower()),
    ):
        if not value:
            continue
        path = Path(value).expanduser()
        if not path.exists():
            return False, f"Nie znaleziono pliku {label}:\n\n{path}"
        if not path.is_file():
            return False, f"Wskazana ścieżka {label} nie jest plikiem:\n\n{path}"
        if path.name.lower() != expected_name:
            return False, f"Wybrany plik nie jest prawidłowym plikiem {label}:\n\n{path}"

    try:
        tracker_width = int(config.get("tracker_width", DEFAULT_TRACKER_WIDTH))
        tracker_height = int(config.get("tracker_height", DEFAULT_TRACKER_HEIGHT))
    except (TypeError, ValueError):
        return False, "Rozmiar trackera musi być podany jako liczby całkowite."

    if not MIN_TRACKER_WIDTH <= tracker_width <= MAX_TRACKER_WIDTH:
        return False, f"Szerokość trackera musi mieścić się w zakresie {MIN_TRACKER_WIDTH}–{MAX_TRACKER_WIDTH} px."
    if not MIN_TRACKER_HEIGHT <= tracker_height <= MAX_TRACKER_HEIGHT:
        return False, f"Wysokość trackera musi mieścić się w zakresie {MIN_TRACKER_HEIGHT}–{MAX_TRACKER_HEIGHT} px."

    return True, ""


# ============================================================
# AUTOMATYCZNE WYKRYWANIE CURSEFORGE
# ============================================================

def find_curseforge_exe():
    """
    Próbuje automatycznie znaleźć CurseForge.exe.
    """

    candidates = []

    # Najpierw znane lokalizacje.
    candidates.extend(KNOWN_CURSEFORGE_PATHS)

    # Następnie lokalizacje związane z launcherem.
    launcher_directory = get_launcher_directory()

    candidates.extend([
        launcher_directory / "CurseForge.exe",
        launcher_directory.parent / "CurseForge.exe",
    ])

    # Usuwamy duplikaty zachowując kolejność.
    unique_candidates = []

    for candidate in candidates:
        candidate = Path(candidate)

        if candidate not in unique_candidates:
            unique_candidates.append(candidate)

    for candidate in unique_candidates:
        try:
            if candidate.exists() and candidate.is_file():
                if candidate.name.lower() == "curseforge.exe":
                    return candidate.resolve()

        except Exception:
            pass

    return None


# ============================================================
# AUTOMATYCZNE WYKRYWANIE INSTANCES
# ============================================================

def find_instances_folder(curseforge_path=None):
    """
    Próbuje automatycznie znaleźć folder Instances.
    """

    candidates = []

    candidates.extend(KNOWN_INSTANCES_PATHS)

    if curseforge_path:
        curseforge_path = Path(curseforge_path)

        curseforge_directory = curseforge_path.parent

        candidates.extend([
            curseforge_directory / "Instances",
            curseforge_directory.parent / "Instances",
            curseforge_directory.parent.parent / "Instances",
        ])

    # Jeżeli znaleziono CurseForge w:
    #
    # D:\MCMODDED\CurseForge Windows\CurseForge.exe
    #
    # to bardzo prawdopodobne jest:
    #
    # D:\MCMODDED\Instances

    if curseforge_path:
        curseforge_path = Path(curseforge_path)

        for parent in curseforge_path.parents:
            candidates.append(parent / "Instances")

    unique_candidates = []

    for candidate in candidates:
        candidate = Path(candidate)

        if candidate not in unique_candidates:
            unique_candidates.append(candidate)

    for candidate in unique_candidates:
        try:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()

        except Exception:
            pass

    return None


# ============================================================
# OKNO KONFIGURACJI
# ============================================================

def choose_curseforge(entry):
    """
    Otwiera wybór pliku CurseForge.exe.
    """

    selected = filedialog.askopenfilename(
        title="Wybierz CurseForge.exe",
        filetypes=[
            (
                "CurseForge",
                "CurseForge.exe"
            ),
            (
                "Pliki wykonywalne",
                "*.exe"
            ),
            (
                "Wszystkie pliki",
                "*.*"
            )
        ]
    )

    if selected:
        entry.delete(0, tk.END)
        entry.insert(0, selected)


def choose_ftb(entry):
    """Otwiera wybór pliku wykonywalnego FTB App Standalone."""
    selected = filedialog.askopenfilename(
        title="Wybierz FTB Electron App.exe",
        filetypes=[("FTB App", "FTB Electron App.exe"), ("Pliki wykonywalne", "*.exe"), ("Wszystkie pliki", "*.*")]
    )
    if selected:
        entry.delete(0, tk.END)
        entry.insert(0, selected)


def choose_instances(entry):
    """
    Otwiera wybór folderu Instances.
    """

    selected = filedialog.askdirectory(
        title="Wybierz folder Instances"
    )

    if selected:
        entry.delete(0, tk.END)
        entry.insert(0, selected)


def show_configuration_window(initial_config=None):
    """
    Wyświetla okno pierwszej konfiguracji lub ustawień.

    Zwraca:
        dict
    albo:
        None
    """

    root = tk.Tk()

    root.title(APP_NAME)
    root.resizable(False, False)

    window_width = 900
    window_height = 720

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = int(
        (screen_width - window_width) / 2
    )

    y = int(
        (screen_height - window_height) / 2
    )

    root.geometry(
        f"{window_width}x{window_height}+{x}+{y}"
    )

    root.protocol(
        "WM_DELETE_WINDOW",
        root.destroy
    )

    # ========================================================
    # WARTOŚCI POCZĄTKOWE
    # ========================================================

    selected_language = normalize_language(
        initial_config.get("language") if initial_config else None
    )

    if initial_config:
        curseforge_value = initial_config.get("curseforge_path", "")
        ftb_value = initial_config.get("ftb_path", "") or ""
        if not ftb_value:
            detected_ftb = find_ftb_exe()
            ftb_value = str(detected_ftb) if detected_ftb else ""

        try:
            tracker_width_value = int(
                initial_config.get(
                    "tracker_width",
                    DEFAULT_TRACKER_WIDTH
                )
            )
        except (
            TypeError,
            ValueError
        ):
            tracker_width_value = DEFAULT_TRACKER_WIDTH

        try:
            tracker_height_value = int(
                initial_config.get(
                    "tracker_height",
                    DEFAULT_TRACKER_HEIGHT
                )
            )
        except (
            TypeError,
            ValueError
        ):
            tracker_height_value = DEFAULT_TRACKER_HEIGHT

    else:
        detected_curseforge = find_curseforge_exe()

        if detected_curseforge:
            curseforge_value = str(
                detected_curseforge
            )
        else:
            curseforge_value = ""

        detected_ftb = find_ftb_exe()
        ftb_value = str(detected_ftb) if detected_ftb else ""

        tracker_width_value = DEFAULT_TRACKER_WIDTH
        tracker_height_value = DEFAULT_TRACKER_HEIGHT

    # Bezpieczne ograniczenie wartości.
    tracker_width_value = max(
        MIN_TRACKER_WIDTH,
        min(
            MAX_TRACKER_WIDTH,
            tracker_width_value
        )
    )

    tracker_height_value = max(
        MIN_TRACKER_HEIGHT,
        min(
            MAX_TRACKER_HEIGHT,
            tracker_height_value
        )
    )

    # ========================================================
    # NAGŁÓWEK
    # ========================================================

    title_label = tk.Label(
        root,
        text=APP_NAME,
        font=("Segoe UI", 18, "bold")
    )

    title_label.pack(
        pady=(18, 2)
    )

    if initial_config is None:
        subtitle_text = (
            tr(selected_language, "first_run")
        )
    else:
        subtitle_text = (
            tr(selected_language, "settings")
        )

    subtitle_label = tk.Label(
        root,
        text=subtitle_text,
        font=("Segoe UI", 10)
    )

    subtitle_label.pack(
        pady=(0, 12)
    )

    # ========================================================
    # GŁÓWNY UKŁAD
    # ========================================================

    main_frame = tk.Frame(root)

    main_frame.pack(
        fill="both",
        expand=True,
        padx=20
    )

    left_frame = tk.Frame(
        main_frame
    )

    left_frame.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 20)
    )

    right_frame = tk.Frame(
        main_frame
    )

    right_frame.pack(
        side="left",
        fill="both",
        expand=False
    )

    # ========================================================
    # FORMULARZ
    # ========================================================

    form = tk.Frame(
        left_frame
    )

    form.pack(
        fill="x"
    )

    # --------------------------------------------------------
    # CurseForge
    # --------------------------------------------------------
    curseforge_label = tk.Label(form, text=tr(selected_language, "curseforge"), anchor="w", font=("Segoe UI", 10, "bold"))
    curseforge_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
    curseforge_frame = tk.Frame(form)
    curseforge_frame.grid(row=1, column=0, sticky="ew")
    curseforge_entry = tk.Entry(curseforge_frame, font=("Segoe UI", 10))
    curseforge_entry.pack(side="left", fill="x", expand=True)
    tk.Button(curseforge_frame, text=tr(selected_language, "choose"), width=12,
              command=lambda: choose_curseforge(curseforge_entry)).pack(side="left", padx=(8, 0))

    # --------------------------------------------------------
    # FTB App Standalone
    # --------------------------------------------------------
    ftb_label = tk.Label(form, text=tr(selected_language, "ftb"), anchor="w", font=("Segoe UI", 10, "bold"))
    ftb_label.grid(row=2, column=0, sticky="w", pady=(18, 5))
    ftb_frame = tk.Frame(form)
    ftb_frame.grid(row=3, column=0, sticky="ew")
    ftb_entry = tk.Entry(ftb_frame, font=("Segoe UI", 10))
    ftb_entry.pack(side="left", fill="x", expand=True)
    tk.Button(ftb_frame, text=tr(selected_language, "choose"), width=12,
              command=lambda: choose_ftb(ftb_entry)).pack(side="left", padx=(8, 0))

    hint_label = tk.Label(form, text=tr(selected_language, "launcher_hint"),
                          font=("Segoe UI", 8), fg="#777777", justify="left", wraplength=500)
    hint_label.grid(row=4, column=0, sticky="w", pady=(10, 0))

    form.columnconfigure(
        0,
        weight=1
    )

    if curseforge_value:
        curseforge_entry.insert(
            0,
            curseforge_value
        )

    if ftb_value:
        ftb_entry.insert(0, ftb_value)

    # ========================================================
    # ROZMIAR TRACKERA
    # ========================================================

    size_label = tk.Label(
        left_frame,
        text=tr(selected_language, "tracker_size"),
        anchor="w",
        font=("Segoe UI", 10, "bold")
    )

    size_label.pack(
        anchor="w",
        pady=(25, 8)
    )

    size_frame = tk.Frame(
        left_frame
    )

    size_frame.pack(
        anchor="w"
    )

    width_label = tk.Label(
        size_frame,
        text=tr(selected_language, "width"),
        font=("Segoe UI", 10)
    )

    width_label.grid(
        row=0,
        column=0,
        sticky="w"
    )

    width_var = tk.StringVar(
        value=str(tracker_width_value)
    )

    width_spinbox = tk.Spinbox(
        size_frame,
        from_=MIN_TRACKER_WIDTH,
        to=MAX_TRACKER_WIDTH,
        increment=10,
        textvariable=width_var,
        width=8,
        font=("Segoe UI", 10)
    )

    width_spinbox.grid(
        row=0,
        column=1,
        padx=(10, 0)
    )

    width_px_label = tk.Label(
        size_frame,
        text="px",
        font=("Segoe UI", 10)
    )

    width_px_label.grid(
        row=0,
        column=2,
        padx=(5, 20)
    )

    height_label = tk.Label(
        size_frame,
        text=tr(selected_language, "height"),
        font=("Segoe UI", 10)
    )

    height_label.grid(
        row=1,
        column=0,
        sticky="w",
        pady=(10, 0)
    )

    height_var = tk.StringVar(
        value=str(tracker_height_value)
    )

    height_spinbox = tk.Spinbox(
        size_frame,
        from_=MIN_TRACKER_HEIGHT,
        to=MAX_TRACKER_HEIGHT,
        increment=10,
        textvariable=height_var,
        width=8,
        font=("Segoe UI", 10)
    )

    height_spinbox.grid(
        row=1,
        column=1,
        padx=(10, 0),
        pady=(10, 0)
    )

    height_px_label = tk.Label(
        size_frame,
        text="px",
        font=("Segoe UI", 10)
    )

    height_px_label.grid(
        row=1,
        column=2,
        padx=(5, 20),
        pady=(10, 0)
    )

    size_info_label = tk.Label(
        left_frame,
        text=tr(
            selected_language,
            "range",
            wmin=MIN_TRACKER_WIDTH,
            wmax=MAX_TRACKER_WIDTH,
            hmin=MIN_TRACKER_HEIGHT,
            hmax=MAX_TRACKER_HEIGHT
        ),
        font=("Segoe UI", 8),
        fg="#777777",
        justify="left"
    )

    size_info_label.pack(
        anchor="w",
        pady=(8, 0)
    )

    # ========================================================
    # JĘZYK
    # ========================================================

    language_frame = tk.Frame(
        left_frame
    )

    language_frame.pack(
        anchor="w",
        pady=(18, 0)
    )

    language_label = tk.Label(
        language_frame,
        text=tr(selected_language, "language"),
        font=("Segoe UI", 10)
    )

    language_label.pack(
        side="left"
    )

    language_var = tk.StringVar(
        value=SUPPORTED_LANGUAGES[selected_language]
    )

    language_menu = tk.OptionMenu(
        language_frame,
        language_var,
        *SUPPORTED_LANGUAGES.values()
    )

    language_menu.config(
        width=10,
        font=("Segoe UI", 9)
    )

    language_menu.pack(
        side="left",
        padx=(12, 0)
    )

    # ========================================================
    # PODGLĄD
    # ========================================================

    preview_title = tk.Label(
        right_frame,
        text=tr(selected_language, "preview"),
        font=("Segoe UI", 11, "bold")
    )

    preview_title.pack(
        pady=(0, 5)
    )

    preview_size_label = tk.Label(
        right_frame,
        text="",
        font=("Segoe UI", 9),
        fg="#777777"
    )

    preview_size_label.pack(
        pady=(0, 8)
    )

    preview_canvas = tk.Canvas(
        right_frame,
        width=480,
        height=340,
        bg="#E5E5E5",
        highlightthickness=1,
        highlightbackground="#AAAAAA"
    )

    preview_canvas.pack()

    # ========================================================
    # RYSOWANIE PODGLĄDU
    # ========================================================

    def draw_preview(*args):
        preview_canvas.delete("all")

        try:
            width = int(
                width_var.get()
            )
        except (
            TypeError,
            ValueError
        ):
            width = DEFAULT_TRACKER_WIDTH

        try:
            height = int(
                height_var.get()
            )
        except (
            TypeError,
            ValueError
        ):
            height = DEFAULT_TRACKER_HEIGHT

        width = max(
            MIN_TRACKER_WIDTH,
            min(
                MAX_TRACKER_WIDTH,
                width
            )
        )

        height = max(
            MIN_TRACKER_HEIGHT,
            min(
                MAX_TRACKER_HEIGHT,
                height
            )
        )

        preview_width = 480
        preview_height = 340
        margin = 20

        scale_x = (
            preview_width - margin * 2
        ) / width

        scale_y = (
            preview_height - margin * 2
        ) / height

        scale = min(
            scale_x,
            scale_y
        )

        # Nie powiększamy małego trackera ponad 1:1.
        scale = min(
            scale,
            1.0
        )

        display_width = max(
            1,
            int(width * scale)
        )

        display_height = max(
            1,
            int(height * scale)
        )

        x1 = (
            preview_width
            - display_width
        ) // 2

        y1 = (
            preview_height
            - display_height
        ) // 2

        x2 = x1 + display_width
        y2 = y1 + display_height

        # ----------------------------------------------------
        # Tło trackera
        # ----------------------------------------------------

        preview_canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill="#151515",
            outline="#444444",
            width=2
        )

        # ----------------------------------------------------
        # Skala elementów
        # ----------------------------------------------------

        title_font_size = max(
            7,
            int(14 * scale)
        )

        normal_font_size = max(
            6,
            int(10 * scale)
        )

        small_font_size = max(
            5,
            int(8 * scale)
        )

        bold_font_size = max(
            6,
            int(11 * scale)
        )

        # ----------------------------------------------------
        # Przykładowa zawartość
        # ----------------------------------------------------

        center_x = (
            x1 + x2
        ) / 2

        current_y = (
            y1 + 10 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "sample_pack"),
            fill="white",
            font=(
                "Segoe UI",
                title_font_size,
                "bold"
            ),
            anchor="n"
        )

        current_y += (
            24 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "world"),
            fill="#999999",
            font=(
                "Segoe UI",
                small_font_size
            ),
            anchor="n"
        )

        current_y += (
            19 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "day"),
            fill="white",
            font=(
                "Segoe UI",
                normal_font_size
            ),
            anchor="n"
        )

        current_y += (
            19 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "completed"),
            fill="white",
            font=(
                "Segoe UI",
                normal_font_size
            ),
            anchor="n"
        )

        current_y += (
            18 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "remaining"),
            fill="#BBBBBB",
            font=(
                "Segoe UI",
                normal_font_size
            ),
            anchor="n"
        )

        current_y += (
            19 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "completion"),
            fill="white",
            font=(
                "Segoe UI",
                bold_font_size,
                "bold"
            ),
            anchor="n"
        )

        current_y += (
            22 * scale
        )

        # ----------------------------------------------------
        # Pasek postępu
        # ----------------------------------------------------

        bar_width = max(
            50,
            int(
                display_width
                - 30 * scale
            )
        )

        bar_height = max(
            5,
            int(
                12 * scale
            )
        )

        bar_x1 = (
            center_x
            - bar_width / 2
        )

        bar_x2 = (
            center_x
            + bar_width / 2
        )

        bar_y1 = current_y
        bar_y2 = (
            current_y
            + bar_height
        )

        preview_canvas.create_rectangle(
            bar_x1,
            bar_y1,
            bar_x2,
            bar_y2,
            fill="#303030",
            outline=""
        )

        completed_width = (
            bar_width
            * 29.17
            / 100
        )

        preview_canvas.create_rectangle(
            bar_x1,
            bar_y1,
            bar_x1 + completed_width,
            bar_y2,
            fill="#4CAF50",
            outline=""
        )

        current_y += (
            20 * scale
        )

        preview_canvas.create_text(
            center_x,
            current_y,
            text=tr(selected_language, "live"),
            fill="#777777",
            font=(
                "Segoe UI",
                max(
                    5,
                    int(7 * scale)
                )
            ),
            anchor="n"
        )

        preview_size_label.config(
            text=tr(selected_language, "size", width=width, height=height)
        )

    # Aktualizacja podglądu po zmianie wartości.
    width_var.trace_add(
        "write",
        draw_preview
    )

    height_var.trace_add(
        "write",
        draw_preview
    )

    draw_preview()

    # ========================================================
    # STATUS
    # ========================================================

    status_label = tk.Label(
        root,
        text="",
        font=("Segoe UI", 9)
    )

    status_label.pack(
        pady=(10, 0)
    )

    # ========================================================
    # WYNIK
    # ========================================================

    result = {
        "config": None
    }

    # ========================================================
    # PRZYWRÓCENIE DOMYŚLNEGO ROZMIARU
    # ========================================================

    def restore_default_size():
        width_var.set(
            str(DEFAULT_TRACKER_WIDTH)
        )

        height_var.set(
            str(DEFAULT_TRACKER_HEIGHT)
        )

    # ========================================================
    # ZAPIS
    # ========================================================

    def save_and_close():

        curseforge_path = (
            curseforge_entry
            .get()
            .strip()
        )

        ftb_path = ftb_entry.get().strip()

        try:
            tracker_width = int(
                width_var.get()
            )

            tracker_height = int(
                height_var.get()
            )

        except (
            TypeError,
            ValueError
        ):
            status_label.config(
                text=tr(selected_language, "number_error")
            )

            return

        if not curseforge_path and not ftb_path:
            status_label.config(text=tr(selected_language, "choose_one_launcher"))
            return

        language_name = language_var.get()
        selected_language_to_save = next(
            (code for code, name in SUPPORTED_LANGUAGES.items()
             if name == language_name),
            selected_language
        )

        config = {
            "curseforge_path": curseforge_path,
            "ftb_path": ftb_path,
            "tracker_width": tracker_width,
            "tracker_height": tracker_height,
            "language": selected_language_to_save
        }

        valid, error_message = validate_config(
            config
        )

        if not valid:
            status_label.config(
                text=tr(selected_language, "invalid_config")
            )

            messagebox.showerror(
                APP_NAME,
                error_message,
                parent=root
            )

            return

        if not save_config(
            curseforge_path,
            ftb_path,
            tracker_width,
            tracker_height,
            selected_language_to_save
        ):
            messagebox.showerror(
                APP_NAME,
                tr(selected_language, "save_error"),
                parent=root
            )

            return

        result["config"] = config

        root.destroy()

    # ========================================================
    # PRZYCISKI
    # ========================================================

    buttons_frame = tk.Frame(root)

    buttons_frame.pack(
        pady=(12, 15)
    )

    restore_button = tk.Button(
        buttons_frame,
        text=tr(selected_language, "reset_size"),
        width=24,
        command=restore_default_size
    )

    restore_button.pack(
        side="left",
        padx=5
    )

    save_button = tk.Button(
        buttons_frame,
        text=tr(selected_language, "save"),
        width=14,
        height=1,
        command=save_and_close
    )

    save_button.pack(
        side="left",
        padx=5
    )

    cancel_button = tk.Button(
        buttons_frame,
        text=tr(selected_language, "cancel"),
        width=14,
        height=1,
        command=root.destroy
    )

    cancel_button.pack(
        side="left",
        padx=5
    )

    # ========================================================
    # ENTER / ESCAPE
    # ========================================================

    root.bind(
        "<Return>",
        lambda event: save_and_close()
    )

    root.bind(
        "<Escape>",
        lambda event: root.destroy()
    )

    root.mainloop()

    return result["config"]


# ============================================================
# POBRANIE POPRAWNEJ KONFIGURACJI
# ============================================================

def ensure_config_language(config):
    language = normalize_language(config.get("language"))
    if config.get("language") != language:
        config["language"] = language
        try:
            ensure_appdata_directory()
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)
        except Exception:
            pass
    return config


def get_valid_config():
    """
    Pobiera istniejącą i poprawną konfigurację.

    Jeżeli config.json nie istnieje:
        uruchamia pierwszą konfigurację.

    Jeżeli config.json jest uszkodzony:
        uruchamia konfigurację.

    Jeżeli ścieżki nie istnieją:
        uruchamia konfigurację.
    """

    config = load_config()

    if config is not None:
        # Uzupełnij brakujące ścieżki wykrytymi instalacjami; stare pola pozostają.
        config.setdefault("curseforge_path", "")
        config.setdefault("ftb_path", "")
        if not config.get("ftb_path"):
            detected_ftb = find_ftb_exe()
            if detected_ftb:
                config["ftb_path"] = str(detected_ftb)
        valid, error_message = validate_config(config)

        if valid:
            return ensure_config_language(config)

        print()
        print("Konfiguracja jest nieprawidłowa.")
        print(error_message)
        print()
        print("Uruchamianie konfiguracji...")

    else:
        print()
        print("Nie znaleziono poprawnego config.json.")
        print("Uruchamianie pierwszej konfiguracji...")

    config = show_configuration_window(
        config
    )

    return config


# ============================================================
# PROCESY JAVA / MINECRAFT
# ============================================================

def get_java_processes():
    """
    Pobiera procesy java.exe / javaw.exe wraz z CommandLine.
    """

    try:
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                "Get-CimInstance Win32_Process | "
                "Where-Object { "
                "$_.Name -eq 'java.exe' -or "
                "$_.Name -eq 'javaw.exe' "
                "} | "
                "Select-Object ProcessId,Name,CommandLine | "
                "ConvertTo-Json -Compress"
            )
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        output = result.stdout.strip()

        if not output:
            return []

        data = json.loads(output)

        if isinstance(data, dict):
            return [data]

        return data

    except Exception:
        return []


# ============================================================
# ODCZYT GAME DIR
# ============================================================

def extract_game_dir(command_line):
    """
    Wyciąga wartość --gameDir z command line Minecrafta.
    """

    if not command_line:
        return None

    match = re.search(
        r'--gameDir\s+"([^"]+)"',
        command_line,
        re.IGNORECASE
    )

    if match:
        return Path(
            match.group(1)
        )

    match = re.search(
        r'--gameDir\s+(\S+)',
        command_line,
        re.IGNORECASE
    )

    if match:
        return Path(
            match.group(1)
        )

    return None


# ============================================================
# ROZPOZNANIE MINECRAFTA
# ============================================================

def is_minecraft_process(process):
    """
    Sprawdza, czy proces Java jest procesem Minecrafta.
    """

    command_line = (
        process.get("CommandLine")
        or ""
    )

    if not command_line:
        return False

    game_dir = extract_game_dir(
        command_line
    )

    if game_dir is None:
        return False

    minecraft_indicators = [
        "--fml.mcVersion",
        "--gameDir",
        "net.neoforged",
        "net.minecraftforge",
        "net.fabricmc",
        "minecraft"
    ]

    command_lower = command_line.lower()

    score = 0

    for indicator in minecraft_indicators:
        if indicator.lower() in command_lower:
            score += 1

    return score >= 2


# ============================================================
# ZNALEZIENIE AKTYWNEGO MINECRAFTA
# ============================================================

def get_minecraft_process():
    """
    Zwraca pierwszy wykryty proces Minecrafta.
    """

    processes = get_java_processes()

    for process in processes:

        if not is_minecraft_process(process):
            continue

        game_dir = extract_game_dir(
            process.get("CommandLine") or ""
        )

        if game_dir is None:
            continue

        pid = process.get("ProcessId")

        if pid is None:
            continue

        try:
            pid = int(pid)

        except (
            TypeError,
            ValueError
        ):
            continue

        return {
            "pid": pid,
            "name": process.get(
                "Name",
                ""
            ),
            "game_dir": game_dir
        }

    return None


# ============================================================
# SPRAWDZENIE PROCESU
# ============================================================

def is_process_running(pid):
    """
    Sprawdza, czy proces o danym PID nadal działa.
    """

    try:
        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return str(pid) in result.stdout

    except Exception:
        return False


# ============================================================
# CURSEFORGE
# ============================================================

def is_curseforge_running():
    """
    Sprawdza, czy CurseForge.exe jest uruchomiony.
    """

    try:
        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                "IMAGENAME eq CurseForge.exe",
                "/FO",
                "CSV",
                "/NH"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return (
            "CurseForge.exe"
            in result.stdout
        )

    except Exception:
        return False


def start_curseforge(curseforge_path):
    """
    Uruchamia CurseForge.

    Jeżeli CurseForge jest już uruchomiony,
    nie uruchamia drugiej kopii.
    """

    if is_curseforge_running():
        print(
            "CurseForge jest już uruchomiony."
        )

        return True

    curseforge_path = Path(
        curseforge_path
    )

    try:
        subprocess.Popen(
            [str(curseforge_path)],
            cwd=str(curseforge_path.parent)
        )
        for _ in range(10):
            if is_curseforge_running():
                return True
            time.sleep(0.5)
        return is_curseforge_running()

    except Exception as error:
        print(
            "Nie udało się uruchomić CurseForge:"
        )
        print(error)

        return False


# ============================================================
# WYBÓR I OBSŁUGA LAUNCHERA
# ============================================================

def find_ftb_exe():
    """Znajduje oficjalną aplikację FTB App Standalone."""
    for candidate in FTB_EXECUTABLE_PATHS:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except Exception:
            pass
    return None


def is_process_name_running(process_name):
    """Sprawdza, czy działa proces o podanej nazwie."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return process_name.lower() in result.stdout.lower()
    except Exception:
        return False


def is_ftb_running():
    return is_process_name_running(FTB_PROCESS_NAME)


def start_ftb(ftb_path=None):
    """Uruchamia FTB App Standalone, jeśli nie działa już jego proces."""
    if is_ftb_running():
        return True
    ftb_path = Path(ftb_path) if ftb_path else find_ftb_exe()
    if not ftb_path or not ftb_path.is_file():
        messagebox.showerror(
            APP_NAME,
            "Nie znaleziono FTB App Standalone.\n\n"
            "Sprawdź instalację aplikacji lub jej domyślną lokalizację."
        )
        return False
    try:
        subprocess.Popen([str(ftb_path)], cwd=str(ftb_path.parent))
        for _ in range(10):
            if is_ftb_running():
                return True
            time.sleep(0.5)
        return is_ftb_running()
    except Exception as error:
        messagebox.showerror(APP_NAME, f"Nie udało się uruchomić FTB App:\n\n{error}")
        return False


def choose_launcher_dialog(title="Wybierz launcher"):
    """Zwraca: 'curseforge', 'ftb', 'background' albo 'exit'."""
    result = {"value": "exit"}
    root = tk.Tk()
    root.title(APP_NAME)
    root.resizable(False, False)
    root.geometry("440x250")
    root.withdraw()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 440) // 2
    y = (root.winfo_screenheight() - 250) // 2
    root.geometry(f"440x250+{x}+{y}")
    root.deiconify()
    root.attributes("-topmost", True)
    tk.Label(root, text=title, font=("Segoe UI", 12, "bold")).pack(pady=(20, 12))
    tk.Label(root, text="Wybierz aplikację, którą chcesz uruchomić:", font=("Segoe UI", 9)).pack(pady=(0, 12))
    buttons = tk.Frame(root)
    buttons.pack(fill="x", padx=28)
    def select(value):
        result["value"] = value
        root.destroy()
    tk.Button(buttons, text="CurseForge", width=16, command=lambda: select("curseforge")).pack(pady=4)
    tk.Button(buttons, text="FTB App", width=16, command=lambda: select("ftb")).pack(pady=4)
    tk.Button(root, text="Pozostaw program w tle", width=25, command=lambda: select("background")).pack(pady=(12, 4))
    tk.Button(root, text="Zakończ", width=25, command=lambda: select("exit")).pack(pady=4)
    root.protocol("WM_DELETE_WINDOW", lambda: select("exit"))
    root.mainloop()
    return result["value"]


def launcher_is_running(launcher):
    if launcher == "curseforge":
        return is_curseforge_running()
    if launcher == "ftb":
        return is_ftb_running()
    return False


def launch_selected_launcher(launcher, config):
    if launcher == "curseforge":
        path = config.get("curseforge_path")
        if not path:
            messagebox.showerror(APP_NAME, "Nie skonfigurowano ścieżki do CurseForge. Otwórz ustawienia programu.")
            return False
        return start_curseforge(path)
    if launcher == "ftb":
        path = config.get("ftb_path") or find_ftb_exe()
        if not path:
            messagebox.showerror(APP_NAME, "Nie skonfigurowano ścieżki do FTB App. Otwórz ustawienia programu.")
            return False
        return start_ftb(path)
    return False


# ============================================================
# TRACKER
# ============================================================

def kill_tracker(tracker_process):
    """
    Zamyka tracker.
    """

    if tracker_process is None:
        return

    pid = tracker_process.pid

    try:
        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(pid),
                "/T",
                "/F"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    except Exception:
        pass

    time.sleep(1)

    if tracker_process.poll() is None:

        try:
            tracker_process.kill()

        except Exception:
            pass


def start_tracker(
    launcher_directory,
    game_dir
):
    """
    Uruchamia tracker z odpowiednim gameDir.

    Przy EXE:
        Modpack_Quest_Tracker.exe

    Przy .py:
        Modpack_Quest_Tracker.py
    """

    if getattr(
        sys,
        "frozen",
        False
    ):

        tracker_path = (
            launcher_directory
            / TRACKER_EXE_NAME
        )

        if not tracker_path.exists():

            print(
                "Nie znaleziono trackera:"
            )

            print(
                tracker_path
            )

            return None

        try:

            return subprocess.Popen(
                [
                    str(tracker_path),
                    "--game-dir",
                    str(game_dir)
                ],
                cwd=str(
                    launcher_directory
                )
            )

        except Exception as error:

            print(
                "Nie udało się uruchomić trackera:"
            )

            print(error)

            return None

    # --------------------------------------------------------
    # Tryb .py
    # --------------------------------------------------------

    tracker_path = (
        launcher_directory
        / TRACKER_PY_NAME
    )

    if not tracker_path.exists():

        print(
            "Nie znaleziono pliku trackera:"
        )

        print(
            tracker_path
        )

        return None

    try:

        return subprocess.Popen(
            [
                sys.executable,
                str(tracker_path),
                "--game-dir",
                str(game_dir)
            ],
            cwd=str(
                launcher_directory
            )
        )

    except Exception as error:

        print(
            "Nie udało się uruchomić trackera:"
        )

        print(error)

        return None


# ============================================================
# TRYB SETTINGS
# ============================================================

def settings_mode():
    """
    Otwiera okno ustawień i kończy działanie launchera.
    """

    config = load_config()

    new_config = show_configuration_window(
        config
    )

    if new_config is not None:

        print()
        print(
            "Konfiguracja została zapisana."
        )

        print(
            f"CurseForge: "
            f"{new_config['curseforge_path']}"
        )

        print(f"FTB App:   {new_config.get('ftb_path') or '(nie skonfigurowano)'}")

        print(
            f"Tracker:   "
            f"{new_config.get('tracker_width', DEFAULT_TRACKER_WIDTH)}"
            f"x"
            f"{new_config.get('tracker_height', DEFAULT_TRACKER_HEIGHT)}"
)
        return True

    print(
        "Nie wprowadzono zmian."
    )

    return False


# ============================================================
# GŁÓWNY LAUNCHER
# ============================================================

def main():
    """Główna pętla menedżera CurseForge / FTB App i trackera."""
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--settings", action="store_true", help="Otwiera ustawienia programu.")
    args = parser.parse_args()

    if args.settings:
        settings_mode()
        return

    launcher_directory = get_launcher_directory()
    config = get_valid_config()
    if config is None:
        print("Konfiguracja została anulowana.")
        return

    valid, error_message = validate_config(config)
    if not valid:
        messagebox.showerror(APP_NAME, error_message)
        return

    tracker_path = (
        launcher_directory / TRACKER_EXE_NAME
        if getattr(sys, "frozen", False)
        else launcher_directory / TRACKER_PY_NAME
    )
    if not tracker_path.exists():
        messagebox.showerror(APP_NAME, f"Nie znaleziono trackera:\n\n{tracker_path}")
        return

    tracker_process = None
    minecraft_pid = None
    active_launcher = None
    background_mode = False

    # Na starcie użytkownik wybiera launcher. W tle można też uruchomić go ręcznie.
    selected = choose_launcher_dialog("Wybierz launcher do uruchomienia")
    if selected == "exit":
        return
    if selected == "background":
        background_mode = True
    else:
        if not launch_selected_launcher(selected, config):
            return
        active_launcher = selected

    print(f"{APP_NAME} - menedżer launcherów uruchomiony.")
    print("Tracker jest powiązany z procesem Minecrafta, a nie z procesem launchera.")

    while True:
        # Wykrywanie Minecrafta niezależnie od tego, czy launcher nadal działa.
        if minecraft_pid is None:
            minecraft = get_minecraft_process()
            if minecraft is not None:
                minecraft_pid = minecraft["pid"]
                game_dir = minecraft["game_dir"]
                print(f"Wykryto Minecraft PID={minecraft_pid}, gameDir={game_dir}")
                if tracker_process is not None:
                    kill_tracker(tracker_process)
                tracker_process = start_tracker(launcher_directory, game_dir)
                if tracker_process is None:
                    minecraft_pid = None

        else:
            if not is_process_running(minecraft_pid):
                print("Minecraft został zamknięty.")
                if tracker_process is not None:
                    kill_tracker(tracker_process)
                    tracker_process = None
                minecraft_pid = None
                print("Tracker został zamknięty.")
            elif tracker_process is not None and tracker_process.poll() is not None:
                tracker_process = None

        # Zamknięcie launchera nie kończy trackera. Czekamy na koniec gry.
        if active_launcher is not None and not launcher_is_running(active_launcher):
            print(f"Launcher ({active_launcher}) został zamknięty.")
            active_launcher = None
            # Nie pytamy ponownie, dopóki Minecraft działa. Po jego zamknięciu
            # użytkownik dostanie wybór kolejnego launchera lub zakończenia programu.
            background_mode = False

        # Gdy nie ma gry ani launchera, pytamy o następny krok.
        if minecraft_pid is None and active_launcher is None:
            # W trybie tła można ręcznie otworzyć CurseForge/FTB App.
            if is_curseforge_running():
                active_launcher = "curseforge"
                background_mode = False
                print("Wykryto ręcznie uruchomiony CurseForge.")
            elif is_ftb_running():
                active_launcher = "ftb"
                background_mode = False
                print("Wykryto ręcznie uruchomiony FTB App.")
            elif not background_mode:
                choice = choose_launcher_dialog("Minecraft nie działa. Co chcesz zrobić?")
                if choice == "exit":
                    break
                if choice == "background":
                    background_mode = True
                elif launch_selected_launcher(choice, config):
                    active_launcher = choice
                else:
                    background_mode = True

        time.sleep(CHECK_INTERVAL)

    # Sprzątanie tylko przy świadomym zakończeniu programu.
    if tracker_process is not None:
        kill_tracker(tracker_process)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()